#!/bin/bash

# =============================================================================
# Stock Management System - Deployment Check Script
# =============================================================================
# This script provides a convenient wrapper for running deployment validation
# and verification checks for the Stock Management System.
#
# Usage:
#   ./scripts/deployment-check.sh [validate|verify|both] [options]
#
# Commands:
#   validate  - Run pre-deployment validation
#   verify    - Run post-deployment verification  
#   both      - Run both validation and verification
#   help      - Show this help message
#
# Examples:
#   ./scripts/deployment-check.sh validate
#   ./scripts/deployment-check.sh verify --base-url https://myapp.com
#   ./scripts/deployment-check.sh both --env-file .env.production
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
COMMAND=""
ENV_FILE=".env.production"
BASE_URL="http://localhost"
STRICT_MODE=false
VERBOSE=false

# Function to print colored output
print_header() {
    echo -e "${BOLD}${CYAN}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Function to show help
show_help() {
    cat << EOF
${BOLD}Stock Management System - Deployment Check Script${NC}

${BOLD}USAGE:${NC}
    $0 [COMMAND] [OPTIONS]

${BOLD}COMMANDS:${NC}
    validate    Run pre-deployment validation checks
    verify      Run post-deployment verification checks
    both        Run both validation and verification
    help        Show this help message

${BOLD}OPTIONS:${NC}
    --env-file FILE     Environment file to validate (default: .env.production)
    --base-url URL      Base URL for verification (default: http://localhost)
    --strict            Enable strict validation mode
    --verbose           Enable verbose output
    --help              Show this help message

${BOLD}EXAMPLES:${NC}
    # Run validation with default settings
    $0 validate

    # Run validation with custom environment file
    $0 validate --env-file .env.prod

    # Run validation in strict mode
    $0 validate --strict

    # Run verification against production URL
    $0 verify --base-url https://myapp.com

    # Run verification with verbose output
    $0 verify --base-url https://myapp.com --verbose

    # Run both validation and verification
    $0 both --env-file .env.production --base-url https://myapp.com

    # Run both with all options
    $0 both --env-file .env.prod --base-url https://myapp.com --strict --verbose

${BOLD}VALIDATION CHECKS:${NC}
    - Required environment variables
    - Security configuration
    - Database settings
    - Performance settings
    - Docker configuration
    - System requirements

${BOLD}VERIFICATION CHECKS:${NC}
    - Frontend accessibility
    - API health endpoints
    - Database connectivity
    - CORS configuration
    - Security headers
    - Performance metrics

${BOLD}EXIT CODES:${NC}
    0    All checks passed
    1    Validation/verification failed
    2    Invalid arguments or script error

EOF
}

# Function to check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 2
    fi
}

# Function to check if required scripts exist
check_scripts() {
    local script_dir="$(dirname "$0")"
    
    if [[ ! -f "$script_dir/validate-deployment.py" ]]; then
        print_error "Validation script not found: $script_dir/validate-deployment.py"
        exit 2
    fi
    
    if [[ ! -f "$script_dir/verify-deployment.py" ]]; then
        print_error "Verification script not found: $script_dir/verify-deployment.py"
        exit 2
    fi
}

# Function to run validation
run_validation() {
    local script_dir="$(dirname "$0")"
    local args=("--env-file" "$ENV_FILE")
    
    if [[ "$STRICT_MODE" == "true" ]]; then
        args+=("--strict")
    fi
    
    print_header "Running Pre-Deployment Validation..."
    print_info "Environment file: $ENV_FILE"
    print_info "Strict mode: $STRICT_MODE"
    
    if python3 "$script_dir/validate-deployment.py" "${args[@]}"; then
        print_success "Validation completed successfully"
        return 0
    else
        print_error "Validation failed"
        return 1
    fi
}

# Function to run verification
run_verification() {
    local script_dir="$(dirname "$0")"
    local args=("--base-url" "$BASE_URL")
    
    if [[ "$VERBOSE" == "true" ]]; then
        args+=("--verbose")
    fi
    
    print_header "Running Post-Deployment Verification..."
    print_info "Base URL: $BASE_URL"
    print_info "Verbose mode: $VERBOSE"
    
    if python3 "$script_dir/verify-deployment.py" "${args[@]}"; then
        print_success "Verification completed successfully"
        return 0
    else
        print_error "Verification failed"
        return 1
    fi
}

# Function to run both validation and verification
run_both() {
    local validation_result=0
    local verification_result=0
    
    print_header "Running Complete Deployment Check..."
    
    # Run validation first
    if ! run_validation; then
        validation_result=1
    fi
    
    echo  # Add spacing between validation and verification
    
    # Run verification regardless of validation result
    if ! run_verification; then
        verification_result=1
    fi
    
    # Summary
    echo
    print_header "Summary"
    
    if [[ $validation_result -eq 0 ]]; then
        print_success "Pre-deployment validation passed"
    else
        print_error "Pre-deployment validation failed"
    fi
    
    if [[ $verification_result -eq 0 ]]; then
        print_success "Post-deployment verification passed"
    else
        print_error "Post-deployment verification failed"
    fi
    
    # Return failure if either check failed
    if [[ $validation_result -ne 0 || $verification_result -ne 0 ]]; then
        return 1
    fi
    
    return 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        validate|verify|both|help)
            if [[ -n "$COMMAND" ]]; then
                print_error "Multiple commands specified. Use only one command."
                exit 2
            fi
            COMMAND="$1"
            shift
            ;;
        --env-file)
            if [[ -z "$2" ]]; then
                print_error "--env-file requires a value"
                exit 2
            fi
            ENV_FILE="$2"
            shift 2
            ;;
        --base-url)
            if [[ -z "$2" ]]; then
                print_error "--base-url requires a value"
                exit 2
            fi
            BASE_URL="$2"
            shift 2
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use '$0 help' for usage information."
            exit 2
            ;;
    esac
done

# Set default command if none specified
if [[ -z "$COMMAND" ]]; then
    COMMAND="both"
fi

# Show help if requested
if [[ "$COMMAND" == "help" ]]; then
    show_help
    exit 0
fi

# Check prerequisites
check_python
check_scripts

# Execute the requested command
case "$COMMAND" in
    validate)
        if run_validation; then
            exit 0
        else
            exit 1
        fi
        ;;
    verify)
        if run_verification; then
            exit 0
        else
            exit 1
        fi
        ;;
    both)
        if run_both; then
            print_success "All deployment checks passed!"
            exit 0
        else
            print_error "One or more deployment checks failed"
            exit 1
        fi
        ;;
    *)
        print_error "Invalid command: $COMMAND"
        echo "Use '$0 help' for usage information."
        exit 2
        ;;
esac