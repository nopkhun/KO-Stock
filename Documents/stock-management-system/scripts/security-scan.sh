#!/bin/bash

# =============================================================================
# Security Scanning Script for Stock Management System
# =============================================================================
# This script performs security scans on Docker images and dependencies
# to identify potential vulnerabilities before deployment.
#
# Usage:
#   ./scripts/security-scan.sh [--backend|--frontend|--all]
#
# Requirements:
#   - Docker
#   - trivy (for vulnerability scanning)
#   - hadolint (for Dockerfile linting)
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
BACKEND_DIR="$PROJECT_ROOT/stock-management-backend"
FRONTEND_DIR="$PROJECT_ROOT/stock-management-frontend"

# Image names
BACKEND_IMAGE="stock-management-backend:security-scan"
FRONTEND_IMAGE="stock-management-frontend:security-scan"

# Scan results directory
SCAN_RESULTS_DIR="$PROJECT_ROOT/security-scan-results"
mkdir -p "$SCAN_RESULTS_DIR"

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

# Function to check if required tools are installed
check_dependencies() {
    print_status "Checking required dependencies..."
    
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v trivy &> /dev/null; then
        missing_deps+=("trivy")
    fi
    
    if ! command -v hadolint &> /dev/null; then
        missing_deps+=("hadolint")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Installation instructions:"
        echo "  Docker: https://docs.docker.com/get-docker/"
        echo "  Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
        echo "  Hadolint: https://github.com/hadolint/hadolint#install"
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Function to lint Dockerfile
lint_dockerfile() {
    local dockerfile_path="$1"
    local component="$2"
    
    print_status "Linting Dockerfile for $component..."
    
    local output_file="$SCAN_RESULTS_DIR/${component}-dockerfile-lint.txt"
    
    if hadolint "$dockerfile_path" > "$output_file" 2>&1; then
        print_success "Dockerfile lint passed for $component"
        return 0
    else
        print_warning "Dockerfile lint found issues for $component"
        echo "Results saved to: $output_file"
        cat "$output_file"
        return 1
    fi
}

# Function to build Docker image for scanning
build_image() {
    local build_dir="$1"
    local image_name="$2"
    local component="$3"
    
    print_status "Building $component image for security scanning..."
    
    cd "$build_dir"
    
    if docker build -t "$image_name" . > /dev/null 2>&1; then
        print_success "Successfully built $component image"
        return 0
    else
        print_error "Failed to build $component image"
        return 1
    fi
}

# Function to scan image for vulnerabilities
scan_image_vulnerabilities() {
    local image_name="$1"
    local component="$2"
    
    print_status "Scanning $component image for vulnerabilities..."
    
    local output_file="$SCAN_RESULTS_DIR/${component}-vulnerabilities.json"
    local summary_file="$SCAN_RESULTS_DIR/${component}-vulnerability-summary.txt"
    
    # Scan for vulnerabilities
    if trivy image --format json --output "$output_file" "$image_name" > /dev/null 2>&1; then
        # Generate human-readable summary
        trivy image --format table "$image_name" > "$summary_file" 2>&1
        
        # Check for critical/high vulnerabilities
        local critical_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$output_file" 2>/dev/null || echo "0")
        local high_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' "$output_file" 2>/dev/null || echo "0")
        
        if [ "$critical_count" -gt 0 ] || [ "$high_count" -gt 0 ]; then
            print_warning "$component has $critical_count critical and $high_count high severity vulnerabilities"
            echo "Detailed results: $output_file"
            echo "Summary: $summary_file"
            return 1
        else
            print_success "$component vulnerability scan passed"
            return 0
        fi
    else
        print_error "Failed to scan $component for vulnerabilities"
        return 1
    fi
}

# Function to scan for secrets
scan_secrets() {
    local build_dir="$1"
    local component="$2"
    
    print_status "Scanning $component for secrets and sensitive data..."
    
    local output_file="$SCAN_RESULTS_DIR/${component}-secrets.txt"
    
    # Use trivy to scan for secrets
    if trivy fs --scanners secret --format table "$build_dir" > "$output_file" 2>&1; then
        # Check if any secrets were found
        if grep -q "Total: 0" "$output_file"; then
            print_success "$component secrets scan passed"
            return 0
        else
            print_warning "$component may contain secrets or sensitive data"
            echo "Results saved to: $output_file"
            cat "$output_file"
            return 1
        fi
    else
        print_error "Failed to scan $component for secrets"
        return 1
    fi
}

# Function to check Python dependencies for known vulnerabilities
scan_python_dependencies() {
    print_status "Scanning Python dependencies for vulnerabilities..."
    
    local output_file="$SCAN_RESULTS_DIR/python-dependencies-vulnerabilities.txt"
    
    cd "$BACKEND_DIR"
    
    # Use trivy to scan requirements.txt
    if trivy fs --scanners vuln --format table requirements.txt > "$output_file" 2>&1; then
        if grep -q "Total: 0" "$output_file"; then
            print_success "Python dependencies scan passed"
            return 0
        else
            print_warning "Python dependencies have known vulnerabilities"
            echo "Results saved to: $output_file"
            cat "$output_file"
            return 1
        fi
    else
        print_error "Failed to scan Python dependencies"
        return 1
    fi
}

# Function to check Node.js dependencies for known vulnerabilities
scan_node_dependencies() {
    print_status "Scanning Node.js dependencies for vulnerabilities..."
    
    local output_file="$SCAN_RESULTS_DIR/node-dependencies-vulnerabilities.txt"
    
    cd "$FRONTEND_DIR"
    
    # Use npm audit if package-lock.json exists, otherwise use trivy
    if [ -f "package-lock.json" ]; then
        if npm audit --audit-level=moderate > "$output_file" 2>&1; then
            print_success "Node.js dependencies scan passed"
            return 0
        else
            print_warning "Node.js dependencies have known vulnerabilities"
            echo "Results saved to: $output_file"
            cat "$output_file"
            return 1
        fi
    else
        # Use trivy to scan package.json
        if trivy fs --scanners vuln --format table package.json > "$output_file" 2>&1; then
            if grep -q "Total: 0" "$output_file"; then
                print_success "Node.js dependencies scan passed"
                return 0
            else
                print_warning "Node.js dependencies have known vulnerabilities"
                echo "Results saved to: $output_file"
                cat "$output_file"
                return 1
            fi
        else
            print_error "Failed to scan Node.js dependencies"
            return 1
        fi
    fi
}

# Function to perform comprehensive security scan
scan_component() {
    local component="$1"
    local build_dir="$2"
    local dockerfile_path="$3"
    local image_name="$4"
    
    print_status "Starting security scan for $component..."
    echo "=================================="
    
    local scan_results=()
    
    # Lint Dockerfile
    if lint_dockerfile "$dockerfile_path" "$component"; then
        scan_results+=("dockerfile_lint:PASS")
    else
        scan_results+=("dockerfile_lint:FAIL")
    fi
    
    # Scan for secrets
    if scan_secrets "$build_dir" "$component"; then
        scan_results+=("secrets:PASS")
    else
        scan_results+=("secrets:FAIL")
    fi
    
    # Build image
    if build_image "$build_dir" "$image_name" "$component"; then
        # Scan image vulnerabilities
        if scan_image_vulnerabilities "$image_name" "$component"; then
            scan_results+=("vulnerabilities:PASS")
        else
            scan_results+=("vulnerabilities:FAIL")
        fi
        
        # Clean up image
        docker rmi "$image_name" > /dev/null 2>&1 || true
    else
        scan_results+=("build:FAIL")
    fi
    
    # Print component results
    echo ""
    print_status "$component scan results:"
    for result in "${scan_results[@]}"; do
        local test_name="${result%:*}"
        local test_result="${result#*:}"
        
        if [ "$test_result" = "PASS" ]; then
            print_success "  $test_name: PASSED"
        else
            print_error "  $test_name: FAILED"
        fi
    done
    
    echo ""
    
    # Return 0 if all tests passed, 1 otherwise
    for result in "${scan_results[@]}"; do
        if [[ "$result" == *":FAIL" ]]; then
            return 1
        fi
    done
    
    return 0
}

# Function to generate security report
generate_report() {
    local report_file="$SCAN_RESULTS_DIR/security-scan-report.md"
    
    print_status "Generating security scan report..."
    
    cat > "$report_file" << EOF
# Security Scan Report

**Generated:** $(date)
**Project:** Stock Management System

## Summary

This report contains the results of security scans performed on the Stock Management System components.

## Scan Results

### Backend (Flask Application)

- **Dockerfile Lint:** $([ -f "$SCAN_RESULTS_DIR/backend-dockerfile-lint.txt" ] && echo "See backend-dockerfile-lint.txt" || echo "Not performed")
- **Vulnerability Scan:** $([ -f "$SCAN_RESULTS_DIR/backend-vulnerabilities.json" ] && echo "See backend-vulnerability-summary.txt" || echo "Not performed")
- **Secrets Scan:** $([ -f "$SCAN_RESULTS_DIR/backend-secrets.txt" ] && echo "See backend-secrets.txt" || echo "Not performed")
- **Python Dependencies:** $([ -f "$SCAN_RESULTS_DIR/python-dependencies-vulnerabilities.txt" ] && echo "See python-dependencies-vulnerabilities.txt" || echo "Not performed")

### Frontend (React/Nginx Application)

- **Dockerfile Lint:** $([ -f "$SCAN_RESULTS_DIR/frontend-dockerfile-lint.txt" ] && echo "See frontend-dockerfile-lint.txt" || echo "Not performed")
- **Vulnerability Scan:** $([ -f "$SCAN_RESULTS_DIR/frontend-vulnerabilities.json" ] && echo "See frontend-vulnerability-summary.txt" || echo "Not performed")
- **Secrets Scan:** $([ -f "$SCAN_RESULTS_DIR/frontend-secrets.txt" ] && echo "See frontend-secrets.txt" || echo "Not performed")
- **Node.js Dependencies:** $([ -f "$SCAN_RESULTS_DIR/node-dependencies-vulnerabilities.txt" ] && echo "See node-dependencies-vulnerabilities.txt" || echo "Not performed")

## Recommendations

1. **Critical/High Vulnerabilities:** Address any critical or high severity vulnerabilities immediately
2. **Dockerfile Issues:** Fix any Dockerfile linting issues for better security practices
3. **Secrets:** Remove any detected secrets or sensitive data from the codebase
4. **Dependencies:** Update vulnerable dependencies to secure versions
5. **Regular Scanning:** Integrate security scanning into your CI/CD pipeline

## Files Generated

EOF
    
    # List all generated files
    for file in "$SCAN_RESULTS_DIR"/*; do
        if [ -f "$file" ]; then
            echo "- $(basename "$file")" >> "$report_file"
        fi
    done
    
    print_success "Security report generated: $report_file"
}

# Main function
main() {
    local scan_target="${1:-all}"
    
    echo "Stock Management System - Security Scanner"
    echo "=========================================="
    echo ""
    
    # Check dependencies
    check_dependencies
    echo ""
    
    # Clean previous results
    rm -rf "$SCAN_RESULTS_DIR"/*
    
    local overall_result=0
    
    case "$scan_target" in
        "backend"|"--backend")
            if ! scan_component "backend" "$BACKEND_DIR" "$BACKEND_DIR/Dockerfile" "$BACKEND_IMAGE"; then
                overall_result=1
            fi
            if ! scan_python_dependencies; then
                overall_result=1
            fi
            ;;
        "frontend"|"--frontend")
            if ! scan_component "frontend" "$FRONTEND_DIR" "$FRONTEND_DIR/Dockerfile" "$FRONTEND_IMAGE"; then
                overall_result=1
            fi
            if ! scan_node_dependencies; then
                overall_result=1
            fi
            ;;
        "all"|"--all"|*)
            if ! scan_component "backend" "$BACKEND_DIR" "$BACKEND_DIR/Dockerfile" "$BACKEND_IMAGE"; then
                overall_result=1
            fi
            if ! scan_python_dependencies; then
                overall_result=1
            fi
            echo ""
            if ! scan_component "frontend" "$FRONTEND_DIR" "$FRONTEND_DIR/Dockerfile" "$FRONTEND_IMAGE"; then
                overall_result=1
            fi
            if ! scan_node_dependencies; then
                overall_result=1
            fi
            ;;
    esac
    
    echo ""
    generate_report
    echo ""
    
    if [ $overall_result -eq 0 ]; then
        print_success "All security scans passed!"
        echo ""
        echo "Next steps:"
        echo "1. Review the detailed scan results in: $SCAN_RESULTS_DIR"
        echo "2. Address any warnings or recommendations"
        echo "3. Integrate this script into your CI/CD pipeline"
    else
        print_error "Some security scans failed!"
        echo ""
        echo "Action required:"
        echo "1. Review the failed scans in: $SCAN_RESULTS_DIR"
        echo "2. Address critical and high severity issues"
        echo "3. Re-run the security scan after fixes"
        echo "4. Do not deploy to production until all critical issues are resolved"
    fi
    
    exit $overall_result
}

# Show usage if help is requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [--backend|--frontend|--all]"
    echo ""
    echo "Options:"
    echo "  --backend   Scan only the backend component"
    echo "  --frontend  Scan only the frontend component"
    echo "  --all       Scan all components (default)"
    echo "  --help      Show this help message"
    echo ""
    echo "This script performs comprehensive security scanning including:"
    echo "  - Dockerfile linting"
    echo "  - Vulnerability scanning of Docker images"
    echo "  - Secret detection in source code"
    echo "  - Dependency vulnerability scanning"
    exit 0
fi

# Run main function with arguments
main "$@"