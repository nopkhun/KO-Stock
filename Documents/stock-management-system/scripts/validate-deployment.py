#!/usr/bin/env python3
"""
Pre-deployment validation script for Stock Management System.

This script validates environment variables, Docker configuration, and system
requirements before deployment to ensure a successful Dokploy deployment.

Usage:
    python scripts/validate-deployment.py [--env-file .env.production] [--strict]

Options:
    --env-file: Path to environment file to validate (default: .env.production)
    --strict: Enable strict validation mode (fail on warnings)
    --help: Show this help message
"""

import os
import sys
import re
import argparse
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class ValidationResult:
    """Represents the result of a validation check."""
    
    def __init__(self, name: str, passed: bool, message: str, level: str = 'error'):
        self.name = name
        self.passed = passed
        self.message = message
        self.level = level  # 'error', 'warning', 'info'

class DeploymentValidator:
    """Main validation class for deployment checks."""
    
    def __init__(self, env_file: str = '.env.production', strict: bool = False):
        self.env_file = env_file
        self.strict = strict
        self.env_vars = {}
        self.results: List[ValidationResult] = []
        
        # Required environment variables for production
        self.required_vars = {
            'SECRET_KEY': {
                'min_length': 32,
                'description': 'Flask secret key for session management'
            },
            'POSTGRES_PASSWORD': {
                'min_length': 8,
                'description': 'PostgreSQL database password'
            },
            'CORS_ORIGINS': {
                'min_length': 1,
                'description': 'Allowed CORS origins for API access'
            }
        }
        
        # Security-critical variables that must be set correctly
        self.security_vars = {
            'DEBUG': 'false',
            'FLASK_ENV': 'production',
            'SESSION_COOKIE_SECURE': 'true'
        }
        
        # Performance and resource variables with recommended values
        self.performance_vars = {
            'GUNICORN_WORKERS': {'min': 2, 'max': 16, 'recommended': 4},
            'DB_POOL_SIZE': {'min': 5, 'max': 100, 'recommended': 20},
            'MEMORY_LIMIT': {'pattern': r'^\d+[mg]$', 'recommended': '512m'},
            'CPU_LIMIT': {'min': 0.5, 'max': 8.0, 'recommended': 1.0}
        }

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

    def print_result(self, result: ValidationResult):
        """Print a validation result with appropriate formatting."""
        if result.passed:
            icon = f"{Colors.GREEN}✓{Colors.END}"
            color = Colors.GREEN
        else:
            if result.level == 'warning':
                icon = f"{Colors.YELLOW}⚠{Colors.END}"
                color = Colors.YELLOW
            else:
                icon = f"{Colors.RED}✗{Colors.END}"
                color = Colors.RED
        
        print(f"{icon} {Colors.BOLD}{result.name}{Colors.END}: {color}{result.message}{Colors.END}")

    def load_env_file(self) -> bool:
        """Load environment variables from file."""
        if not os.path.exists(self.env_file):
            self.results.append(ValidationResult(
                "Environment File",
                False,
                f"Environment file '{self.env_file}' not found"
            ))
            return False
        
        try:
            with open(self.env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.env_vars[key.strip()] = value.strip()
            
            self.results.append(ValidationResult(
                "Environment File",
                True,
                f"Successfully loaded {len(self.env_vars)} variables from '{self.env_file}'"
            ))
            return True
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Environment File",
                False,
                f"Error reading '{self.env_file}': {str(e)}"
            ))
            return False

    def validate_required_variables(self):
        """Validate that all required environment variables are present and valid."""
        self.print_header("REQUIRED ENVIRONMENT VARIABLES")
        
        for var_name, config in self.required_vars.items():
            if var_name not in self.env_vars:
                self.results.append(ValidationResult(
                    f"Required Variable: {var_name}",
                    False,
                    f"Missing required variable: {config['description']}"
                ))
                continue
            
            value = self.env_vars[var_name]
            
            # Check minimum length
            if len(value) < config['min_length']:
                self.results.append(ValidationResult(
                    f"Required Variable: {var_name}",
                    False,
                    f"Value too short (minimum {config['min_length']} characters)"
                ))
                continue
            
            # Additional validation for specific variables
            if var_name == 'SECRET_KEY':
                if not self._validate_secret_key(value):
                    continue
            elif var_name == 'POSTGRES_PASSWORD':
                if not self._validate_password(value):
                    continue
            elif var_name == 'CORS_ORIGINS':
                if not self._validate_cors_origins(value):
                    continue
            
            self.results.append(ValidationResult(
                f"Required Variable: {var_name}",
                True,
                f"Valid {config['description']}"
            ))

    def _validate_secret_key(self, value: str) -> bool:
        """Validate SECRET_KEY format and strength."""
        # Check for common weak patterns
        weak_patterns = [
            'change_this',
            'secret',
            'password',
            'default',
            '123456',
            'abcdef'
        ]
        
        value_lower = value.lower()
        for pattern in weak_patterns:
            if pattern in value_lower:
                self.results.append(ValidationResult(
                    "Secret Key Security",
                    False,
                    f"SECRET_KEY contains weak pattern '{pattern}' - generate a secure random key"
                ))
                return False
        
        # Check character diversity
        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_special = any(not c.isalnum() for c in value)
        
        diversity_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if diversity_score < 3:
            self.results.append(ValidationResult(
                "Secret Key Security",
                False,
                "SECRET_KEY should contain uppercase, lowercase, digits, and special characters",
                "warning"
            ))
            return not self.strict
        
        return True

    def _validate_password(self, value: str) -> bool:
        """Validate database password strength."""
        if len(value) < 12:
            self.results.append(ValidationResult(
                "Database Password Security",
                False,
                "POSTGRES_PASSWORD should be at least 12 characters for production",
                "warning"
            ))
            return not self.strict
        
        # Check for common weak passwords
        weak_passwords = [
            'password',
            'postgres',
            '123456',
            'admin',
            'root',
            'change_this'
        ]
        
        if value.lower() in weak_passwords:
            self.results.append(ValidationResult(
                "Database Password Security",
                False,
                "POSTGRES_PASSWORD is a common weak password"
            ))
            return False
        
        return True

    def _validate_cors_origins(self, value: str) -> bool:
        """Validate CORS origins format and security."""
        origins = [origin.strip() for origin in value.split(',')]
        
        for origin in origins:
            if origin == '*':
                self.results.append(ValidationResult(
                    "CORS Security",
                    False,
                    "CORS_ORIGINS should not use '*' in production"
                ))
                return False
            
            if not origin.startswith(('http://', 'https://')):
                self.results.append(ValidationResult(
                    "CORS Format",
                    False,
                    f"CORS origin '{origin}' must include protocol (https://)"
                ))
                return False
            
            if origin.startswith('http://') and 'localhost' not in origin:
                self.results.append(ValidationResult(
                    "CORS Security",
                    False,
                    f"CORS origin '{origin}' uses HTTP in production (should use HTTPS)",
                    "warning"
                ))
                if self.strict:
                    return False
        
        return True

    def validate_security_settings(self):
        """Validate security-critical environment variables."""
        self.print_header("SECURITY CONFIGURATION")
        
        for var_name, expected_value in self.security_vars.items():
            if var_name not in self.env_vars:
                self.results.append(ValidationResult(
                    f"Security Setting: {var_name}",
                    False,
                    f"Missing security variable (should be '{expected_value}')"
                ))
                continue
            
            actual_value = self.env_vars[var_name].lower()
            expected_value_lower = expected_value.lower()
            
            if actual_value != expected_value_lower:
                self.results.append(ValidationResult(
                    f"Security Setting: {var_name}",
                    False,
                    f"Insecure value '{actual_value}' (should be '{expected_value}')"
                ))
                continue
            
            self.results.append(ValidationResult(
                f"Security Setting: {var_name}",
                True,
                f"Correctly set to '{expected_value}'"
            ))

    def validate_database_configuration(self):
        """Validate database configuration."""
        self.print_header("DATABASE CONFIGURATION")
        
        # Check if using DATABASE_URL or individual settings
        has_database_url = 'DATABASE_URL' in self.env_vars
        has_individual_settings = all(
            var in self.env_vars 
            for var in ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_HOST']
        )
        
        if not has_database_url and not has_individual_settings:
            self.results.append(ValidationResult(
                "Database Configuration",
                False,
                "Must set either DATABASE_URL or individual database settings"
            ))
            return
        
        if has_database_url:
            self._validate_database_url()
        
        if has_individual_settings:
            self._validate_individual_db_settings()
        
        # Validate connection pool settings
        self._validate_connection_pool()

    def _validate_database_url(self):
        """Validate DATABASE_URL format."""
        database_url = self.env_vars.get('DATABASE_URL', '')
        
        try:
            parsed = urlparse(database_url)
            
            if parsed.scheme != 'postgresql':
                self.results.append(ValidationResult(
                    "Database URL Scheme",
                    False,
                    f"DATABASE_URL scheme should be 'postgresql', got '{parsed.scheme}'"
                ))
                return
            
            if not parsed.hostname:
                self.results.append(ValidationResult(
                    "Database URL Host",
                    False,
                    "DATABASE_URL missing hostname"
                ))
                return
            
            # For Dokploy, hostname should be 'database' (Docker Compose service name)
            if parsed.hostname != 'database' and parsed.hostname != 'localhost':
                self.results.append(ValidationResult(
                    "Database URL Host",
                    False,
                    f"For Dokploy, DATABASE_URL hostname should be 'database', got '{parsed.hostname}'",
                    "warning"
                ))
            
            if not parsed.password:
                self.results.append(ValidationResult(
                    "Database URL Password",
                    False,
                    "DATABASE_URL missing password"
                ))
                return
            
            self.results.append(ValidationResult(
                "Database URL",
                True,
                "DATABASE_URL format is valid"
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Database URL",
                False,
                f"Invalid DATABASE_URL format: {str(e)}"
            ))

    def _validate_individual_db_settings(self):
        """Validate individual database settings."""
        db_host = self.env_vars.get('POSTGRES_HOST', 'localhost')
        
        # For Dokploy, host should be 'database'
        if db_host != 'database' and db_host != 'localhost':
            self.results.append(ValidationResult(
                "Database Host",
                False,
                f"For Dokploy, POSTGRES_HOST should be 'database', got '{db_host}'",
                "warning"
            ))
        
        db_port = self.env_vars.get('POSTGRES_PORT', '5432')
        if not db_port.isdigit() or not (1 <= int(db_port) <= 65535):
            self.results.append(ValidationResult(
                "Database Port",
                False,
                f"Invalid POSTGRES_PORT '{db_port}' (should be 1-65535)"
            ))

    def _validate_connection_pool(self):
        """Validate database connection pool settings."""
        pool_settings = {
            'DB_POOL_SIZE': {'default': 20, 'min': 5, 'max': 100},
            'DB_MAX_OVERFLOW': {'default': 30, 'min': 0, 'max': 200},
            'DB_POOL_TIMEOUT': {'default': 30, 'min': 5, 'max': 300}
        }
        
        for setting, config in pool_settings.items():
            if setting in self.env_vars:
                try:
                    value = int(self.env_vars[setting])
                    if not (config['min'] <= value <= config['max']):
                        self.results.append(ValidationResult(
                            f"Connection Pool: {setting}",
                            False,
                            f"Value {value} outside recommended range {config['min']}-{config['max']}",
                            "warning"
                        ))
                    else:
                        self.results.append(ValidationResult(
                            f"Connection Pool: {setting}",
                            True,
                            f"Value {value} is within recommended range"
                        ))
                except ValueError:
                    self.results.append(ValidationResult(
                        f"Connection Pool: {setting}",
                        False,
                        f"Invalid integer value '{self.env_vars[setting]}'"
                    ))

    def validate_performance_settings(self):
        """Validate performance and resource settings."""
        self.print_header("PERFORMANCE CONFIGURATION")
        
        for var_name, config in self.performance_vars.items():
            if var_name not in self.env_vars:
                continue
            
            value = self.env_vars[var_name]
            
            if 'pattern' in config:
                # Pattern-based validation (e.g., memory limits)
                if not re.match(config['pattern'], value):
                    self.results.append(ValidationResult(
                        f"Performance: {var_name}",
                        False,
                        f"Invalid format '{value}' (expected pattern: {config['pattern']})"
                    ))
                    continue
            else:
                # Numeric validation
                try:
                    numeric_value = float(value)
                    if 'min' in config and numeric_value < config['min']:
                        self.results.append(ValidationResult(
                            f"Performance: {var_name}",
                            False,
                            f"Value {numeric_value} below minimum {config['min']}",
                            "warning"
                        ))
                        continue
                    
                    if 'max' in config and numeric_value > config['max']:
                        self.results.append(ValidationResult(
                            f"Performance: {var_name}",
                            False,
                            f"Value {numeric_value} above maximum {config['max']}",
                            "warning"
                        ))
                        continue
                        
                except ValueError:
                    self.results.append(ValidationResult(
                        f"Performance: {var_name}",
                        False,
                        f"Invalid numeric value '{value}'"
                    ))
                    continue
            
            self.results.append(ValidationResult(
                f"Performance: {var_name}",
                True,
                f"Valid configuration: {value}"
            ))

    def validate_docker_configuration(self):
        """Validate Docker and Docker Compose configuration."""
        self.print_header("DOCKER CONFIGURATION")
        
        # Check if docker-compose.yml exists
        compose_files = ['docker-compose.yml', 'docker-compose.dokploy.yml']
        compose_file = None
        
        for file in compose_files:
            if os.path.exists(file):
                compose_file = file
                break
        
        if not compose_file:
            self.results.append(ValidationResult(
                "Docker Compose File",
                False,
                "No docker-compose.yml file found"
            ))
            return
        
        self.results.append(ValidationResult(
            "Docker Compose File",
            True,
            f"Found Docker Compose file: {compose_file}"
        ))
        
        # Check Dockerfile existence
        dockerfiles = [
            'stock-management-backend/Dockerfile',
            'stock-management-frontend/Dockerfile'
        ]
        
        for dockerfile in dockerfiles:
            if os.path.exists(dockerfile):
                self.results.append(ValidationResult(
                    f"Dockerfile: {dockerfile}",
                    True,
                    "Dockerfile exists"
                ))
            else:
                self.results.append(ValidationResult(
                    f"Dockerfile: {dockerfile}",
                    False,
                    "Dockerfile not found"
                ))

    def validate_system_requirements(self):
        """Validate system requirements and dependencies."""
        self.print_header("SYSTEM REQUIREMENTS")
        
        # Check Docker availability
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.results.append(ValidationResult(
                    "Docker",
                    True,
                    f"Docker available: {version}"
                ))
            else:
                self.results.append(ValidationResult(
                    "Docker",
                    False,
                    "Docker not available or not working"
                ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results.append(ValidationResult(
                "Docker",
                False,
                "Docker command not found"
            ))
        
        # Check Docker Compose availability
        try:
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.results.append(ValidationResult(
                    "Docker Compose",
                    True,
                    f"Docker Compose available: {version}"
                ))
            else:
                # Try legacy docker-compose
                result = subprocess.run(['docker-compose', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.results.append(ValidationResult(
                        "Docker Compose",
                        True,
                        f"Docker Compose (legacy) available: {version}"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Docker Compose",
                        False,
                        "Docker Compose not available"
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results.append(ValidationResult(
                "Docker Compose",
                False,
                "Docker Compose command not found"
            ))

    def generate_summary(self) -> Tuple[int, int, int]:
        """Generate and print validation summary."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed and r.level == 'error')
        warnings = sum(1 for r in self.results if not r.passed and r.level == 'warning')
        
        self.print_header("VALIDATION SUMMARY")
        
        print(f"{Colors.GREEN}✓ Passed:{Colors.END} {passed}")
        print(f"{Colors.RED}✗ Failed:{Colors.END} {failed}")
        print(f"{Colors.YELLOW}⚠ Warnings:{Colors.END} {warnings}")
        print(f"{Colors.BOLD}Total Checks:{Colors.END} {len(self.results)}")
        
        # Print failed checks
        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED CHECKS:{Colors.END}")
            for result in self.results:
                if not result.passed and result.level == 'error':
                    print(f"  {Colors.RED}✗{Colors.END} {result.name}: {result.message}")
        
        # Print warnings
        if warnings > 0:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS:{Colors.END}")
            for result in self.results:
                if not result.passed and result.level == 'warning':
                    print(f"  {Colors.YELLOW}⚠{Colors.END} {result.name}: {result.message}")
        
        return passed, failed, warnings

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print(f"{Colors.BOLD}{Colors.MAGENTA}Stock Management System - Deployment Validation{Colors.END}")
        print(f"Environment file: {self.env_file}")
        print(f"Strict mode: {'Enabled' if self.strict else 'Disabled'}")
        
        # Load environment file
        if not self.load_env_file():
            return False
        
        # Run all validation checks
        self.validate_required_variables()
        self.validate_security_settings()
        self.validate_database_configuration()
        self.validate_performance_settings()
        self.validate_docker_configuration()
        self.validate_system_requirements()
        
        # Print all results
        print(f"\n{Colors.BOLD}{Colors.BLUE}DETAILED RESULTS:{Colors.END}")
        for result in self.results:
            self.print_result(result)
        
        # Generate summary
        passed, failed, warnings = self.generate_summary()
        
        # Determine overall success
        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ VALIDATION FAILED{Colors.END}")
            print(f"Fix the {failed} failed check(s) before deployment.")
            return False
        elif warnings > 0 and self.strict:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ VALIDATION FAILED (STRICT MODE){Colors.END}")
            print(f"Fix the {warnings} warning(s) or disable strict mode.")
            return False
        elif warnings > 0:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ VALIDATION PASSED WITH WARNINGS{Colors.END}")
            print(f"Consider fixing the {warnings} warning(s) for better security/performance.")
            return True
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ VALIDATION PASSED{Colors.END}")
            print("All checks passed. Ready for deployment!")
            return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate Stock Management System deployment configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate-deployment.py
  python scripts/validate-deployment.py --env-file .env.production
  python scripts/validate-deployment.py --strict
  python scripts/validate-deployment.py --env-file .env.production --strict
        """
    )
    
    parser.add_argument(
        '--env-file',
        default='.env.production',
        help='Path to environment file to validate (default: .env.production)'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict validation mode (fail on warnings)'
    )
    
    args = parser.parse_args()
    
    # Create validator and run validation
    validator = DeploymentValidator(args.env_file, args.strict)
    success = validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()