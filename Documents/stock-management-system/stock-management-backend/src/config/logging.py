"""
Comprehensive logging configuration for Stock Management System
Implements structured logging with timestamps and service identification
"""

import logging
import logging.config
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g
import traceback


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    Includes service identification, timestamps, and request context
    """
    
    def __init__(self, service_name: str = "stock-management-backend"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log structure
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'service': self.service_name,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        try:
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'request_id': getattr(g, 'request_id', None)
                }
        except RuntimeError:
            # Outside request context
            pass
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class DatabaseErrorHandler:
    """
    Specialized error handler for database-related issues
    Provides detailed logging and error categorization
    """
    
    @staticmethod
    def log_database_error(logger: logging.Logger, error: Exception, 
                          operation: str, context: Optional[Dict[str, Any]] = None):
        """
        Log database errors with detailed context and troubleshooting information
        
        Args:
            logger: Logger instance
            error: Database exception
            operation: Description of the operation that failed
            context: Additional context information
        """
        error_msg = str(error).lower()
        
        # Categorize database errors
        if 'timeout' in error_msg or 'timed out' in error_msg:
            error_category = "timeout"
            troubleshooting = [
                "Check database server performance",
                "Review query complexity and optimization",
                "Verify network connectivity",
                "Consider increasing timeout settings"
            ]
        elif 'connection refused' in error_msg or 'could not connect' in error_msg:
            error_category = "connection_refused"
            troubleshooting = [
                "Verify database server is running",
                "Check database host and port configuration",
                "Verify network connectivity and firewall settings",
                "Check database server logs"
            ]
        elif 'authentication failed' in error_msg or 'password' in error_msg:
            error_category = "authentication"
            troubleshooting = [
                "Verify database credentials",
                "Check user permissions",
                "Ensure password is correct",
                "Verify user exists in database"
            ]
        elif 'database' in error_msg and 'does not exist' in error_msg:
            error_category = "database_not_found"
            troubleshooting = [
                "Verify database name is correct",
                "Ensure database has been created",
                "Check database initialization scripts",
                "Verify connection string"
            ]
        elif 'permission denied' in error_msg or 'access denied' in error_msg:
            error_category = "permission_denied"
            troubleshooting = [
                "Check user database permissions",
                "Verify user has required privileges",
                "Check database access policies",
                "Review user role assignments"
            ]
        elif 'deadlock' in error_msg:
            error_category = "deadlock"
            troubleshooting = [
                "Review transaction isolation levels",
                "Optimize query order and locking",
                "Consider retry logic for deadlock scenarios",
                "Analyze concurrent access patterns"
            ]
        else:
            error_category = "unknown"
            troubleshooting = [
                "Check database server logs",
                "Verify database configuration",
                "Review recent database changes",
                "Contact database administrator"
            ]
        
        # Log structured error information
        logger.error(
            f"Database operation failed: {operation}",
            extra={
                'error_category': error_category,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'operation': operation,
                'troubleshooting': troubleshooting,
                'context': context or {}
            }
        )


class NetworkErrorHandler:
    """
    Specialized error handler for network-related issues
    """
    
    @staticmethod
    def log_network_error(logger: logging.Logger, error: Exception, 
                         operation: str, context: Optional[Dict[str, Any]] = None):
        """
        Log network errors with detailed context
        
        Args:
            logger: Logger instance
            error: Network exception
            operation: Description of the operation that failed
            context: Additional context information
        """
        error_msg = str(error).lower()
        
        # Categorize network errors
        if 'timeout' in error_msg:
            error_category = "timeout"
            troubleshooting = [
                "Check network connectivity",
                "Verify service endpoints are reachable",
                "Review timeout configuration",
                "Check for network congestion"
            ]
        elif 'connection refused' in error_msg:
            error_category = "connection_refused"
            troubleshooting = [
                "Verify target service is running",
                "Check port and host configuration",
                "Verify firewall settings",
                "Check service discovery configuration"
            ]
        elif 'name resolution' in error_msg or 'dns' in error_msg:
            error_category = "dns_resolution"
            troubleshooting = [
                "Check DNS configuration",
                "Verify hostname is correct",
                "Check network DNS settings",
                "Try using IP address instead of hostname"
            ]
        else:
            error_category = "unknown"
            troubleshooting = [
                "Check network connectivity",
                "Verify service configuration",
                "Review network logs",
                "Contact network administrator"
            ]
        
        logger.error(
            f"Network operation failed: {operation}",
            extra={
                'error_category': error_category,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'operation': operation,
                'troubleshooting': troubleshooting,
                'context': context or {}
            }
        )


def setup_logging(app_name: str = "stock-management-backend", 
                 log_level: str = None) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        app_name: Application name for service identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    
    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Determine if we should use structured logging
    use_structured = os.getenv('STRUCTURED_LOGGING', 'true').lower() == 'true'
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    if use_structured:
        # Use structured JSON formatter
        formatter = StructuredFormatter(service_name=app_name)
    else:
        # Use standard formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create application logger
    app_logger = logging.getLogger(app_name)
    
    # Log startup information
    app_logger.info(
        f"Logging initialized for {app_name}",
        extra={
            'log_level': log_level,
            'structured_logging': use_structured,
            'environment': os.getenv('FLASK_ENV', 'unknown')
        }
    )
    
    return app_logger


def setup_error_handlers(app):
    """
    Setup Flask error handlers with comprehensive logging
    
    Args:
        app: Flask application instance
    """
    logger = logging.getLogger('stock-management-backend')
    
    @app.errorhandler(404)
    def handle_404(error):
        logger.warning(
            "Resource not found",
            extra={
                'status_code': 404,
                'requested_path': request.path,
                'method': request.method
            }
        )
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def handle_500(error):
        logger.error(
            "Internal server error",
            extra={
                'status_code': 500,
                'error_description': str(error)
            }
        )
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log unhandled exceptions
        logger.error(
            "Unhandled exception occurred",
            exc_info=True,
            extra={
                'error_type': type(error).__name__,
                'error_message': str(error)
            }
        )
        
        # Return generic error response
        return {'error': 'An unexpected error occurred'}, 500


def log_startup_info(logger: logging.Logger, config: Dict[str, Any]):
    """
    Log comprehensive startup information
    
    Args:
        logger: Logger instance
        config: Application configuration dictionary
    """
    logger.info(
        "Application startup initiated",
        extra={
            'flask_env': config.get('FLASK_ENV', 'unknown'),
            'debug_mode': config.get('DEBUG', False),
            'database_configured': bool(config.get('SQLALCHEMY_DATABASE_URI')),
            'secret_key_configured': bool(config.get('SECRET_KEY')),
            'cors_configured': bool(config.get('CORS_ORIGINS')),
            'python_version': sys.version,
            'working_directory': os.getcwd()
        }
    )


def log_shutdown_info(logger: logging.Logger, reason: str = "normal"):
    """
    Log application shutdown information
    
    Args:
        logger: Logger instance
        reason: Reason for shutdown
    """
    logger.info(
        "Application shutdown initiated",
        extra={
            'shutdown_reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
    )


# Create module-level instances for easy import
db_error_handler = DatabaseErrorHandler()
network_error_handler = NetworkErrorHandler()