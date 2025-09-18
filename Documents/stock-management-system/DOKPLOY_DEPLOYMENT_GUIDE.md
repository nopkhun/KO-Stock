# Dokploy Deployment Guide - Stock Management System

This comprehensive guide provides step-by-step instructions for deploying the Stock Management System on Dokploy, including troubleshooting and operational procedures.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Pre-Deployment Preparation](#pre-deployment-preparation)
- [Dokploy Stack Creation](#dokploy-stack-creation)
- [Environment Variables Configuration](#environment-variables-configuration)
- [Volume and Storage Setup](#volume-and-storage-setup)
- [Network and Domain Configuration](#network-and-domain-configuration)
- [Deployment Process](#deployment-process)
- [Post-Deployment Verification](#post-deployment-verification)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Maintenance Procedures](#maintenance-procedures)

## Prerequisites

### Server Requirements
- **VPS Server**: Minimum 2GB RAM, 2 CPU cores, 20GB storage
- **Operating System**: Ubuntu 20.04+ or compatible Linux distribution
- **Dokploy**: Latest version installed and configured
- **Domain**: Registered domain pointing to your server (optional but recommended)

### Required Access
- **Dokploy Dashboard**: Admin access to your Dokploy instance
- **Server SSH**: Root or sudo access for troubleshooting
- **Domain DNS**: Access to configure DNS records (if using custom domain)

### Pre-Installation Checklist
- [ ] Dokploy is installed and accessible
- [ ] Server has sufficient resources
- [ ] Domain DNS is configured (if applicable)
- [ ] SSL certificate can be obtained (Let's Encrypt recommended)
- [ ] Backup strategy is planned

## Pre-Deployment Preparation

### Step 1: Generate Secure Credentials

Before starting the deployment, generate secure values for sensitive environment variables:

```bash
# Generate SECRET_KEY (32+ characters)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate database password (16+ characters)
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(16))"

# Alternative using OpenSSL
openssl rand -base64 32  # For SECRET_KEY
openssl rand -base64 16  # For POSTGRES_PASSWORD
```

**Save these values securely** - you'll need them for environment configuration.

### Step 2: Prepare Repository Access

Ensure your repository is accessible to Dokploy:

1. **Public Repository**: Use HTTPS URL directly
2. **Private Repository**: Configure SSH keys or access tokens in Dokploy
3. **Branch Selection**: Decide which branch to deploy (main/master recommended)

### Step 3: Plan Resource Allocation

Based on your VPS specifications, plan resource allocation:

#### Small VPS (2GB RAM, 2 CPU)
```
Backend: 512MB RAM, 1.0 CPU
Frontend: 256MB RAM, 0.5 CPU
Database: 256MB RAM, 0.5 CPU
Total: ~1GB RAM, 2.0 CPU
```

#### Medium VPS (4GB RAM, 4 CPU)
```
Backend: 1GB RAM, 2.0 CPU
Frontend: 512MB RAM, 1.0 CPU
Database: 512MB RAM, 1.0 CPU
Total: ~2GB RAM, 4.0 CPU
```

## Dokploy Stack Creation

### Step 1: Create New Project

1. **Access Dokploy Dashboard**
   - Navigate to your Dokploy instance URL
   - Log in with your admin credentials

2. **Create New Project**
   - Click "Create Project" or "New Project"
   - Enter project name: `stock-management-system`
   - Add description: `Production deployment of Stock Management System`

### Step 2: Configure Docker Compose Deployment

1. **Select Deployment Type**
   - Choose "Docker Compose" deployment option
   - This will use the existing `docker-compose.yml` file

2. **Repository Configuration**
   - **Repository URL**: Enter your repository URL
     ```
     https://github.com/yourusername/stock-management-system.git
     ```
   - **Branch**: Select deployment branch (usually `main` or `master`)
   - **Build Path**: Leave as root (`/`) unless project is in subdirectory

3. **Build Configuration**
   - **Docker Compose File**: `docker-compose.yml` (default)
   - **Build Context**: Root directory
   - **Auto Deploy**: Enable for automatic deployments on git push

### Step 3: Initial Stack Configuration

1. **Stack Settings**
   - **Stack Name**: `stock-management`
   - **Environment**: `production`
   - **Auto Restart**: Enable
   - **Health Checks**: Enable

2. **Resource Limits** (adjust based on your VPS)
   ```yaml
   # For medium VPS (4GB RAM)
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 1g
             cpus: '2.0'
     frontend:
       deploy:
         resources:
           limits:
             memory: 512m
             cpus: '1.0'
     database:
       deploy:
         resources:
           limits:
             memory: 512m
             cpus: '1.0'
   ```

## Environment Variables Configuration

### Step 1: Access Environment Variables

1. Navigate to your project in Dokploy
2. Go to "Environment Variables" or "Configuration" section
3. Choose "Add Environment Variable" for each required variable

### Step 2: Core Security Variables

**CRITICAL**: Set these variables first:

```bash
# Application Security (REQUIRED)
SECRET_KEY=your_generated_32_plus_character_secret_key
POSTGRES_PASSWORD=your_generated_secure_database_password

# Production Settings (REQUIRED)
FLASK_ENV=production
DEBUG=false

# Domain Configuration (REQUIRED for production)
CORS_ORIGINS=https://yourdomain.com
```

### Step 3: Database Configuration

Choose one of these approaches:

#### Option A: Single DATABASE_URL (Recommended)
```bash
DATABASE_URL=postgresql://postgres:your_generated_secure_database_password@database:5432/stock_management
```

#### Option B: Individual Database Settings
```bash
POSTGRES_DB=stock_management
POSTGRES_USER=postgres
POSTGRES_HOST=database
POSTGRES_PORT=5432
# POSTGRES_PASSWORD already set above
```

### Step 4: Session and Cookie Security

For HTTPS deployments (recommended):
```bash
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=None
PERMANENT_SESSION_LIFETIME=86400
```

For HTTP deployments (development only):
```bash
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

### Step 5: Performance and Monitoring

```bash
# Application Performance
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=30

# Database Performance
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30

# Logging and Monitoring
LOG_LEVEL=INFO
REQUEST_LOGGING=true
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_DATABASE=true
HEALTH_CHECK_DETAILED=true

# Frontend Configuration
VITE_API_BASE_URL=/api
```

### Step 6: Resource Limits (Optional)

```bash
# Container Resource Limits
MEMORY_LIMIT=1g
CPU_LIMIT=2.0
FRONTEND_MEMORY_LIMIT=512m
FRONTEND_CPU_LIMIT=1.0
DB_MEMORY_LIMIT=512m
DB_CPU_LIMIT=1.0
```

## Volume and Storage Setup

### Step 1: Create Persistent Volumes

In Dokploy dashboard, navigate to "Volumes" section:

1. **Database Volume**
   - **Name**: `postgres_data`
   - **Driver**: `local`
   - **Mount Point**: `/var/lib/postgresql/data`
   - **Backup**: Enable (critical data)

2. **Upload Volume** (if file uploads are used)
   - **Name**: `upload_data`
   - **Driver**: `local`
   - **Mount Point**: `/app/uploads`
   - **Backup**: Enable (user data)

### Step 2: Volume Configuration Verification

Ensure your `docker-compose.yml` references these volumes:

```yaml
volumes:
  postgres_data:
    external: true  # Managed by Dokploy
  upload_data:
    external: true  # Managed by Dokploy
```

### Step 3: Backup Configuration

1. **Enable Volume Backups** in Dokploy
2. **Set Backup Schedule**: Daily at 2 AM recommended
3. **Retention Policy**: 30 days minimum
4. **Backup Location**: Configure external storage if available

## Network and Domain Configuration

### Step 1: Internal Network Setup

The application uses Docker's internal networking:

```yaml
networks:
  stock_management_network:
    driver: bridge
```

Services communicate using service names:
- Database: `database:5432`
- Backend: `backend:5000`
- Frontend: `frontend:80`

### Step 2: External Access Configuration

1. **Port Exposure**
   - Only expose frontend port `80` externally
   - Backend and database remain internal

2. **Service Configuration**
   ```yaml
   frontend:
     ports:
       - "80:80"  # HTTP access
   ```

### Step 3: Domain and SSL Setup

#### Option A: Custom Domain with SSL (Recommended)

1. **Domain Configuration**
   - Navigate to "Domains" in Dokploy
   - Add your domain: `yourdomain.com`
   - Point to frontend service on port 80

2. **SSL Certificate**
   - Enable "Auto SSL" (Let's Encrypt)
   - Or upload custom SSL certificate
   - Force HTTPS redirect

3. **DNS Configuration**
   ```
   A Record: yourdomain.com → your_server_ip
   CNAME: www.yourdomain.com → yourdomain.com
   ```

#### Option B: IP Access (Development/Testing)

1. **Direct IP Access**
   - Access via `http://your_server_ip`
   - No SSL configuration needed
   - Update CORS_ORIGINS to include IP

2. **Environment Variables for IP Access**
   ```bash
   CORS_ORIGINS=http://your_server_ip
   SESSION_COOKIE_SECURE=false
   ```

## Deployment Process

### Step 1: Initial Deployment

1. **Review Configuration**
   - Verify all environment variables are set
   - Check volume configuration
   - Confirm resource limits

2. **Start Deployment**
   - Click "Deploy" in Dokploy dashboard
   - Monitor build logs in real-time
   - Wait for all services to become healthy

3. **Deployment Timeline**
   ```
   0-2 min:  Image building
   2-4 min:  Container startup
   4-6 min:  Database initialization
   6-8 min:  Health checks passing
   8-10 min: Application ready
   ```

### Step 2: Monitor Deployment Progress

1. **Build Logs**
   - Watch for build errors
   - Verify all dependencies install correctly
   - Check for security warnings

2. **Container Logs**
   - Monitor startup sequence
   - Check for environment variable validation
   - Verify database connections

3. **Health Check Status**
   - Database: Should be healthy first
   - Backend: Should connect to database
   - Frontend: Should proxy to backend

### Step 3: Handle Deployment Issues

If deployment fails:

1. **Check Build Logs** for errors
2. **Verify Environment Variables** are correct
3. **Review Resource Limits** if out of memory
4. **Check Volume Mounts** are configured
5. **Validate Network Configuration**

## Post-Deployment Verification

### Step 1: Service Health Verification

1. **Check Service Status**
   ```bash
   # In Dokploy dashboard, verify all services show "Healthy"
   # Green status indicators for all containers
   ```

2. **Health Endpoint Testing**
   ```bash
   # Test backend health (replace with your domain/IP)
   curl https://yourdomain.com/api/health
   
   # Expected response:
   {
     "status": "healthy",
     "timestamp": "2024-01-01T12:00:00Z",
     "database": "connected",
     "version": "1.0.0"
   }
   ```

3. **Database Connectivity**
   ```bash
   # Test detailed health check
   curl https://yourdomain.com/api/health/detailed
   
   # Should include system metrics and database status
   ```

### Step 2: Application Functionality Testing

1. **Frontend Access**
   - Navigate to your domain or IP
   - Verify login page loads correctly
   - Check for console errors in browser

2. **Authentication Testing**
   - Test login with default credentials
   - Verify session persistence
   - Check logout functionality

3. **API Functionality**
   - Test basic CRUD operations
   - Verify data persistence
   - Check error handling

### Step 3: Performance Verification

1. **Response Time Testing**
   ```bash
   # Test API response times
   curl -w "@curl-format.txt" -o /dev/null -s https://yourdomain.com/api/health
   ```

2. **Resource Usage Monitoring**
   - Check CPU and memory usage in Dokploy
   - Verify no resource limit warnings
   - Monitor for memory leaks

3. **Database Performance**
   - Check connection pool usage
   - Monitor query response times
   - Verify no connection errors

### Step 4: Security Verification

1. **HTTPS Configuration**
   ```bash
   # Test SSL certificate
   curl -I https://yourdomain.com
   
   # Check security headers
   curl -I https://yourdomain.com | grep -i security
   ```

2. **CORS Testing**
   ```bash
   # Test CORS from browser console
   fetch('https://yourdomain.com/api/health')
     .then(response => response.json())
     .then(data => console.log(data));
   ```

3. **Session Security**
   - Verify secure cookies in browser dev tools
   - Test session timeout
   - Check CSRF protection

## Troubleshooting Guide

### Common Deployment Issues

#### 1. Build Failures

**Symptoms**: Deployment fails during build phase

**Diagnostic Steps**:
```bash
# Check build logs in Dokploy dashboard
# Look for specific error messages
```

**Common Causes & Solutions**:

- **Missing Dependencies**
  ```bash
  # Solution: Update requirements.txt or package.json
  # Rebuild with --no-cache flag
  ```

- **Docker Build Context Issues**
  ```bash
  # Solution: Verify Dockerfile paths
  # Check .dockerignore file
  ```

- **Resource Limits During Build**
  ```bash
  # Solution: Temporarily increase build resources
  # Or use multi-stage builds more efficiently
  ```

#### 2. Environment Variable Errors

**Symptoms**: Application fails to start, validation errors

**Diagnostic Steps**:
```bash
# Check container logs for validation errors
# Verify environment variables in Dokploy dashboard
```

**Solutions**:
```bash
# Ensure all required variables are set:
SECRET_KEY=your_secret_key
POSTGRES_PASSWORD=your_db_password
CORS_ORIGINS=https://yourdomain.com

# Check for typos in variable names (case-sensitive)
# Verify no extra spaces or special characters
```

#### 3. Database Connection Issues

**Symptoms**: Backend can't connect to database, health checks fail

**Diagnostic Steps**:
```bash
# Check database container logs
# Test database connectivity manually
```

**Solutions**:
```bash
# Verify database service starts first
depends_on:
  database:
    condition: service_healthy

# Check password consistency
POSTGRES_PASSWORD=same_password_everywhere

# Verify host configuration
POSTGRES_HOST=database  # Use Docker service name
```

#### 4. CORS and Session Issues

**Symptoms**: Frontend can't access API, authentication fails

**Diagnostic Steps**:
```bash
# Check browser console for CORS errors
# Verify cookie settings in browser dev tools
```

**Solutions**:
```bash
# For HTTPS deployments:
CORS_ORIGINS=https://yourdomain.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=None

# For HTTP deployments (dev only):
CORS_ORIGINS=http://yourdomain.com
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
```

#### 5. Health Check Failures

**Symptoms**: Services marked unhealthy, frequent restarts

**Diagnostic Steps**:
```bash
# Test health endpoints manually
curl http://localhost:5000/api/health

# Check health check configuration
```

**Solutions**:
```bash
# Adjust health check timing
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_TIMEOUT=10s
HEALTH_CHECK_RETRIES=3
HEALTH_CHECK_START_PERIOD=60s

# Verify health check endpoints are accessible
# Check service dependencies
```

#### 6. SSL/HTTPS Issues

**Symptoms**: Mixed content errors, certificate warnings

**Diagnostic Steps**:
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443

# Check certificate validity
curl -I https://yourdomain.com
```

**Solutions**:
```bash
# Verify domain DNS points to server
# Check Let's Encrypt certificate generation
# Update CORS origins to use HTTPS
CORS_ORIGINS=https://yourdomain.com

# Force HTTPS redirect in Dokploy
# Update cookie settings for HTTPS
SESSION_COOKIE_SECURE=true
```

### Performance Issues

#### 1. High Memory Usage

**Symptoms**: Out of memory errors, container restarts

**Diagnostic Steps**:
```bash
# Check memory usage in Dokploy dashboard
# Monitor container stats
```

**Solutions**:
```bash
# Increase memory limits
MEMORY_LIMIT=1g
DB_MEMORY_LIMIT=512m

# Optimize database connections
DB_POOL_SIZE=20
GUNICORN_WORKERS=4

# Check for memory leaks in application logs
```

#### 2. Slow Response Times

**Symptoms**: API requests timeout, slow page loads

**Diagnostic Steps**:
```bash
# Test API response times
curl -w "%{time_total}" https://yourdomain.com/api/health

# Check database query performance
```

**Solutions**:
```bash
# Increase worker processes
GUNICORN_WORKERS=8
GUNICORN_TIMEOUT=60

# Optimize database settings
DB_POOL_SIZE=30
DB_POOL_TIMEOUT=60

# Enable compression
COMPRESS_RESPONSES=true
```

#### 3. Database Performance Issues

**Symptoms**: Slow queries, connection timeouts

**Diagnostic Steps**:
```bash
# Check database logs
# Monitor connection pool usage
```

**Solutions**:
```bash
# Increase connection pool
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50

# Optimize database configuration
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30

# Consider database indexing
# Monitor slow query logs
```

### Network and Connectivity Issues

#### 1. Service Discovery Problems

**Symptoms**: Services can't communicate internally

**Solutions**:
```bash
# Verify Docker network configuration
networks:
  stock_management_network:
    driver: bridge

# Use correct service names for internal communication
POSTGRES_HOST=database  # Not localhost or IP
```

#### 2. External Access Issues

**Symptoms**: Can't access application from internet

**Solutions**:
```bash
# Check port exposure
ports:
  - "80:80"  # Only for frontend

# Verify firewall settings
# Check Dokploy proxy configuration
```

### Recovery Procedures

#### 1. Service Recovery

**Steps**:
1. **Identify Failed Service**
   - Check Dokploy dashboard for unhealthy services
   - Review container logs for errors

2. **Restart Individual Service**
   ```bash
   # In Dokploy dashboard:
   # Navigate to service → Actions → Restart
   ```

3. **Full Stack Restart**
   ```bash
   # If multiple services are affected:
   # Project → Actions → Restart All Services
   ```

4. **Verify Recovery**
   - Check all services return to healthy status
   - Test application functionality
   - Monitor logs for recurring issues

#### 2. Data Recovery

**Database Recovery**:
1. **Check Volume Integrity**
   - Verify postgres_data volume is mounted
   - Check for filesystem errors

2. **Restore from Backup**
   ```bash
   # If data is corrupted:
   # Stop database service
   # Restore volume from backup
   # Restart services
   ```

3. **Manual Database Recovery**
   ```bash
   # Access database container
   docker exec -it container_name psql -U postgres

   # Check database integrity
   \l  # List databases
   \dt # List tables
   ```

#### 3. Complete Redeployment

**When to Use**: Major configuration changes, persistent issues

**Steps**:
1. **Backup Current State**
   - Export environment variables
   - Backup persistent volumes
   - Document current configuration

2. **Clean Deployment**
   ```bash
   # In Dokploy:
   # Delete current deployment
   # Remove containers and images
   # Keep persistent volumes
   ```

3. **Redeploy from Scratch**
   - Create new deployment
   - Restore environment variables
   - Mount existing volumes
   - Verify functionality

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Monitoring (Automated)

1. **Health Check Monitoring**
   - Verify all services are healthy
   - Check response times
   - Monitor error rates

2. **Resource Usage Monitoring**
   - CPU and memory usage
   - Disk space utilization
   - Network traffic patterns

3. **Log Review**
   - Check for error patterns
   - Monitor security events
   - Review performance metrics

#### Weekly Maintenance

1. **Log Analysis**
   ```bash
   # Review application logs for patterns
   # Check for recurring errors
   # Monitor user activity trends
   ```

2. **Performance Review**
   - Analyze response time trends
   - Review resource usage patterns
   - Check database performance metrics

3. **Security Review**
   - Review access logs
   - Check for failed login attempts
   - Monitor for suspicious activity

#### Monthly Maintenance

1. **System Updates**
   ```bash
   # Update base Docker images
   # Update application dependencies
   # Apply security patches
   ```

2. **Backup Verification**
   - Test backup restoration process
   - Verify backup integrity
   - Update backup retention policies

3. **Configuration Review**
   - Review environment variables
   - Update resource limits if needed
   - Optimize performance settings

#### Quarterly Maintenance

1. **Security Audit**
   - Review and rotate secrets
   - Update SSL certificates
   - Audit user access permissions

2. **Performance Optimization**
   - Analyze long-term performance trends
   - Optimize database queries
   - Review and adjust resource allocation

3. **Disaster Recovery Testing**
   - Test complete system recovery
   - Verify backup and restore procedures
   - Update disaster recovery documentation

### Backup and Recovery Procedures

#### Automated Backup Setup

1. **Database Backup Configuration**
   ```bash
   # In Dokploy, configure automated backups:
   # Schedule: Daily at 2 AM
   # Retention: 30 days
   # Compression: Enabled
   ```

2. **Volume Backup**
   ```bash
   # Backup persistent volumes:
   # postgres_data: Critical (daily)
   # upload_data: Important (weekly)
   ```

3. **Configuration Backup**
   ```bash
   # Export environment variables monthly
   # Backup docker-compose.yml
   # Document configuration changes
   ```

#### Manual Backup Procedures

1. **Database Backup**
   ```bash
   # Create manual database backup
   docker exec postgres_container pg_dump -U postgres stock_management > backup_$(date +%Y%m%d).sql
   
   # Compressed backup
   docker exec postgres_container pg_dump -U postgres stock_management | gzip > backup_$(date +%Y%m%d).sql.gz
   ```

2. **Volume Backup**
   ```bash
   # Backup volume data
   docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz -C /data .
   ```

3. **Configuration Backup**
   ```bash
   # Export environment variables
   # Save from Dokploy dashboard or via API
   
   # Backup compose file
   cp docker-compose.yml docker-compose.backup.yml
   ```

#### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Stop application services
   docker-compose stop backend frontend
   
   # Restore database
   docker exec -i postgres_container psql -U postgres stock_management < backup_file.sql
   
   # Restart services
   docker-compose start backend frontend
   ```

2. **Volume Recovery**
   ```bash
   # Stop services using the volume
   docker-compose stop
   
   # Restore volume data
   docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data_backup.tar.gz -C /data
   
   # Restart services
   docker-compose up -d
   ```

3. **Complete System Recovery**
   ```bash
   # Restore from complete backup:
   # 1. Restore volume data
   # 2. Restore configuration
   # 3. Redeploy application
   # 4. Verify functionality
   ```

### Performance Tuning Guidelines

#### Resource Optimization

1. **CPU Allocation**
   ```bash
   # Monitor CPU usage patterns
   # Adjust based on actual usage:
   
   # Light usage (< 50% average)
   CPU_LIMIT=1.0
   GUNICORN_WORKERS=2
   
   # Medium usage (50-80% average)
   CPU_LIMIT=2.0
   GUNICORN_WORKERS=4
   
   # High usage (> 80% average)
   CPU_LIMIT=4.0
   GUNICORN_WORKERS=8
   ```

2. **Memory Optimization**
   ```bash
   # Monitor memory usage and adjust:
   
   # Small deployment
   MEMORY_LIMIT=512m
   DB_POOL_SIZE=10
   
   # Medium deployment
   MEMORY_LIMIT=1g
   DB_POOL_SIZE=20
   
   # Large deployment
   MEMORY_LIMIT=2g
   DB_POOL_SIZE=30
   ```

3. **Database Tuning**
   ```bash
   # Connection pool optimization
   DB_POOL_SIZE=20              # 2-4 per CPU core
   DB_MAX_OVERFLOW=30           # 1.5x pool size
   DB_POOL_TIMEOUT=30           # Connection timeout
   DB_POOL_RECYCLE=3600         # 1 hour recycle
   
   # Query optimization
   # Monitor slow queries
   # Add database indexes as needed
   ```

#### Application Performance

1. **Gunicorn Optimization**
   ```bash
   # Worker configuration
   GUNICORN_WORKERS=4           # (2 * CPU cores) + 1
   GUNICORN_WORKER_CLASS=sync   # or gevent for async
   GUNICORN_TIMEOUT=30          # Request timeout
   GUNICORN_KEEPALIVE=2         # Keep-alive timeout
   ```

2. **Caching Configuration**
   ```bash
   # Enable response caching
   CACHE_TYPE=simple
   CACHE_DEFAULT_TIMEOUT=300
   
   # Static file caching
   STATIC_FILE_CACHE=true
   CACHE_CONTROL_MAX_AGE=86400
   ```

3. **Compression Settings**
   ```bash
   # Enable compression
   COMPRESS_RESPONSES=true
   COMPRESS_LEVEL=6
   COMPRESS_MIN_SIZE=1024
   ```

This completes the comprehensive Dokploy deployment guide. The guide provides step-by-step instructions for deploying the Stock Management System on Dokploy, including detailed troubleshooting procedures and maintenance guidelines.