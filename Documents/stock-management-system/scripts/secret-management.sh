#!/bin/bash

# =============================================================================
# Secret Management Script for Stock Management System
# =============================================================================
# This script provides utilities for secure secret management in production
# deployments, including secret generation, validation, and rotation.
#
# Usage:
#   ./scripts/secret-management.sh [command] [options]
#
# Commands:
#   generate    Generate secure secrets for production
#   validate    Validate existing secrets
#   rotate      Rotate existing secrets (with backup)
#   check       Check for exposed secrets in codebase
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="$PROJECT_ROOT/.secrets"
BACKUP_DIR="$PROJECT_ROOT/.secrets/backups"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to generate secure random string
generate_secure_string() {
    local length="${1:-32}"
    local charset="${2:-A-Za-z0-9}"
    
    # Use multiple sources for better entropy
    if command -v openssl &> /dev/null; then
        openssl rand -base64 $((length * 3 / 4)) | tr -d "=+/" | cut -c1-${length}
    elif command -v python3 &> /dev/null; then
        python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range($length)))"
    else
        # Fallback to /dev/urandom
        tr -dc "$charset" < /dev/urandom | head -c "$length"
    fi
}

# Function to generate database password
generate_db_password() {
    local length="${1:-16}"
    
    # Generate password with mixed case, numbers, and symbols
    local password=""
    
    # Ensure at least one of each character type
    password+=$(tr -dc 'A-Z' < /dev/urandom | head -c 2)
    password+=$(tr -dc 'a-z' < /dev/urandom | head -c 2)
    password+=$(tr -dc '0-9' < /dev/urandom | head -c 2)
    password+=$(tr -dc '!@#$%^&*' < /dev/urandom | head -c 2)
    
    # Fill remaining length with mixed characters
    local remaining=$((length - 8))
    password+=$(tr -dc 'A-Za-z0-9!@#$%^&*' < /dev/urandom | head -c "$remaining")
    
    # Shuffle the password
    echo "$password" | fold -w1 | shuf | tr -d '\n'
}

