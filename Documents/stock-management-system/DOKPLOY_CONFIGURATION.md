# Dokploy Configuration Guide

This guide provides step-by-step instructions for configuring the Stock Management System for deployment on Dokploy, including environment variables, networking, and volume management.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables Setup](#environment-variables-setup)
- [Docker Compose Configuration](#docker-compose-configuration)
- [Volume Configuration](#volume-configuration)
- [Network Configuration](#network-configuration)
- [Health Check Configuration](#health-check-configuration)
- [Security Configuration](#security-configuration)
- [Performance Optimization](#performance-optimization)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying to Dokploy, ensure you have:

1. **Dokploy installed** on your VPS server
2. **Domain name** configured and pointing to your server
3. **SSL certificate** set up (recommended: Let's Encrypt via Dokploy)
4. **Sufficient resources** on your VPS (minimum: 2GB RAM, 2 CPU cores)
5. **Docker and Docker Compose** installed (handled by Dokploy)

## Environment Variables Setup

### Step 1: Generate Secure Values

Before configuring Dokploy, generate secure values for sensitive variables:

```bash
# Generate SECRET_KEY (32+ characters)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate database password (12+ characters)
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(16))"

# Or use openssl if Python is not available
openssl rand -base64 32
```

### Step 2: Required Environment Variables

Set these variables in Dokploy's environment variables interface:

#### Core Security Variables
```bash
# REQUIRED: Generate unique values for your deployment
SECRET_KEY=your_generated_32_plus_character_secret_key
POSTGRES_PASSWORD=your_generated_secure_database_password

# REQUIRED: Set to your actual domain
CORS_ORIGINS=https://yourdomain.com

# REQUIRED: Production security settings
SESSION_COOKIE_SECURE=true
DEBUG=false
FLASK_ENV=production
```

#### Database Configuration
```bash
# Use DATABASE_URL for simplicity (recommended)
DATABASE_URL=postgresql://postgres:your_generated_secure_database_password@database:5432/stock_management

# OR use individual settings
POSTGRES_DB=stock_management
POSTGRES_USER=postgres
POSTGRES_HOST=database
POSTGRES_PORT=5432
```

#### Application Settings
```bash
# Application metadata
APP_NAME=Stock Management System
APP_VERSION=1.0.0
APP_ENVIRONMENT=production

# Server configuration
HOST=0.0.0.0
PORT=5000

# Frontend configuration
VITE_API_BASE_URL=/api
```

### Step 3: Optional Performance Variables

For better performance, add these variables:

```bash
# Gunicorn workers (adjust based on CPU cores)
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=30

# Database connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
REQUEST_LOGGING=true

# Health checks
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_DATABASE=true
HEALTH_CHECK_DETAILED=true
```

### Step 4: Resource Limits

Configure resource limits based on your VPS specifications:

```bash
# For 2GB RAM VPS
MEMORY_LIMIT=512m
CPU_LIMIT=1.0

# For 4GB RAM VPS
MEMORY_LIMIT=1g
CPU_LIMIT=2.0

# For 8GB RAM VPS
MEMORY_LIMIT=2g
CPU_LIMIT=4.0
```

## Docker Compose Configuration

### Dokploy-Optimized docker-compose.yml

Ensure your `docker-compose.yml` is optimized for Dokploy:

```yaml
version: '3.8'

services:
  database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-stock_management}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - stock_management_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-stock_management}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: ${DB_MEMORY_LIMIT:-256m}
          cpus: '${DB_CPU_LIMIT:-0.5}'

  backend:
    build:
      context: ./stock-management-backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=${FLASK_ENV:-production}
      - DEBUG=${DEBUG:-false}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - SESSION_COOKIE_SECURE=${SESSION_COOKIE_SECURE:-true}
      - SESSION_COOKIE_SAMESITE=${SESSION_COOKIE_SAMESITE:-None}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
      - HEALTH_CHECK_ENABLED=${HEALTH_CHECK_ENABLED:-true}
    volumes:
      - upload_data:/app/uploads
    networks:
      - stock_management_network
    depends_on:
      database:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: ${MEMORY_LIMIT:-512m}
          cpus: '${CPU_LIMIT:-1.0}'

  frontend:
    build:
      context: ./stock-management-frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE_URL=${VITE_API_BASE_URL:-/api}
    ports:
      - "80:80"
    networks:
      - stock_management_network
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: ${FRONTEND_MEMORY_LIMIT:-256m}
          cpus: '${FRONTEND_CPU_LIMIT:-0.5}'

volumes:
  postgres_data:
    driver: local
  upload_data:
    driver: local

networks:
  stock_management_network:
    driver: bridge
```

## Volume Configuration

### Persistent Data Volumes

Configure persistent volumes in Dokploy for data that must survive container restarts:

#### Database Volume
- **Volume Name**: `postgres_data`
- **Mount Path**: `/var/lib/postgresql/data`
- **Purpose**: PostgreSQL database files
- **Backup**: Critical - contains all application data

#### Upload Volume (Optional)
- **Volume Name**: `upload_data`
- **Mount Path**: `/app/uploads`
- **Purpose**: User-uploaded files
- **Backup**: Important if file upload feature is used

### Volume Management in Dokploy

1. **Navigate to Volumes** in Dokploy dashboard
2. **Create volumes** before first deployment:
   ```bash
   # Volume names should match docker-compose.yml
   postgres_data
   upload_data
   ```
3. **Set backup policies** for critical volumes
4. **Monitor volume usage** regularly

## Network Configuration

### Internal Service Communication

Services communicate via Docker's internal network:

```yaml
# Network configuration in docker-compose.yml
networks:
  stock_management_network:
    driver: bridge
```

### Service Discovery

Services use Docker Compose service names for internal communication:

- **Database**: `database:5432`
- **Backend**: `backend:5000`
- **Frontend**: `frontend:80`

### External Access

Only the frontend service should be exposed externally:

```yaml
# Only frontend exposes ports
ports:
  - "80:80"  # HTTP traffic
```

### Dokploy Proxy Configuration

Configure Dokploy's reverse proxy:

1. **Domain**: Set your domain name
2. **SSL**: Enable Let's Encrypt SSL
3. **Port**: 80 (frontend service)
4. **Path**: / (root path)

## Health Check Configuration

### Backend Health Checks

The backend provides comprehensive health check endpoints:

```bash
# Basic health check
GET /api/health

# Detailed health check with system metrics
GET /api/health/detailed

# Readiness probe (checks database connectivity)
GET /api/health/ready

# Liveness probe (basic service status)
GET /api/health/live
```

### Docker Health Check Configuration

```yaml
# Backend health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s

# Database health check
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d stock_management"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s

# Frontend health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:80/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### Dokploy Health Check Settings

Configure in Dokploy dashboard:

- **Health Check Path**: `/api/health`
- **Health Check Port**: 80 (via frontend proxy)
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 60 seconds

## Security Configuration

### HTTPS and SSL

1. **Enable SSL** in Dokploy dashboard
2. **Use Let's Encrypt** for automatic certificate management
3. **Force HTTPS** redirect
4. **Set security headers** in environment variables:

```bash
# Security headers
FORCE_HTTPS=true
HSTS_MAX_AGE=31536000
HSTS_INCLUDE_SUBDOMAINS=true
X_CONTENT_TYPE_OPTIONS=nosniff
X_FRAME_OPTIONS=DENY
X_XSS_PROTECTION=1; mode=block
```

### CORS Configuration

Configure CORS for your domain:

```bash
# Single domain
CORS_ORIGINS=https://yourdomain.com

# Multiple domains
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Subdomain support
CORS_ORIGINS=https://yourdomain.com,https://*.yourdomain.com
```

### Session Security

Configure secure session settings:

```bash
# HTTPS-only cookies
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true

# Cross-origin support
SESSION_COOKIE_SAMESITE=None

# Session timeout (24 hours)
PERMANENT_SESSION_LIFETIME=86400
```

### Container Security

Ensure containers run securely:

```dockerfile
# In Dockerfiles, create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

USER appuser
```

## Performance Optimization

### Resource Allocation

Optimize resource allocation based on VPS specifications:

#### Small VPS (2GB RAM, 2 CPU)
```bash
# Total: ~1.5GB allocated
MEMORY_LIMIT=512m          # Backend
FRONTEND_MEMORY_LIMIT=256m # Frontend
DB_MEMORY_LIMIT=256m       # Database
CPU_LIMIT=1.0              # Backend
FRONTEND_CPU_LIMIT=0.5     # Frontend
DB_CPU_LIMIT=0.5           # Database
```

#### Medium VPS (4GB RAM, 4 CPU)
```bash
# Total: ~3GB allocated
MEMORY_LIMIT=1g            # Backend
FRONTEND_MEMORY_LIMIT=512m # Frontend
DB_MEMORY_LIMIT=512m       # Database
CPU_LIMIT=2.0              # Backend
FRONTEND_CPU_LIMIT=1.0     # Frontend
DB_CPU_LIMIT=1.0           # Database
```

#### Large VPS (8GB RAM, 8 CPU)
```bash
# Total: ~6GB allocated
MEMORY_LIMIT=2g            # Backend
FRONTEND_MEMORY_LIMIT=1g   # Frontend
DB_MEMORY_LIMIT=1g         # Database
CPU_LIMIT=4.0              # Backend
FRONTEND_CPU_LIMIT=2.0     # Frontend
DB_CPU_LIMIT=2.0           # Database
```

### Application Performance

```bash
# Gunicorn workers (2 * CPU cores + 1)
GUNICORN_WORKERS=4         # For 2 CPU
GUNICORN_WORKERS=8         # For 4 CPU

# Database connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Caching and compression
CACHE_TYPE=simple
COMPRESS_MIMETYPES=text/html,text/css,text/xml,application/json,application/javascript
```

## Monitoring Setup

### Application Monitoring

Enable comprehensive monitoring:

```bash
# Logging configuration
LOG_LEVEL=INFO
REQUEST_LOGGING=true
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s

# Health check monitoring
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_DATABASE=true
HEALTH_CHECK_DETAILED=true

# Performance monitoring
MONITOR_PERFORMANCE=true
COLLECT_METRICS=true
```

### Dokploy Monitoring

Use Dokploy's built-in monitoring features:

1. **Container Logs**: View real-time logs for each service
2. **Resource Usage**: Monitor CPU, memory, and disk usage
3. **Health Status**: Track service health and uptime
4. **Alerts**: Set up alerts for service failures

### External Monitoring (Optional)

For production environments, consider external monitoring:

- **Uptime monitoring**: Pingdom, UptimeRobot
- **Application monitoring**: New Relic, DataDog
- **Log aggregation**: ELK Stack, Splunk
- **Error tracking**: Sentry, Rollbar

## Troubleshooting

### Common Deployment Issues

#### 1. Environment Variable Errors

**Symptoms**: Application fails to start, validation errors in logs

**Solutions**:
```bash
# Check required variables are set
SECRET_KEY=your_secret_key
POSTGRES_PASSWORD=your_db_password
CORS_ORIGINS=https://yourdomain.com

# Verify variable names (case-sensitive)
# Check for extra spaces or special characters
```

#### 2. Database Connection Issues

**Symptoms**: Backend can't connect to database

**Solutions**:
```bash
# Ensure database service starts first
depends_on:
  database:
    condition: service_healthy

# Check database credentials match
POSTGRES_PASSWORD=same_password_in_all_services

# Verify host is set correctly
POSTGRES_HOST=database  # Docker Compose service name
```

#### 3. CORS Errors

**Symptoms**: Frontend can't access backend API

**Solutions**:
```bash
# Set correct domain in CORS_ORIGINS
CORS_ORIGINS=https://yourdomain.com

# Enable credentials for session-based auth
CORS_ALLOW_CREDENTIALS=true

# Check cookie settings for HTTPS
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=None
```

#### 4. Health Check Failures

**Symptoms**: Services marked as unhealthy in Dokploy

**Solutions**:
```bash
# Check health check endpoints are accessible
curl http://localhost:5000/api/health

# Verify health check configuration
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_DATABASE=true

# Check service dependencies
# Ensure database is healthy before backend starts
```

#### 5. SSL/HTTPS Issues

**Symptoms**: Mixed content errors, insecure connections

**Solutions**:
```bash
# Enable HTTPS in Dokploy
# Set secure cookie settings
SESSION_COOKIE_SECURE=true
FORCE_HTTPS=true

# Update CORS origins to use HTTPS
CORS_ORIGINS=https://yourdomain.com
```

### Debug Mode

To enable debug logging temporarily:

```bash
# Set in Dokploy environment variables
LOG_LEVEL=DEBUG

# Keep DEBUG=false for security
DEBUG=false

# Enable detailed health checks
HEALTH_CHECK_DETAILED=true
```

### Log Analysis

Check logs in Dokploy dashboard:

1. **Container Logs**: Real-time application logs
2. **System Logs**: Docker and system-level logs
3. **Access Logs**: HTTP request logs
4. **Error Logs**: Application error logs

### Performance Issues

If experiencing performance problems:

```bash
# Increase resource limits
MEMORY_LIMIT=1g
CPU_LIMIT=2.0

# Optimize database connections
DB_POOL_SIZE=30
GUNICORN_WORKERS=8

# Enable caching
CACHE_TYPE=simple
COMPRESS_RESPONSES=true
```

### Recovery Procedures

#### Service Recovery
1. **Check logs** for error messages
2. **Restart services** via Dokploy dashboard
3. **Verify environment variables** are correct
4. **Check resource usage** and limits
5. **Validate health checks** are passing

#### Data Recovery
1. **Check volume mounts** are correct
2. **Verify backup procedures** are working
3. **Test database connectivity** manually
4. **Restore from backup** if necessary

#### Complete Redeployment
1. **Export environment variables** from Dokploy
2. **Backup persistent volumes**
3. **Redeploy stack** with updated configuration
4. **Verify all services** are healthy
5. **Test application functionality**

## Best Practices

### Security
- Use strong, unique passwords for all services
- Enable HTTPS and secure cookies
- Regularly update Docker images
- Monitor logs for security events
- Use specific CORS origins, never '*'

### Performance
- Allocate resources based on actual usage
- Monitor and adjust connection pool settings
- Use appropriate health check intervals
- Enable compression and caching
- Optimize Docker image sizes

### Reliability
- Set up proper health checks
- Use restart policies
- Configure persistent volumes
- Implement backup procedures
- Monitor service dependencies

### Maintenance
- Regularly update dependencies
- Monitor resource usage
- Review and rotate secrets
- Test backup and recovery procedures
- Keep documentation updated