#!/bin/bash

# =============================================================================
# STARTUP OPTIMIZATION SCRIPT FOR STOCK MANAGEMENT SYSTEM
# =============================================================================
# This script optimizes container startup time and resource usage
# Run this script before starting the application stack
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/startup-optimization.log"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check system resources
check_system_resources() {
    log "Checking system resources..."
    
    # Check available memory
    AVAILABLE_MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    TOTAL_MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    MEMORY_USAGE_PERCENT=$(( (TOTAL_MEMORY - AVAILABLE_MEMORY) * 100 / TOTAL_MEMORY ))
    
    log "Memory: ${AVAILABLE_MEMORY}MB available / ${TOTAL_MEMORY}MB total (${MEMORY_USAGE_PERCENT}% used)"
    
    if [ "$MEMORY_USAGE_PERCENT" -gt 85 ]; then
        log_warning "High memory usage detected (${MEMORY_USAGE_PERCENT}%). Consider freeing up memory before starting containers."
    fi
    
    # Check available disk space
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    DISK_AVAILABLE=$(df -h / | awk 'NR==2 {print $4}')
    
    log "Disk: ${DISK_AVAILABLE} available (${DISK_USAGE}% used)"
    
    if [ "$DISK_USAGE" -gt 85 ]; then
        log_warning "High disk usage detected (${DISK_USAGE}%). Consider cleaning up disk space."
    fi
    
    # Check CPU load
    CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    CPU_CORES=$(nproc)
    
    log "CPU: Load average ${CPU_LOAD} on ${CPU_CORES} cores"
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "System resources check completed"
}

# Function to optimize Docker settings
optimize_docker() {
    log "Optimizing Docker settings..."
    
    # Clean up unused Docker resources
    log "Cleaning up unused Docker resources..."
    docker system prune -f >/dev/null 2>&1 || true
    
    # Remove dangling images
    DANGLING_IMAGES=$(docker images -f "dangling=true" -q)
    if [ -n "$DANGLING_IMAGES" ]; then
        log "Removing dangling images..."
        docker rmi $DANGLING_IMAGES >/dev/null 2>&1 || true
    fi
    
    # Check Docker daemon configuration
    if [ -f /etc/docker/daemon.json ]; then
        log "Docker daemon configuration found"
    else
        log_warning "No Docker daemon configuration found. Consider optimizing Docker settings."
    fi
    
    log_success "Docker optimization completed"
}

# Function to pre-pull Docker images
pre_pull_images() {
    log "Pre-pulling Docker images to optimize startup time..."
    
    cd "$PROJECT_ROOT"
    
    # Pull base images used in Dockerfiles
    log "Pulling base images..."
    docker pull postgres:15-alpine >/dev/null 2>&1 &
    POSTGRES_PID=$!
    
    docker pull python:3.11-slim >/dev/null 2>&1 &
    PYTHON_PID=$!
    
    docker pull node:18-alpine >/dev/null 2>&1 &
    NODE_PID=$!
    
    docker pull nginx:alpine >/dev/null 2>&1 &
    NGINX_PID=$!
    
    # Wait for all pulls to complete
    wait $POSTGRES_PID && log_success "PostgreSQL image pulled"
    wait $PYTHON_PID && log_success "Python image pulled"
    wait $NODE_PID && log_success "Node.js image pulled"
    wait $NGINX_PID && log_success "Nginx image pulled"
    
    log_success "Base images pre-pulled successfully"
}

# Function to optimize application images
optimize_app_images() {
    log "Building optimized application images..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend image with optimizations
    log "Building backend image..."
    docker build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from stock-management-backend:latest \
        -t stock-management-backend:latest \
        ./stock-management-backend/ >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "Backend image built successfully"
    else
        log_error "Failed to build backend image"
        exit 1
    fi
    
    # Build frontend image with optimizations
    log "Building frontend image..."
    docker build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from stock-management-frontend:latest \
        -t stock-management-frontend:latest \
        ./stock-management-frontend/ >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "Frontend image built successfully"
    else
        log_error "Failed to build frontend image"
        exit 1
    fi
}

# Function to prepare volumes
prepare_volumes() {
    log "Preparing Docker volumes..."
    
    # Create named volumes if they don't exist
    docker volume create postgres_data >/dev/null 2>&1 || true
    
    # Check volume permissions
    log "Checking volume permissions..."
    
    log_success "Volumes prepared successfully"
}