# Function to validate secret strength
validate_secret_strength() {
    local secret="$1"
    local min_length="${2:-32}"
    local secret_name="${3:-secret}"
    
    local issues=()
    
    # Check length
    if [ ${#secret} -lt "$min_length" ]; then
        issues+=("Length is ${#secret}, minimum required is $min_length")
    fi
    
    # Check for common weak patterns
    if [[ "$secret" =~ ^[a-z]+$ ]]; then
        issues+=("Contains only lowercase letters")
    fi
    
    if [[ "$secret" =~ ^[A-Z]+$ ]]; then
        issues+=("Contains only uppercase letters")
    fi
    
    if [[ "$secret" =~ ^[0-9]+$ ]]; then
        issues+=("Contains only numbers")
    fi
    
    # Check for common weak passwords
    local weak_patterns=("password" "123456" "admin" "root" "test" "demo" "change" "default")
    for pattern in "${weak_patterns[@]}"; do
        if [[ "${secret,,}" == *"$pattern"* ]]; then
            issues+=("Contains weak pattern: $pattern")
        fi
    done
    
    # Check entropy (basic check)
    local unique_chars=$(echo "$secret" | fold -w1 | sort -u | wc -l)
    if [ "$unique_chars" -lt 8 ]; then
        issues+=("Low character diversity (only $unique_chars unique characters)")
    fi
    
    if [ ${#issues[@]} -eq 0 ]; then
        print_success "$secret_name validation passed"
        return 0
    else
        print_error "$secret_name validation failed:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return 1
    fi
}

# Function to generate all production secrets
generate_secrets() {
    print_status "Generating secure secrets for production deployment..."
    
    # Create secrets directory
    mkdir -p "$SECRETS_DIR"
    chmod 700 "$SECRETS_DIR"
    
    local secrets_file="$SECRETS_DIR/production-secrets.env"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    # Backup existing secrets if they exist
    if [ -f "$secrets_file" ]; then
        mkdir -p "$BACKUP_DIR"
        cp "$secrets_file" "$BACKUP_DIR/production-secrets-backup-$timestamp.env"
        print_status "Backed up existing secrets to: $BACKUP_DIR/production-secrets-backup-$timestamp.env"
    fi
    
    print_status "Generating new secrets..."
    
    # Generate secrets
    local secret_key=$(generate_secure_string 64)
    local db_password=$(generate_db_password 20)
    local jwt_secret=$(generate_secure_string 64)
    
    # Create secrets file
    cat > "$secrets_file" << EOF
# =============================================================================
# PRODUCTION SECRETS - GENERATED $(date)
# =============================================================================
# WARNING: This file contains sensitive production secrets!
# 
# Security Guidelines:
# 1. Never commit this file to version control
# 2. Restrict file permissions (600 or 700)
# 3. Use secure channels to transfer these secrets
# 4. Rotate secrets regularly (every 90 days recommended)
# 5. Use environment variable injection in production (Dokploy)
# =============================================================================

# Flask Application Secret Key (64 characters)
# Used for session management, CSRF protection, and cryptographic operations
SECRET_KEY=$secret_key

# Database Password (20 characters with mixed case, numbers, symbols)
# Use this as POSTGRES_PASSWORD in your environment
POSTGRES_PASSWORD=$db_password

# JWT Secret Key (64 characters) - Optional if using JWT authentication
# Keep this different from SECRET_KEY for additional security
JWT_SECRET_KEY=$jwt_secret

# =============================================================================
# DEPLOYMENT INSTRUCTIONS
# =============================================================================
# 
# For Dokploy deployment:
# 1. Copy these values to Dokploy's environment variables interface
# 2. Set SECRET_KEY in Dokploy environment variables
# 3. Set POSTGRES_PASSWORD in Dokploy environment variables
# 4. Optionally set JWT_SECRET_KEY if using JWT authentication
# 
# For manual deployment:
# 1. Export these as environment variables before starting the application
# 2. Or add them to your .env file (ensure .env is in .gitignore)
# 
# Security Notes:
# - These secrets are cryptographically secure random strings
# - SECRET_KEY: 64 characters for maximum security
# - POSTGRES_PASSWORD: 20 characters with mixed character types
# - All secrets have been validated for strength and entropy
# 
# =============================================================================

EOF

    # Set secure permissions
    chmod 600 "$secrets_file"
    
    # Validate generated secrets
    print_status "Validating generated secrets..."
    
    local validation_passed=true
    
    if ! validate_secret_strength "$secret_key" 32 "SECRET_KEY"; then
        validation_passed=false
    fi
    
    if ! validate_secret_strength "$db_password" 12 "POSTGRES_PASSWORD"; then
        validation_passed=false
    fi
    
    if ! validate_secret_strength "$jwt_secret" 32 "JWT_SECRET_KEY"; then
        validation_passed=false
    fi
    
    if [ "$validation_passed" = true ]; then
        print_success "All secrets generated and validated successfully!"
        echo ""
        echo "Secrets saved to: $secrets_file"
        echo ""
        echo "Next steps:"
        echo "1. Review the generated secrets file"
        echo "2. Copy the secrets to your deployment environment (Dokploy)"
        echo "3. Ensure the secrets file is not committed to version control"
        echo "4. Set up regular secret rotation (recommended: every 90 days)"
        echo ""
        print_warning "IMPORTANT: Keep these secrets secure and never share them in plain text!"
    else
        print_error "Secret validation failed. Please regenerate secrets."
        return 1
    fi
}

# Function to validate existing secrets
validate_secrets() {
    print_status "Validating existing secrets..."
    
    local secrets_file="$SECRETS_DIR/production-secrets.env"
    
    if [ ! -f "$secrets_file" ]; then
        print_error "No secrets file found at: $secrets_file"
        echo "Run: $0 generate"
        return 1
    fi
    
    # Source the secrets file
    source "$secrets_file"
    
    local validation_passed=true
    
    # Validate SECRET_KEY
    if [ -n "${SECRET_KEY:-}" ]; then
        if ! validate_secret_strength "$SECRET_KEY" 32 "SECRET_KEY"; then
            validation_passed=false
        fi
    else
        print_error "SECRET_KEY not found in secrets file"
        validation_passed=false
    fi
    
    # Validate POSTGRES_PASSWORD
    if [ -n "${POSTGRES_PASSWORD:-}" ]; then
        if ! validate_secret_strength "$POSTGRES_PASSWORD" 12 "POSTGRES_PASSWORD"; then
            validation_passed=false
        fi
    else
        print_error "POSTGRES_PASSWORD not found in secrets file"
        validation_passed=false
    fi
    
    # Validate JWT_SECRET_KEY (optional)
    if [ -n "${JWT_SECRET_KEY:-}" ]; then
        if ! validate_secret_strength "$JWT_SECRET_KEY" 32 "JWT_SECRET_KEY"; then
            validation_passed=false
        fi
    fi
    
    if [ "$validation_passed" = true ]; then
        print_success "All secrets validation passed!"
        
        # Check file permissions
        local file_perms=$(stat -c "%a" "$secrets_file" 2>/dev/null || stat -f "%A" "$secrets_file" 2>/dev/null || echo "unknown")
        if [ "$file_perms" != "600" ]; then
            print_warning "Secrets file permissions are $file_perms, recommended: 600"
            echo "Fix with: chmod 600 $secrets_file"
        fi
        
        return 0
    else
        print_error "Secret validation failed!"
        echo "Consider regenerating secrets with: $0 generate"
        return 1
    fi
}

# Function to rotate secrets
rotate_secrets() {
    print_status "Rotating production secrets..."
    
    local secrets_file="$SECRETS_DIR/production-secrets.env"
    
    if [ ! -f "$secrets_file" ]; then
        print_error "No existing secrets file found. Generate initial secrets first."
        echo "Run: $0 generate"
        return 1
    fi
    
    # Confirm rotation
    echo ""
    print_warning "Secret rotation will generate new secrets and backup the old ones."
    echo "This will require updating your deployment environment with new values."
    echo ""
    read -p "Are you sure you want to rotate secrets? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Secret rotation cancelled."
        return 0
    fi
    
    # Generate new secrets (this will automatically backup old ones)
    generate_secrets
    
    echo ""
    print_success "Secret rotation completed!"
    echo ""
    echo "IMPORTANT: Update your deployment environment with the new secrets:"
    echo "1. Update Dokploy environment variables with new values"
    echo "2. Restart the application to use new secrets"
    echo "3. Verify the application works with new secrets"
    echo "4. Old secrets are backed up in: $BACKUP_DIR"
}

# Function to check for exposed secrets
check_exposed_secrets() {
    print_status "Checking for exposed secrets in codebase..."
    
    local issues_found=false
    
    # Patterns to search for
    local secret_patterns=(
        "SECRET_KEY\s*=\s*['\"][^'\"]{8,}"
        "POSTGRES_PASSWORD\s*=\s*['\"][^'\"]{8,}"
        "JWT_SECRET\s*=\s*['\"][^'\"]{8,}"
        "password\s*=\s*['\"][^'\"]{8,}"
        "api_key\s*=\s*['\"][^'\"]{8,}"
        "token\s*=\s*['\"][^'\"]{8,}"
    )
    
    # Files to exclude from search
    local exclude_patterns=(
        "*.example"
        "*.template"
        "*.md"
        ".git/*"
        "node_modules/*"
        "__pycache__/*"
        "*.pyc"
        ".secrets/*"
        "security-scan-results/*"
    )
    
    # Build exclude arguments for grep
    local exclude_args=""
    for pattern in "${exclude_patterns[@]}"; do
        exclude_args+="--exclude=$pattern "
    done
    
    print_status "Scanning for potential secret patterns..."
    
    for pattern in "${secret_patterns[@]}"; do
        local matches=$(grep -r -i -E "$pattern" "$PROJECT_ROOT" $exclude_args 2>/dev/null || true)
        
        if [ -n "$matches" ]; then
            print_warning "Potential secret found with pattern: $pattern"
            echo "$matches"
            echo ""
            issues_found=true
        fi
    done
    
    # Check for common secret file names
    print_status "Checking for common secret file names..."
    
    local secret_files=(
        ".env"
        "secrets.txt"
        "passwords.txt"
        "config.json"
        "credentials.json"
    )
    
    for file in "${secret_files[@]}"; do
        if find "$PROJECT_ROOT" -name "$file" -not -path "*/.git/*" -not -path "*/.secrets/*" | grep -q .; then
            print_warning "Found potential secret file: $file"
            find "$PROJECT_ROOT" -name "$file" -not -path "*/.git/*" -not -path "*/.secrets/*"
            echo ""
            issues_found=true
        fi
    done
    
    if [ "$issues_found" = false ]; then
        print_success "No exposed secrets detected in codebase"
        return 0
    else
        print_error "Potential secret exposure detected!"
        echo ""
        echo "Recommendations:"
        echo "1. Remove any hardcoded secrets from source code"
        echo "2. Use environment variables for all sensitive configuration"
        echo "3. Add sensitive files to .gitignore"
        echo "4. Use secret management tools in production"
        echo "5. Rotate any exposed secrets immediately"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Stock Management System - Secret Management"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  generate    Generate secure secrets for production"
    echo "  validate    Validate existing secrets for strength and security"
    echo "  rotate      Rotate existing secrets (creates backup)"
    echo "  check       Check codebase for exposed secrets"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 generate                 # Generate new production secrets"
    echo "  $0 validate                 # Validate existing secrets"
    echo "  $0 rotate                   # Rotate all secrets"
    echo "  $0 check                    # Check for exposed secrets"
    echo ""
    echo "Security Features:"
    echo "  - Cryptographically secure random generation"
    echo "  - Strength validation with entropy checking"
    echo "  - Automatic backup before rotation"
    echo "  - Secure file permissions (600)"
    echo "  - Pattern-based secret detection"
    echo ""
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "generate")
            generate_secrets
            ;;
        "validate")
            validate_secrets
            ;;
        "rotate")
            rotate_secrets
            ;;
        "check")
            check_exposed_secrets
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"