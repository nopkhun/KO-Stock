# Backend Health Check Troubleshooting Guide

## Current Issue
```
dependency failed to start: container kostock-kostock-shg4ih-backend-1 is unhealthy
```

## Root Causes & Solutions

### 1. Backend Startup Issues

**Possible Causes:**
- Environment variables not set correctly
- Database connection failing
- Application startup errors
- Health check endpoint not responding

**Debugging Steps:**

#### Check Container Logs
```bash
# In Dokploy or Docker
docker logs kostock-kostock-shg4ih-backend-1

# Look for:
# - Environment validation errors
# - Database connection errors
# - Flask startup errors
# - Import errors
```

#### Test Health Endpoints Manually
```bash
# Test simple ping (no dependencies)
curl http://localhost:5000/api/ping

# Test simple health (minimal dependencies)
curl http://localhost:5000/api/health/simple

# Test liveness check
curl http://localhost:5000/api/health/live

# Test full health check (includes database)
curl http://localhost:5000/api/health
```

### 2. Environment Variable Issues

**Required Variables:**
```bash
# Critical for startup
SECRET_KEY=your-32-character-secret-key
POSTGRES_PASSWORD=your-database-password

# Database connection
DATABASE_URL=postgresql://postgres:password@database:5432/stock_management

# Or individual settings
POSTGRES_DB=stock_management
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
```

**Check in Dokploy:**
1. Go to Environment Variables section
2. Verify all required variables are set
3. Ensure no typos in variable names
4. Check for special characters that might need escaping

### 3. Database Connection Issues

**Common Problems:**
- Database container not ready when backend starts
- Wrong database credentials
- Network connectivity between containers
- Database initialization taking too long

**Solutions:**
```yaml
# Use longer start period in health check
healthcheck:
  start_period: 120s  # Wait 2 minutes before checking
  interval: 30s
  timeout: 15s
  retries: 5
```

### 4. Health Check Timeout Issues

**Current Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:5000/api/health || exit 1
```

**Extended Health Check (for debugging):**
```yaml
healthcheck:
  test: |
    curl -f http://localhost:5000/api/ping || 
    curl -f http://localhost:5000/api/health/simple || 
    exit 1
  interval: 15s
  timeout: 30s
  retries: 10
  start_period: 120s
```

## Quick Fixes

### Fix 1: Use Debug Compose File
```bash
# Use the debug version with extended timeouts
cp docker-compose.debug.yml docker-compose.yml
```

### Fix 2: Test with Simple Health Check
Update your compose file to use the simple health endpoint:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/api/ping"]
```

### Fix 3: Increase Timeouts
```yaml
healthcheck:
  start_period: 180s  # 3 minutes
  timeout: 30s
  retries: 10
```

## Environment Variables for Debugging

Add these to your Dokploy environment:
```bash
# Enable debug logging
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1

# Flask debugging (only for troubleshooting)
FLASK_DEBUG=0  # Keep as 0 for production

# Database debugging
DB_ECHO_POOL=true
```

## Step-by-Step Debugging Process

### Step 1: Check Basic Connectivity
```bash
# Test if container is running
docker ps | grep backend

# Test if port is accessible
curl http://localhost:5000/api/ping
```

### Step 2: Check Application Logs
```bash
# View recent logs
docker logs --tail 50 kostock-kostock-shg4ih-backend-1

# Follow logs in real-time
docker logs -f kostock-kostock-shg4ih-backend-1
```

### Step 3: Test Health Endpoints
```bash
# Test in order of complexity
curl http://localhost:5000/api/ping                # Simplest
curl http://localhost:5000/api/health/simple       # No DB
curl http://localhost:5000/api/health/live         # Basic checks
curl http://localhost:5000/api/health              # Full check
```

### Step 4: Check Database Connection
```bash
# Test database connectivity from backend container
docker exec -it kostock-kostock-shg4ih-backend-1 bash
curl http://database:5432  # Should get connection refused (normal)
```

## Common Error Messages & Solutions

### "Environment validation failed"
- Check all required environment variables are set
- Verify SECRET_KEY is at least 32 characters
- Ensure POSTGRES_PASSWORD is set

### "Database connection failed"
- Verify database container is healthy
- Check DATABASE_URL format
- Ensure database credentials match

### "curl: command not found"
- Backend Dockerfile includes curl installation
- If missing, health check will fail

### "Connection refused"
- Backend application not starting
- Check for Python import errors
- Verify Flask app is binding to 0.0.0.0:5000

## Files Available for Testing

1. **docker-compose.debug.yml** - Extended timeouts and logging
2. **docker-compose.minimal.yml** - Minimal configuration
3. **Health endpoints added:**
   - `/api/ping` - Ultra-simple test
   - `/api/health/simple` - No database dependencies
   - `/api/health/live` - Basic liveness check
   - `/api/health` - Full health check

## Next Steps if Still Failing

1. **Use debug compose file** with extended timeouts
2. **Check Dokploy logs** for container orchestration issues
3. **Test locally** with Docker Compose to isolate Dokploy issues
4. **Contact support** with specific error messages and logs