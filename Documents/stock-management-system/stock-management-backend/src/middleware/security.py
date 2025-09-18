"""
Security Middleware Module

This module provides comprehensive security middleware for the Flask application
including input validation, rate limiting, and security headers.
"""

import re
import time
import hashlib
from functools import wraps
from typing import Dict, Any, Optional, List
from flask import request, jsonify, g, current_app
from werkzeug.exceptions import BadRequest
import bleach


class SecurityMiddleware:
    """
    Comprehensive security middleware for Flask applications.
    Provides input validation, rate limiting, and security checks.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.rate_limit_storage = {}
        self.blocked_ips = set()
        
        # Security configuration
        self.config = {
            'rate_limit_requests': 100,  # requests per window
            'rate_limit_window': 3600,   # window in seconds (1 hour)
            'rate_limit_burst': 20,      # burst requests allowed
            'max_content_length': 16 * 1024 * 1024,  # 16MB
            'blocked_user_agents': [
                'sqlmap', 'nikto', 'nmap', 'masscan', 'zap'
            ],
            'suspicious_patterns': [
                r'<script[^>]*>.*?</script>',  # XSS attempts
                r'union\s+select',             # SQL injection
                r'drop\s+table',               # SQL injection
                r'insert\s+into',              # SQL injection
                r'delete\s+from',              # SQL injection
                r'\.\./',                      # Path traversal
                r'etc/passwd',                 # File inclusion
                r'cmd\.exe',                   # Command injection
                r'powershell',                 # Command injection
            ]
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the security middleware with Flask app"""
        self.app = app
        
        # Register before_request handlers
        app.before_request(self.before_request_security_check)
        
        # Register after_request handlers for security headers
        app.after_request(self.after_request_security_headers)
    
    def before_request_security_check(self):
        """
        Comprehensive security check before processing requests.
        Includes rate limiting, input validation, and threat detection.
        """
        try:
            # Skip security checks for health endpoints
            if request.endpoint in ['health.health_check', 'health.readiness', 'health.liveness']:
                return None
            
            # Check rate limiting
            if not self._check_rate_limit():
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.'
                }), 429
            
            # Check blocked IPs
            if self._is_ip_blocked():
                return jsonify({
                    'error': 'Access denied',
                    'message': 'Your IP address has been blocked.'
                }), 403
            
            # Check user agent
            if not self._check_user_agent():
                return jsonify({
                    'error': 'Invalid user agent',
                    'message': 'Suspicious user agent detected.'
                }), 403
            
            # Validate content length
            if not self._check_content_length():
                return jsonify({
                    'error': 'Request too large',
                    'message': 'Request payload exceeds maximum allowed size.'
                }), 413
            
            # Check for suspicious patterns in request
            if not self._check_suspicious_patterns():
                self._log_security_event('suspicious_pattern_detected')
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'Request contains suspicious content.'
                }), 400
            
            # Validate and sanitize JSON input
            if request.is_json and request.method in ['POST', 'PUT', 'PATCH']:
                if not self._validate_json_input():
                    return jsonify({
                        'error': 'Invalid input',
                        'message': 'Request contains invalid or malicious content.'
                    }), 400
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Security middleware error: {str(e)}")
            return jsonify({
                'error': 'Security check failed',
                'message': 'An error occurred during security validation.'
            }), 500
    
    def after_request_security_headers(self, response):
        """Add comprehensive security headers to all responses"""
        try:
            # Skip adding headers for health check endpoints to avoid conflicts
            if request.endpoint in ['health.health_check', 'health.readiness', 'health.liveness']:
                return response
            
            # Content Security Policy
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            response.headers['Content-Security-Policy'] = csp_policy
            
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
            response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
            response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
            response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
            
            # Remove server information
            response.headers.pop('Server', None)
            
            # Cache control for sensitive endpoints
            if request.endpoint and any(sensitive in request.endpoint 
                                     for sensitive in ['auth', 'user', 'admin']):
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"Error adding security headers: {str(e)}")
            return response
    
    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        client_ip = self._get_client_ip()
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limit_storage(current_time)
        
        # Get or create client record
        if client_ip not in self.rate_limit_storage:
            self.rate_limit_storage[client_ip] = {
                'requests': [],
                'burst_count': 0,
                'last_request': current_time
            }
        
        client_data = self.rate_limit_storage[client_ip]
        
        # Check burst limit (requests in last minute)
        recent_requests = [req_time for req_time in client_data['requests'] 
                          if current_time - req_time < 60]
        
        if len(recent_requests) >= self.config['rate_limit_burst']:
            self._log_security_event('rate_limit_burst_exceeded', {'ip': client_ip})
            return False
        
        # Check hourly limit
        hourly_requests = [req_time for req_time in client_data['requests'] 
                          if current_time - req_time < self.config['rate_limit_window']]
        
        if len(hourly_requests) >= self.config['rate_limit_requests']:
            self._log_security_event('rate_limit_exceeded', {'ip': client_ip})
            return False
        
        # Add current request
        client_data['requests'].append(current_time)
        client_data['last_request'] = current_time
        
        return True
    
    def _is_ip_blocked(self) -> bool:
        """Check if client IP is blocked"""
        client_ip = self._get_client_ip()
        return client_ip in self.blocked_ips
    
    def _check_user_agent(self) -> bool:
        """Check for suspicious user agents"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        for blocked_agent in self.config['blocked_user_agents']:
            if blocked_agent in user_agent:
                self._log_security_event('blocked_user_agent', {
                    'user_agent': user_agent,
                    'ip': self._get_client_ip()
                })
                return False
        
        return True
    
    def _check_content_length(self) -> bool:
        """Check if content length is within limits"""
        content_length = request.content_length
        if content_length and content_length > self.config['max_content_length']:
            self._log_security_event('content_length_exceeded', {
                'content_length': content_length,
                'ip': self._get_client_ip()
            })
            return False
        
        return True
    
    def _check_suspicious_patterns(self) -> bool:
        """Check for suspicious patterns in request data"""
        # Check URL path
        path = request.path.lower()
        for pattern in self.config['suspicious_patterns']:
            if re.search(pattern, path, re.IGNORECASE):
                self._log_security_event('suspicious_pattern_in_path', {
                    'path': request.path,
                    'pattern': pattern,
                    'ip': self._get_client_ip()
                })
                return False
        
        # Check query parameters
        for key, value in request.args.items():
            combined = f"{key}={value}".lower()
            for pattern in self.config['suspicious_patterns']:
                if re.search(pattern, combined, re.IGNORECASE):
                    self._log_security_event('suspicious_pattern_in_query', {
                        'query': combined,
                        'pattern': pattern,
                        'ip': self._get_client_ip()
                    })
                    return False
        
        return True
    
    def _validate_json_input(self) -> bool:
        """Validate and sanitize JSON input"""
        try:
            data = request.get_json()
            if not data:
                return True
            
            # Recursively validate JSON data
            sanitized_data = self._sanitize_json_data(data)
            
            # Store sanitized data for use in routes
            g.sanitized_json = sanitized_data
            
            return True
            
        except Exception as e:
            self._log_security_event('json_validation_error', {
                'error': str(e),
                'ip': self._get_client_ip()
            })
            return False
    
    def _sanitize_json_data(self, data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {key: self._sanitize_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        elif isinstance(data, str):
            # Check for suspicious patterns
            for pattern in self.config['suspicious_patterns']:
                if re.search(pattern, data, re.IGNORECASE):
                    raise ValueError(f"Suspicious pattern detected: {pattern}")
            
            # Sanitize HTML content
            return bleach.clean(data, tags=[], attributes={}, strip=True)
        else:
            return data
    
    def _get_client_ip(self) -> str:
        """Get client IP address considering proxy headers"""
        # Check for forwarded IP (common in reverse proxy setups)
        forwarded_ips = request.headers.get('X-Forwarded-For')
        if forwarded_ips:
            # Take the first IP in the chain
            return forwarded_ips.split(',')[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
        
        # Fall back to remote address
        return request.remote_addr or 'unknown'
    
    def _cleanup_rate_limit_storage(self, current_time: float):
        """Clean up old rate limit entries"""
        cutoff_time = current_time - self.config['rate_limit_window']
        
        for client_ip in list(self.rate_limit_storage.keys()):
            client_data = self.rate_limit_storage[client_ip]
            
            # Remove old requests
            client_data['requests'] = [
                req_time for req_time in client_data['requests'] 
                if req_time > cutoff_time
            ]
            
            # Remove client if no recent requests
            if not client_data['requests'] and current_time - client_data['last_request'] > 3600:
                del self.rate_limit_storage[client_ip]
    
    def _log_security_event(self, event_type: str, details: Optional[Dict] = None):
        """Log security events for monitoring"""
        log_data = {
            'event_type': event_type,
            'timestamp': time.time(),
            'ip': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'path': request.path,
            'method': request.method,
            'details': details or {}
        }
        
        current_app.logger.warning(f"Security event: {event_type}", extra=log_data)
    
    def block_ip(self, ip_address: str):
        """Block an IP address"""
        self.blocked_ips.add(ip_address)
        self._log_security_event('ip_blocked', {'blocked_ip': ip_address})
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip_address)
        self._log_security_event('ip_unblocked', {'unblocked_ip': ip_address})


def input_validation(required_fields: List[str] = None, 
                    optional_fields: List[str] = None,
                    field_types: Dict[str, type] = None):
    """
    Decorator for input validation with type checking and sanitization.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        field_types: Dict mapping field names to expected types
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get sanitized data from security middleware
                data = getattr(g, 'sanitized_json', request.get_json())
                
                if not data:
                    return jsonify({
                        'error': 'Invalid input',
                        'message': 'Request body must contain valid JSON'
                    }), 400
                
                # Check required fields
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        return jsonify({
                            'error': 'Missing required fields',
                            'message': f'Required fields: {", ".join(missing_fields)}'
                        }), 400
                
                # Check field types
                if field_types:
                    for field, expected_type in field_types.items():
                        if field in data and not isinstance(data[field], expected_type):
                            return jsonify({
                                'error': 'Invalid field type',
                                'message': f'Field "{field}" must be of type {expected_type.__name__}'
                            }), 400
                
                # Remove unexpected fields
                allowed_fields = set((required_fields or []) + (optional_fields or []))
                if allowed_fields:
                    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
                    g.validated_json = filtered_data
                else:
                    g.validated_json = data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Input validation error: {str(e)}")
                return jsonify({
                    'error': 'Validation failed',
                    'message': 'Input validation error occurred'
                }), 400
        
        return decorated_function
    return decorator


def secure_headers(additional_headers: Dict[str, str] = None):
    """
    Decorator to add additional security headers to specific routes.
    
    Args:
        additional_headers: Dict of additional headers to add
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            if additional_headers:
                if hasattr(response, 'headers'):
                    for header, value in additional_headers.items():
                        response.headers[header] = value
            
            return response
        
        return decorated_function
    return decorator