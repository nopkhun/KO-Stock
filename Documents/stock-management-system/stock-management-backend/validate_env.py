#!/usr/bin/env python3
"""
Environment Validation Script for Stock Management System

This script validates environment variables before deployment.
Use this to check your configuration before starting the application.

Usage:
    python validate_env.py
    
    # With custom .env file:
    python validate_env.py --env-file /path/to/.env
    
    # Check specific environment:
    FLASK_ENV=production python validate_env.py
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config.env_validator import validate_environment, EnvironmentValidationError
except ImportError as e:
    print(f"❌ Failed to import validation module: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)


def load_env_file(env_file_path: str):
    """Load environment variables from a .env file"""
    if not os.path.exists(env_file_path):
        print(f"❌ Environment file not found: {env_file_path}")
        return False
    
    try:
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
        
        print(f"✓ Loaded environment from: {env_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load environment file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate environment configuration for Stock Management System"
    )
    parser.add_argument(
        '--env-file', 
        help='Path to .env file to load before validation'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only show errors and warnings'
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("Stock Management System - Environment Validation")
        print("=" * 60)
    
    # Load .env file if specified
    if args.env_file:
        if not load_env_file(args.env_file):
            sys.exit(1)
    
    # Try to validate environment
    try:
        if not args.quiet:
            print("Validating environment configuration...")
        
        config = validate_environment()
        
        if not args.quiet:
            print("✓ Environment validation successful!")
            print("\nConfiguration summary:")
            print(f"  Flask Environment: {config.get('FLASK_ENV', 'unknown')}")
            print(f"  Debug Mode: {config.get('DEBUG', 'false')}")
            print(f"  Database: {'PostgreSQL' if config.get('DATABASE_URL') or config.get('POSTGRES_PASSWORD') else 'Not configured'}")
            print(f"  CORS Origins: {config.get('CORS_ORIGINS', 'default')}")
            print(f"  Secure Cookies: {config.get('SESSION_COOKIE_SECURE', 'false')}")
            print(f"  Secret Key: {'✓ Configured' if config.get('SECRET_KEY') else '❌ Missing'}")
        
        return 0
        
    except EnvironmentValidationError as e:
        print(str(e))
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected validation error: {e}")
        import traceback
        if not args.quiet:
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())