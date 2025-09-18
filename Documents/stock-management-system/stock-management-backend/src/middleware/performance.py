"""
Performance middleware for Flask application
Handles response compression, caching headers, and performance optimizations
"""

import gzip
import io
import time
from functools import wraps
from flask import request, Response, current_app, g
from werkzeug.exceptions import NotAcceptable
import logging


class PerformanceMiddleware:
    """
    Middleware to handle performance optimizations including:
    - Response compression (gzip)
    - Caching headers
    - Response time tracking
    - Content optimization
    """
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger('stock-management-backend.performance')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the performance middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Configure compression settings
        app.config.setdefault('COMPRESS_MIMETYPES', [
            'text/html',
            'text/css',
            'text/xml',
            'text/plain',
            'text/javascript',
            'application/json',
            'application/javascript',
            'application/xml',
            'application/rss+xml',
            'application/atom+xml',
            'image/svg+xml'
        ])
        
        app.config.setdefault('COMPRESS_LEVEL', 6)
        app.config.setdefault('COMPRESS_MIN_SIZE', 500)
        
        self.logger.info("Performance middleware initialized")
    
    def before_request(self):
        """Track request start time for performance monitoring"""
        g.start_time = time.time()
    
    def after_request(self, response):
        """
        Apply performance optimizations to response
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response with performance optimizations
        """
        try:
            # Calculate response time
            if hasattr(g, 'start_time'):
                response_time = (time.time() - g.start_time) * 1000
                response.headers['X-Response-Time'] = f"{response_time:.2f}ms"
            
            # Apply caching headers based on route
            self._apply_caching_headers(response)
            
            # Apply compression if appropriate
            if self._should_compress(response):
                response = self._compress_response(response)
            
            # Add performance headers
            self._add_performance_headers(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in performance middleware: {e}", exc_info=True)
            return response
    
    def _should_compress(self, response):
        """
        Determine if response should be compressed
        
        Args:
            response: Flask response object
            
        Returns:
            bool: True if response should be compressed
        """
        # Don't compress if already compressed
        if response.headers.get('Content-Encoding'):
            return False
        
        # Don't compress small responses
        if (hasattr(response, 'content_length') and 
            response.content_length and 
            response.content_length < current_app.config['COMPRESS_MIN_SIZE']):
            return False
        
        # Check if client accepts gzip
        if 'gzip' not in request.headers.get('Accept-Encoding', ''):
            return False
        
        # Check content type
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        return content_type in current_app.config['COMPRESS_MIMETYPES']
    
    def _compress_response(self, response):
        """
        Compress response using gzip
        
        Args:
            response: Flask response object
            
        Returns:
            Compressed response
        """
        try:
            # Get response data
            data = response.get_data()
            
            if not data:
                return response
            
            # Compress data
            gzip_buffer = io.BytesIO()
            with gzip.GzipFile(
                fileobj=gzip_buffer, 
                mode='wb', 
                compresslevel=current_app.config['COMPRESS_LEVEL']
            ) as gzip_file:
                gzip_file.write(data)
            
            compressed_data = gzip_buffer.getvalue()
            
            # Update response
            response.set_data(compressed_data)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(compressed_data)
            
            # Add compression ratio for monitoring
            if len(data) > 0:
                ratio = (1 - len(compressed_data) / len(data)) * 100
                response.headers['X-Compression-Ratio'] = f"{ratio:.1f}%"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
            return response
    
    def _apply_caching_headers(self, response):
        """
        Apply appropriate caching headers based on route and content
        
        Args:
            response: Flask response object
        """
        # Get current endpoint
        endpoint = request.endpoint
        
        if not endpoint:
            return
        
        # API routes caching strategy
        if endpoint.startswith('health'):
            # Health checks - short cache
            response.headers['Cache-Control'] = 'public, max-age=30'
        elif endpoint.endswith('.static'):
            # Static files - long cache
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            response.headers['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
        elif 'reports' in endpoint or 'dashboard' in endpoint:
            # Reports and dashboard - medium cache with revalidation
            response.headers['Cache-Control'] = 'public, max-age=300, must-revalidate'
        elif request.method == 'GET' and 'api' in endpoint:
            # GET API requests - short cache with revalidation
            if 'inventory' in endpoint or 'product' in endpoint:
                response.headers['Cache-Control'] = 'public, max-age=60, must-revalidate'
            else:
                response.headers['Cache-Control'] = 'public, max-age=30, must-revalidate'
        elif request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # Mutating operations - no cache
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        else:
            # Default - no cache for dynamic content
            response.headers['Cache-Control'] = 'no-cache, must-revalidate'
        
        # Add ETag for GET requests on cacheable content
        if (request.method == 'GET' and 
            'public' in response.headers.get('Cache-Control', '') and
            response.status_code == 200):
            
            # Generate simple ETag based on content
            if hasattr(response, 'get_data'):
                import hashlib
                content_hash = hashlib.md5(response.get_data()).hexdigest()[:16]
                response.headers['ETag'] = f'"{content_hash}"'
    
    def _add_performance_headers(self, response):
        """
        Add performance-related headers
        
        Args:
            response: Flask response object
        """
        # Add server identification
        response.headers['X-Powered-By'] = 'Stock-Management-Backend'
        
        # Add content optimization hints
        if response.headers.get('Content-Type', '').startswith('application/json'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Add performance hints for browsers
        if request.endpoint and not request.endpoint.startswith('health'):
            response.headers['X-DNS-Prefetch-Control'] = 'on'


def cache_response(max_age=300, public=True, must_revalidate=True):
    """
    Decorator to add caching headers to specific routes
    
    Args:
        max_age: Cache max age in seconds
        public: Whether cache can be public
        must_revalidate: Whether cache must revalidate
    
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            if isinstance(response, Response):
                cache_control = []
                
                if public:
                    cache_control.append('public')
                else:
                    cache_control.append('private')
                
                cache_control.append(f'max-age={max_age}')
                
                if must_revalidate:
                    cache_control.append('must-revalidate')
                
                response.headers['Cache-Control'] = ', '.join(cache_control)
            
            return response
        return decorated_function
    return decorator


def no_cache(f):
    """
    Decorator to prevent caching of specific routes
    
    Args:
        f: Function to decorate
    
    Returns:
        Decorated function with no-cache headers
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        if isinstance(response, Response):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    return decorated_function


def compress_response(f):
    """
    Decorator to force compression on specific routes
    
    Args:
        f: Function to decorate
    
    Returns:
        Decorated function with compression
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        if isinstance(response, Response):
            # Force compression by setting appropriate headers
            response.headers['Vary'] = 'Accept-Encoding'
        
        return response
    return decorated_function


class QueryOptimizer:
    """
    Database query optimization utilities
    """
    
    @staticmethod
    def optimize_query_options():
        """
        Get optimized SQLAlchemy query options
        
        Returns:
            Dictionary of query optimization options
        """
        return {
            'lazy': 'select',  # Optimize lazy loading
            'batch_size': 50,  # Batch size for bulk operations
            'expire_on_commit': False,  # Don't expire objects on commit
            'autoflush': True,  # Auto-flush for consistency
            'query_cache_size': 500  # Query cache size
        }
    
    @staticmethod
    def get_pagination_params(request, default_per_page=20, max_per_page=100):
        """
        Get optimized pagination parameters from request
        
        Args:
            request: Flask request object
            default_per_page: Default items per page
            max_per_page: Maximum items per page
        
        Returns:
            Tuple of (page, per_page, offset)
        """
        try:
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(max_per_page, max(1, int(request.args.get('per_page', default_per_page))))
            offset = (page - 1) * per_page
            
            return page, per_page, offset
            
        except (ValueError, TypeError):
            return 1, default_per_page, 0
    
    @staticmethod
    def add_query_hints(query, hints=None):
        """
        Add performance hints to SQLAlchemy query
        
        Args:
            query: SQLAlchemy query object
            hints: Dictionary of query hints
        
        Returns:
            Optimized query object
        """
        if hints is None:
            hints = {}
        
        # Add default optimization hints
        if 'join_strategy' in hints:
            query = query.options(hints['join_strategy'])
        
        if 'load_strategy' in hints:
            query = query.options(hints['load_strategy'])
        
        # Add query execution options
        if 'execution_options' in hints:
            query = query.execution_options(**hints['execution_options'])
        
        return query


# Performance monitoring utilities
class PerformanceMonitor:
    """
    Performance monitoring and metrics collection
    """
    
    def __init__(self):
        self.logger = logging.getLogger('stock-management-backend.performance.monitor')
    
    def log_slow_query(self, query_time, query_info):
        """
        Log slow database queries for optimization
        
        Args:
            query_time: Query execution time in seconds
            query_info: Information about the query
        """
        if query_time > 1.0:  # Log queries slower than 1 second
            self.logger.warning(
                "Slow query detected",
                extra={
                    'query_time_seconds': query_time,
                    'query_info': query_info,
                    'performance_impact': 'high' if query_time > 5.0 else 'medium'
                }
            )
    
    def log_memory_usage(self, endpoint, memory_usage):
        """
        Log memory usage for specific endpoints
        
        Args:
            endpoint: API endpoint name
            memory_usage: Memory usage in MB
        """
        if memory_usage > 100:  # Log high memory usage
            self.logger.warning(
                "High memory usage detected",
                extra={
                    'endpoint': endpoint,
                    'memory_usage_mb': memory_usage,
                    'performance_impact': 'high' if memory_usage > 500 else 'medium'
                }
            )