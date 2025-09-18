"""
Environment Variable Validation Module

This module provides comprehensive validation for environment variables
required for the Stock Management System to run in production.
"""

import os
import sys
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse


class EnvironmentValidationError(Exception):
    """Custom exception for environment validation errors"""
    pass


class EnvironmentValidator:
    """
    Validates environment variables and provides clear error messages
    for missing or invalid configurations.
    """
    
    # Required environment variables with their validation rules
    REQUIRED_VARS = {
        'SECRET_KEY': {
            'description': 'Flask secret key for session management',
            'min_length': 32,
            'validator': 'validate_secret_key'
        },
        'POSTGRES_PASSWORD': {
            'description': 'PostgreSQL database password',
            'min_length': 8,
            'validator': 'validate_password'
        }
    }
    
    # Optional environment variables with defaults and validation
    OPTIONAL_VARS = {
        'POSTGRES_DB': {
            'default': 'stock_management',
            'description': 'PostgreSQL database name',
            'validator': 'validate_db_name'
        },
        'POSTGRES_USER': {
            'default': 'postgres',
            'description': 'PostgreSQL username',
            'validator': 'validate_username'
        },
        'FLASK_ENV': {
            'default': 'production',
            'description': 'Flask environment (development/production)',
            'allowed_values': ['development', 'production', 'testing'],
            'validator': 'validate_flask_env'
        },
        'SESSION_COOKIE_SECURE': {
            'default': 'true',
            'description': 'Enable secure cookies for HTTPS',
            'allowed_values': ['true', 'false'],
            'validator': 'validate_boolean'
        },
        'SESSION_COOKIE_SAMESITE': {
            'default': 'None',
            'description': 'SameSite cookie policy',
            'allowed_values': ['None', 'Lax', 'Strict'],
            'validator': 'validate_samesite'
        },
        'CORS_ORIGINS': {
            'default': 'https://yourdomain.com',
            'description': 'Comma-separated list of allowed CORS origins',
            'validator': 'validate_cors_origins'
        },
        'DATABASE_URL': {
            'default': None,
            'description': 'Full PostgreSQL connection URL (overrides individual DB settings)',
            'validator': 'validate_database_url'
        },
        'DEBUG': {
            'default': 'false',
            'description': 'Enable debug mode',
            'allowed_values': ['true', 'false'],
            'validator': 'validate_boolean'
        },
        'BCRYPT_LOG_ROUNDS': {
            'default': '12',
            'description': 'BCrypt hashing rounds (8-15 recommended)',
            'validator': 'validate_bcrypt_rounds'
        },
        'RATE_LIMIT_ENABLED': {
            'default': 'true',
            'description': 'Enable rate limiting middleware',
            'allowed_values': ['true', 'false'],
            'validator': 'validate_boolean'
        },
        'RATE_LIMIT_REQUESTS': {
            'default': '100',
            'description': 'Maximum requests per hour per IP',
            'validator': 'validate_positive_integer'
        },
        'RATE_LIMIT_BURST': {
            'default': '20',
            'description': 'Maximum burst requests per minute per IP',
            'validator': 'validate_positive_integer'
        },
        'SECURITY_HEADERS_ENABLED': {
            'default': 'true',
            'description': 'Enable security headers middleware',
            'allowed_values': ['true', 'false'],
            'validator': 'validate_boolean'
        },
        'INPUT_VALIDATION_ENABLED': {
            'default': 'true',
            'description': 'Enable input validation middleware',
            'allowed_values': ['true', 'false'],
            'validator': 'validate_boolean'
        }
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.validated_config: Dict[str, Any] = {}
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Validate all environment variables and return validated configuration.
        
        Returns:
            Dict containing validated configuration
            
        Raises:
            EnvironmentValidationError: If validation fails
        """
        self.errors.clear()
        self.warnings.clear()
        self.validated_config.clear()
        
        # Validate required variables
        self._validate_required_vars()
        
        # Validate optional variables and set defaults
        self._validate_optional_vars()
        
        # Perform cross-validation checks
        self._cross_validate()
        
        # Check for errors
        if self.errors:
            error_message = self._format_error_message()
            raise EnvironmentValidationError(error_message)
        
        # Log warnings if any
        if self.warnings:
            self._log_warnings()
        
        return self.validated_config
    
    def _validate_required_vars(self):
        """Validate all required environment variables"""
        for var_name, config in self.REQUIRED_VARS.items():
            value = os.getenv(var_name)
            
            if not value:
                self.errors.append(
                    f"Missing required environment variable: {var_name}\n"
                    f"  Description: {config['description']}\n"
                    f"  Please set this variable in your environment or .env file"
                )
                continue
            
            # Run specific validator if defined
            if 'validator' in config:
                validator_method = getattr(self, config['validator'])
                is_valid, error_msg = validator_method(value, config)
                
                if not is_valid:
                    self.errors.append(
                        f"Invalid value for {var_name}: {error_msg}\n"
                        f"  Current value: {value}\n"
                        f"  Description: {config['description']}"
                    )
                    continue
            
            self.validated_config[var_name] = value
    
    def _validate_optional_vars(self):
        """Validate optional environment variables and set defaults"""
        for var_name, config in self.OPTIONAL_VARS.items():
            value = os.getenv(var_name, config.get('default'))
            
            if value is None:
                continue
            
            # Run specific validator if defined
            if 'validator' in config:
                validator_method = getattr(self, config['validator'])
                is_valid, error_msg = validator_method(value, config)
                
                if not is_valid:
                    if config.get('default'):
                        self.warnings.append(
                            f"Invalid value for {var_name}, using default: {config['default']}\n"
                            f"  Error: {error_msg}\n"
                            f"  Current value: {value}"
                        )
                        value = config['default']
                    else:
                        self.errors.append(
                            f"Invalid value for {var_name}: {error_msg}\n"
                            f"  Current value: {value}\n"
                            f"  Description: {config['description']}"
                        )
                        continue
            
            self.validated_config[var_name] = value
    
    def _cross_validate(self):
        """Perform cross-validation between related variables"""
        # Validate DATABASE_URL vs individual DB settings
        database_url = self.validated_config.get('DATABASE_URL')
        if database_url:
            # If DATABASE_URL is provided, ensure it's valid
            parsed = urlparse(database_url)
            if not all([parsed.scheme, parsed.hostname, parsed.username]):
                self.errors.append(
                    "DATABASE_URL is malformed. Expected format: "
                    "postgresql://username:password@host:port/database"
                )
        else:
            # If no DATABASE_URL, ensure individual DB settings are present
            required_db_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']
            missing_db_vars = [var for var in required_db_vars 
                             if var not in self.validated_config]
            
            if missing_db_vars:
                self.errors.append(
                    f"Either DATABASE_URL or individual database settings required.\n"
                    f"  Missing: {', '.join(missing_db_vars)}\n"
                    f"  Provide either DATABASE_URL or all of: {', '.join(required_db_vars)}"
                )
        
        # Validate HTTPS settings consistency
        secure_cookies = self.validated_config.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
        samesite_none = self.validated_config.get('SESSION_COOKIE_SAMESITE') == 'None'
        
        if secure_cookies and not samesite_none:
            self.warnings.append(
                "SESSION_COOKIE_SECURE=true typically requires SESSION_COOKIE_SAMESITE=None "
                "for cross-origin requests in production"
            )
    
    # Validator methods
    def validate_secret_key(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate Flask secret key"""
        min_length = config.get('min_length', 32)
        
        if len(value) < min_length:
            return False, f"Must be at least {min_length} characters long"
        
        if value in ['change-me', 'your-super-secret-key-change-in-production', 'dev-key']:
            return False, "Must not use default/example values"
        
        # Check for sufficient entropy (basic check)
        if len(set(value)) < 10:
            return False, "Must contain more diverse characters for security"
        
        return True, ""
    
    def validate_password(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate database password"""
        min_length = config.get('min_length', 8)
        
        if len(value) < min_length:
            return False, f"Must be at least {min_length} characters long"
        
        if value in ['password', '123456', 'postgres', 'admin']:
            return False, "Must not use common/weak passwords"
        
        return True, ""
    
    def validate_db_name(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate database name"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            return False, "Must start with letter and contain only letters, numbers, and underscores"
        
        return True, ""
    
    def validate_username(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate database username"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            return False, "Must start with letter and contain only letters, numbers, and underscores"
        
        return True, ""
    
    def validate_flask_env(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate Flask environment"""
        allowed = config.get('allowed_values', [])
        if value not in allowed:
            return False, f"Must be one of: {', '.join(allowed)}"
        
        return True, ""
    
    def validate_boolean(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate boolean string values"""
        if value.lower() not in ['true', 'false']:
            return False, "Must be 'true' or 'false'"
        
        return True, ""
    
    def validate_samesite(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate SameSite cookie policy"""
        allowed = config.get('allowed_values', [])
        if value not in allowed:
            return False, f"Must be one of: {', '.join(allowed)}"
        
        return True, ""
    
    def validate_cors_origins(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate CORS origins"""
        if value == '*':
            self.warnings.append(
                "CORS_ORIGINS='*' allows all origins. Consider restricting to specific domains in production."
            )
            return True, ""
        
        origins = [origin.strip() for origin in value.split(',')]
        
        for origin in origins:
            if origin and not (origin.startswith('http://') or origin.startswith('https://')):
                return False, f"Origin '{origin}' must start with http:// or https://"
        
        return True, ""
    
    def validate_database_url(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate database URL format"""
        try:
            parsed = urlparse(value)
            
            if parsed.scheme not in ['postgresql', 'postgres']:
                return False, "Scheme must be 'postgresql' or 'postgres'"
            
            if not parsed.hostname:
                return False, "Must include hostname"
            
            if not parsed.username:
                return False, "Must include username"
            
            if not parsed.path or parsed.path == '/':
                return False, "Must include database name in path"
            
            return True, ""
            
        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"
    
    def validate_bcrypt_rounds(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate BCrypt rounds"""
        try:
            rounds = int(value)
            if rounds < 8 or rounds > 15:
                return False, "Must be between 8 and 15 (recommended: 12)"
            return True, ""
        except ValueError:
            return False, "Must be a valid integer"
    
    def validate_positive_integer(self, value: str, config: Dict) -> tuple[bool, str]:
        """Validate positive integer values"""
        try:
            num = int(value)
            if num <= 0:
                return False, "Must be a positive integer"
            return True, ""
        except ValueError:
            return False, "Must be a valid integer"
    
    def _format_error_message(self) -> str:
        """Format validation errors into a readable message"""
        message = "\n" + "="*80 + "\n"
        message += "ENVIRONMENT VALIDATION FAILED\n"
        message += "="*80 + "\n\n"
        message += "The following environment variable issues were found:\n\n"
        
        for i, error in enumerate(self.errors, 1):
            message += f"{i}. {error}\n\n"
        
        message += "="*80 + "\n"
        message += "TROUBLESHOOTING TIPS:\n"
        message += "="*80 + "\n"
        message += "1. Check your .env file in the project root\n"
        message += "2. Ensure all required variables are set\n"
        message += "3. Verify variable values meet security requirements\n"
        message += "4. For Dokploy deployment, set variables in the Dokploy interface\n"
        message += "5. Refer to .env.example for proper format and examples\n"
        message += "="*80 + "\n"
        
        return message
    
    def _log_warnings(self):
        """Log validation warnings"""
        print("\n" + "="*60)
        print("ENVIRONMENT VALIDATION WARNINGS")
        print("="*60)
        
        for i, warning in enumerate(self.warnings, 1):
            print(f"{i}. {warning}\n")
        
        print("="*60 + "\n")


def validate_environment() -> Dict[str, Any]:
    """
    Convenience function to validate environment variables.
    
    Returns:
        Dict containing validated configuration
        
    Raises:
        EnvironmentValidationError: If validation fails
    """
    validator = EnvironmentValidator()
    return validator.validate_all()


def get_database_config(validated_config: Dict[str, Any]) -> str:
    """
    Generate database URL from validated configuration.
    
    Args:
        validated_config: Validated environment configuration
        
    Returns:
        Database URL string
    """
    database_url = validated_config.get('DATABASE_URL')
    
    if database_url:
        return database_url
    
    # Build URL from individual components
    user = validated_config.get('POSTGRES_USER', 'postgres')
    password = validated_config.get('POSTGRES_PASSWORD')
    db_name = validated_config.get('POSTGRES_DB', 'stock_management')
    host = os.getenv('POSTGRES_HOST', 'database')  # Default for Docker Compose
    port = os.getenv('POSTGRES_PORT', '5432')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"