# Function to optimize network settings
optimize_network() {
    log "Optimizing network settings..."
    
    # Create custom network if it doesn't exist
    docker network create stock_management_network >/dev/null 2>&1 || true
    
    # Check network configuration
    NETWORK_EXISTS=$(docker network ls | grep stock_management_network | wc -l)
    if [ "$NETWORK_EXISTS" -gt 0 ]; then
        log_success "Custom network configured"
    else
        log_warning "Custom network not found, will use default"
    fi
}

# Function to validate environment configuration
validate_environment() {
    log "Validating environment configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            log_warning ".env file not found, copying from .env.example"
            cp .env.example .env
        else
            log_error ".env file not found and no .env.example available"
            exit 1
        fi
    fi
    
    # Validate critical environment variables
    source .env 2>/dev/null || true
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "CHANGE_THIS_TO_A_RANDOM_32_PLUS_CHARACTER_STRING_FOR_PRODUCTION" ]; then
        log_warning "SECRET_KEY not set or using default value. Please update for production."
    fi
    
    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "change_this_secure_password_123" ]; then
        log_warning "POSTGRES_PASSWORD not set or using default value. Please update for production."
    fi
    
    log_success "Environment validation completed"
}

# Function to warm up application
warmup_application() {
    log "Warming up application components..."
    
    cd "$PROJECT_ROOT"
    
    # Start services in dependency order with optimized startup
    log "Starting database service..."
    docker-compose up -d database
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    timeout=60
    counter=0
    while [ $counter -lt $timeout ]; do
        if docker-compose exec -T database pg_isready -U postgres >/dev/null 2>&1; then
            log_success "Database is ready"
            break
        fi
        sleep 2
        counter=$((counter + 2))
    done
    
    if [ $counter -ge $timeout ]; then
        log_error "Database failed to start within ${timeout} seconds"
        exit 1
    fi
    
    # Start backend service
    log "Starting backend service..."
    docker-compose up -d backend
    
    # Wait for backend to be ready
    log "Waiting for backend to be ready..."
    timeout=90
    counter=0
    while [ $counter -lt $timeout ]; do
        if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
            log_success "Backend is ready"
            break
        fi
        sleep 3
        counter=$((counter + 3))
    done
    
    if [ $counter -ge $timeout ]; then
        log_error "Backend failed to start within ${timeout} seconds"
        exit 1
    fi
    
    # Start frontend service
    log "Starting frontend service..."
    docker-compose up -d frontend
    
    # Wait for frontend to be ready
    log "Waiting for frontend to be ready..."
    timeout=60
    counter=0
    while [ $counter -lt $timeout ]; do
        if curl -f http://localhost/health >/dev/null 2>&1; then
            log_success "Frontend is ready"
            break
        fi
        sleep 2
        counter=$((counter + 2))
    done
    
    if [ $counter -ge $timeout ]; then
        log_error "Frontend failed to start within ${timeout} seconds"
        exit 1
    fi
    
    log_success "All services started successfully"
}

# Function to run performance check
run_performance_check() {
    log "Running performance check..."
    
    # Check if performance monitor script exists
    if [ -f "$SCRIPT_DIR/performance-monitor.py" ]; then
        python3 "$SCRIPT_DIR/performance-monitor.py" --single --url http://localhost
    else
        log_warning "Performance monitor script not found, skipping performance check"
    fi
}

# Main function
main() {
    echo "============================================================================="
    echo "STOCK MANAGEMENT SYSTEM - STARTUP OPTIMIZATION"
    echo "============================================================================="
    echo "This script will optimize the startup process for better performance"
    echo "Log file: $LOG_FILE"
    echo "============================================================================="
    echo
    
    # Parse command line arguments
    SKIP_BUILD=false
    SKIP_WARMUP=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-warmup)
                SKIP_WARMUP=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-build    Skip building Docker images"
                echo "  --skip-warmup   Skip application warmup"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run optimization steps
    check_system_resources
    optimize_docker
    validate_environment
    prepare_volumes
    optimize_network
    
    if [ "$SKIP_BUILD" = false ]; then
        pre_pull_images
        optimize_app_images
    else
        log "Skipping image building as requested"
    fi
    
    if [ "$SKIP_WARMUP" = false ]; then
        warmup_application
        run_performance_check
    else
        log "Skipping application warmup as requested"
    fi
    
    echo
    echo "============================================================================="
    log_success "Startup optimization completed successfully!"
    echo "============================================================================="
    echo "Your Stock Management System is now optimized and ready for use."
    echo "Access the application at: http://localhost"
    echo "API health check: http://localhost/api/health"
    echo "============================================================================="
}

# Run main function
main "$@"