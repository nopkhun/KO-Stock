# Troubleshooting Guide - Stock Management System Deployment

This guide provides solutions for common issues encountered when deploying the Stock Management System to Dokploy.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Environment Variable Issues](#environment-variable-issues)
- [Database Connection Problems](#database-connection-problems)
- [Frontend Access Issues](#frontend-access-issues)
- [API Connectivity Problems](#api-connectivity-problems)
- [CORS and Authentication Issues](#cors-and-authentication-issues)
- [Docker and Container Issues](#docker-and-container-issues)
- [Performance Problems](#performance-problems)
- [SSL/HTTPS Issues](#sslhttps-issues)
- [Health Check Failures](#health-check-failures)
- [Resource and Memory Issues](#resource-and-memory-issues)
- [Logging and Monitoring](#logging-and-monitoring)
- [Recovery Procedures](#recovery-procedures)

## Quick Diagnostics

### Run Validation Scripts

Before troubleshooting, run the validation and verification scripts:

```bash
# Pre-deployment validation
python scripts/validate-deployment.py --env-file .env.production --strict

# Post-deployment verification
python scripts/verify-deployment.py --base-url https://yourdomain.com --verbose
```

### Check Service Status in Dokploy

1. **Navigate to your application** in Dokploy dashboard
2. **Check service status** - all services should show "Running"
3. **Review logs** for each service (database, backend, frontend)
4. **Check resource usage** - CPU and memory utilization

### Quick Health Check Commands

```bash
# Check if services are responding
curl -f https://yourdomain.com/
curl -f https://yourdomain.com/api/health

# Check Docker containers (if you have SSH access)
docker ps
docker logs <container_name>
```

## Environment Variable Issues

### Problem: Application Won't Start - Missing Environment Variables

**Symptoms:**
- Backend container exits immediately
- Error logs show "Missing required environment variable"
- Validation script reports missing variables

**Solution:**
1. **Check required variables are set in Dokploy:**
   ```bash
   SECRET_KEY=your_32_plus_character_secret_key
   POSTGRES_PASSWORD=your_secure_database_password
   CORS_ORIGINS=https://yourdomain.com
   ```

2. **Verify variable names are exact** (case-sensitive):
   - `SECRET_KEY` not `secret_key`
   - `POSTGRES_PASSWORD` not `postgres_password`

3. **Check for extra spaces** in variable values
4. **Ensure no quotes** around values in Dokploy interface

### Problem: Weak Security Configuration

**Symptoms:**
- Validation script reports security warnings
- Application works but security headers missing

**Solution:**
1. **Set production security variables:**
   ```bash
   DEBUG=false
   FLASK_ENV=production
   SESSION_COOKIE_SECURE=true
   ```

2. **Generate strong SECRET_KEY:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Use strong database password:**
   ```bash
   # At least 12 characters with mixed case, numbers, symbols
   POSTGRES_PASSWORD=MySecureDbPass123!
   ```

### Problem: Environment Variables Not Taking Effect

**Symptoms:**
- Variables set in Dokploy but application uses defaults
- Changes to environment variables don't apply

**Solution:**
1. **Restart all services** in Dokploy after changing variables
2. **Check variable precedence** - ensure no conflicting values in code
3. **Verify Dokploy environment injection** is working:
   ```bash
   # Check container environment (if SSH access available)
   docker exec <container_name> env | grep SECRET_KEY
   ```

## Database Connection Problems

### Problem: Backend Can't Connect to Database

**Symptoms:**
- Backend health checks fail
- Error logs show "connection refused" or "database not found"
- API returns 500 errors

**Solution:**
1. **Check database service is running** in Dokploy dashboard
2. **Verify database connection settings:**
   ```bash
   # For DATABASE_URL approach
   DATABASE_URL=postgresql://postgres:your_password@database:5432/stock_management
   
   # For individual settings
   POSTGRES_HOST=database  # Must be 'database' for Docker Compose
   POSTGRES_PORT=5432
   POSTGRES_DB=stock_management
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   ```

3. **Check database logs** for connection attempts and errors
4. **Verify network connectivity** between services

### Problem: Database Connection Timeout

**Symptoms:**
- Intermittent database connection failures
- Slow API responses
- Connection pool exhaustion errors

**Solution:**
1. **Increase connection timeout:**
   ```bash
   DB_POOL_TIMEOUT=60
   DB_POOL_RECYCLE=3600
   ```

2. **Optimize connection pool:**
   ```bash
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=30
   ```

3. **Check database resource limits** in Dokploy
4. **Monitor database performance** and query execution times

### Problem: Database Data Not Persisting

**Symptoms:**
- Data disappears after container restart
- Database appears empty after deployment

**Solution:**
1. **Verify persistent volume is configured** in Dokploy:
   - Volume name: `postgres_data`
   - Mount path: `/var/lib/postgresql/data`

2. **Check volume mounting** in docker-compose.yml:
   ```yaml
   volumes:
     - postgres_data:/var/lib/postgresql/data
   ```

3. **Ensure volume exists** before first deployment
4. **Check volume permissions** and ownership

## Frontend Access Issues

### Problem: Frontend Not Loading

**Symptoms:**
- Browser shows "This site can't be reached"
- 502 Bad Gateway errors
- Blank page or loading indefinitely

**Solution:**
1. **Check frontend container status** in Dokploy
2. **Verify port mapping** in docker-compose.yml:
   ```yaml
   ports:
     - "80:80"
   ```

3. **Check Nginx configuration** in frontend container
4. **Verify domain DNS** points to your server
5. **Check Dokploy proxy configuration**

### Problem: Frontend Loads But Can't Reach API

**Symptoms:**
- Frontend loads but shows API connection errors
- Network tab shows failed API requests
- CORS errors in browser console

**Solution:**
1. **Check API base URL configuration:**
   ```bash
   VITE_API_BASE_URL=/api
   ```

2. **Verify Nginx proxy configuration** routes `/api` to backend
3. **Check backend service is running** and healthy
4. **Test API directly:**
   ```bash
   curl https://yourdomain.com/api/health
   ```

## API Connectivity Problems

### Problem: API Returns 500 Internal Server Error

**Symptoms:**
- All API endpoints return 500 errors
- Backend logs show application errors

**Solution:**
1. **Check backend logs** for specific error messages
2. **Verify database connectivity** from backend
3. **Check environment variables** are set correctly
4. **Ensure all required dependencies** are installed
5. **Test database connection manually:**
   ```bash
   # Inside backend container
   python -c "from src.config.database import db; print(db.engine.execute('SELECT 1').scalar())"
   ```

### Problem: API Returns 404 Not Found

**Symptoms:**
- Specific API endpoints return 404
- Some endpoints work, others don't

**Solution:**
1. **Check API route registration** in backend code
2. **Verify URL paths** match frontend requests
3. **Check Nginx proxy configuration** for API routing
4. **Test API endpoints directly:**
   ```bash
   curl -v https://yourdomain.com/api/health
   curl -v https://yourdomain.com/api/locations
   ```

### Problem: API Slow Response Times

**Symptoms:**
- API requests take >5 seconds
- Timeout errors in frontend
- Poor user experience

**Solution:**
1. **Increase Gunicorn workers:**
   ```bash
   GUNICORN_WORKERS=8  # Adjust based on CPU cores
   ```

2. **Optimize database queries** and add indexes
3. **Increase resource limits:**
   ```bash
   MEMORY_LIMIT=1g
   CPU_LIMIT=2.0
   ```

4. **Enable response compression:**
   ```bash
   COMPRESS_RESPONSES=true
   ```

## CORS and Authentication Issues

### Problem: CORS Errors in Browser

**Symptoms:**
- Browser console shows CORS policy errors
- API requests blocked by CORS policy
- "Access-Control-Allow-Origin" errors

**Solution:**
1. **Set correct CORS origins:**
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

2. **For multiple domains:**
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```

3. **Enable credentials for session-based auth:**
   ```bash
   CORS_ALLOW_CREDENTIALS=true
   ```

4. **Check cookie settings for cross-origin:**
   ```bash
   SESSION_COOKIE_SAMESITE=None
   SESSION_COOKIE_SECURE=true
   ```

### Problem: Session/Authentication Not Working

**Symptoms:**
- Users can't log in
- Sessions don't persist
- Authentication state lost on page refresh

**Solution:**
1. **Check session cookie settings:**
   ```bash
   SESSION_COOKIE_SECURE=true  # For HTTPS
   SESSION_COOKIE_HTTPONLY=true
   SESSION_COOKIE_SAMESITE=None  # For cross-origin
   ```

2. **Verify SECRET_KEY is consistent** across restarts
3. **Check session timeout settings:**
   ```bash
   PERMANENT_SESSION_LIFETIME=86400  # 24 hours
   ```

4. **Test cookie creation and reading** in browser dev tools

## Docker and Container Issues

### Problem: Container Keeps Restarting

**Symptoms:**
- Container status shows "Restarting" in Dokploy
- Service never becomes healthy
- Restart loop in logs

**Solution:**
1. **Check container logs** for crash reasons
2. **Verify health check configuration:**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 60s
   ```

3. **Check resource limits** aren't too restrictive
4. **Verify all dependencies** are available
5. **Test container locally** before deploying

### Problem: Docker Build Failures

**Symptoms:**
- Deployment fails during build phase
- "No such file or directory" errors
- Dependency installation failures

**Solution:**
1. **Check Dockerfile syntax** and paths
2. **Verify all required files** are in build context
3. **Update base images** to latest versions:
   ```dockerfile
   FROM python:3.11-slim
   FROM node:18-alpine
   ```

4. **Clear Docker build cache** and rebuild
5. **Check network connectivity** during build

### Problem: Container Out of Memory

**Symptoms:**
- Container killed with exit code 137
- "Out of memory" errors in logs
- Performance degradation before crash

**Solution:**
1. **Increase memory limits:**
   ```bash
   MEMORY_LIMIT=1g  # Increase from 512m
   ```

2. **Optimize application memory usage:**
   ```bash
   DB_POOL_SIZE=10  # Reduce if too high
   GUNICORN_WORKERS=2  # Reduce if necessary
   ```

3. **Monitor memory usage** in Dokploy dashboard
4. **Check for memory leaks** in application code

## Performance Problems

### Problem: Slow Application Performance

**Symptoms:**
- Pages load slowly
- API responses take >3 seconds
- High CPU/memory usage

**Solution:**
1. **Increase resource allocation:**
   ```bash
   MEMORY_LIMIT=2g
   CPU_LIMIT=2.0
   GUNICORN_WORKERS=8
   ```

2. **Optimize database performance:**
   ```bash
   DB_POOL_SIZE=30
   DB_MAX_OVERFLOW=50
   ```

3. **Enable caching and compression:**
   ```bash
   CACHE_TYPE=simple
   COMPRESS_RESPONSES=true
   ```

4. **Monitor resource usage** and identify bottlenecks

### Problem: High Resource Usage

**Symptoms:**
- CPU usage consistently >80%
- Memory usage near limits
- Server becomes unresponsive

**Solution:**
1. **Scale resources** based on usage patterns
2. **Optimize application code** for efficiency
3. **Implement caching** for frequently accessed data
4. **Consider horizontal scaling** with multiple instances

## SSL/HTTPS Issues

### Problem: SSL Certificate Errors

**Symptoms:**
- Browser shows "Not secure" warning
- SSL certificate errors
- Mixed content warnings

**Solution:**
1. **Enable SSL in Dokploy** with Let's Encrypt
2. **Force HTTPS redirect:**
   ```bash
   FORCE_HTTPS=true
   ```

3. **Update CORS origins** to use HTTPS:
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **Check domain DNS** configuration
5. **Verify certificate renewal** is working

### Problem: Mixed Content Errors

**Symptoms:**
- Some resources load over HTTP instead of HTTPS
- Browser blocks insecure content
- Partial page functionality

**Solution:**
1. **Update all URLs** to use HTTPS or relative paths
2. **Set security headers:**
   ```bash
   FORCE_HTTPS=true
   HSTS_MAX_AGE=31536000
   ```

3. **Check Content Security Policy** settings
4. **Update API base URL** to use HTTPS

## Health Check Failures

### Problem: Health Checks Always Fail

**Symptoms:**
- Services marked as unhealthy in Dokploy
- Health check endpoints return errors
- Containers restart frequently

**Solution:**
1. **Test health check endpoints manually:**
   ```bash
   curl http://localhost:5000/api/health
   curl http://localhost:80/health
   ```

2. **Check health check configuration:**
   ```bash
   HEALTH_CHECK_ENABLED=true
   HEALTH_CHECK_DATABASE=true
   ```

3. **Adjust health check timing:**
   ```yaml
   healthcheck:
     start_period: 120s  # Increase startup time
     interval: 60s       # Reduce frequency
   ```

4. **Verify health check dependencies** (database, etc.)

### Problem: Intermittent Health Check Failures

**Symptoms:**
- Health checks sometimes pass, sometimes fail
- Sporadic service restarts
- Inconsistent service status

**Solution:**
1. **Increase health check timeout:**
   ```yaml
   healthcheck:
     timeout: 30s  # Increase from 10s
   ```

2. **Check for resource contention** during health checks
3. **Monitor database connectivity** stability
4. **Review application logs** for intermittent errors

## Resource and Memory Issues

### Problem: Database Performance Degradation

**Symptoms:**
- Slow query execution
- Database connection timeouts
- High database CPU usage

**Solution:**
1. **Increase database resources:**
   ```bash
   DB_MEMORY_LIMIT=1g
   DB_CPU_LIMIT=2.0
   ```

2. **Optimize connection pool:**
   ```bash
   DB_POOL_SIZE=20
   DB_POOL_RECYCLE=1800
   ```

3. **Add database indexes** for frequently queried columns
4. **Monitor query performance** and optimize slow queries

### Problem: Disk Space Issues

**Symptoms:**
- "No space left on device" errors
- Container fails to start
- Log files growing too large

**Solution:**
1. **Clean up Docker images and containers:**
   ```bash
   docker system prune -a
   ```

2. **Implement log rotation:**
   ```bash
   LOG_MAX_BYTES=10485760  # 10MB
   LOG_BACKUP_COUNT=5
   ```

3. **Monitor disk usage** in Dokploy dashboard
4. **Set up automated cleanup** for old logs and data

## Logging and Monitoring

### Problem: Missing or Insufficient Logs

**Symptoms:**
- Can't find error information
- Logs don't contain enough detail
- Debugging is difficult

**Solution:**
1. **Enable detailed logging:**
   ```bash
   LOG_LEVEL=DEBUG  # Temporarily for troubleshooting
   REQUEST_LOGGING=true
   ```

2. **Check log configuration:**
   ```bash
   LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s
   ```

3. **Access logs in Dokploy dashboard**
4. **Set up log aggregation** for better analysis

### Problem: Log Files Growing Too Large

**Symptoms:**
- Disk space consumed by logs
- Performance impact from large log files
- Difficulty finding recent logs

**Solution:**
1. **Implement log rotation:**
   ```bash
   LOG_MAX_BYTES=10485760
   LOG_BACKUP_COUNT=5
   ```

2. **Reduce log verbosity** in production:
   ```bash
   LOG_LEVEL=INFO  # Change from DEBUG
   ```

3. **Set up external log management** (optional)
4. **Regular log cleanup** procedures

## Recovery Procedures

### Complete Service Recovery

If all services are down:

1. **Check Dokploy dashboard** for service status
2. **Review recent changes** to environment variables or configuration
3. **Restart all services** in correct order:
   - Database first
   - Backend second
   - Frontend last
4. **Monitor logs** during startup
5. **Run verification script** once services are up

### Database Recovery

If database is corrupted or lost:

1. **Stop all services** that depend on database
2. **Check volume integrity** and mounting
3. **Restore from backup** if available
4. **Reinitialize database** if no backup:
   ```bash
   # This will recreate database schema and seed data
   # WARNING: This will lose all existing data
   ```
5. **Restart services** and verify functionality

### Configuration Recovery

If configuration is broken:

1. **Export working environment variables** from backup
2. **Reset to known good configuration**
3. **Apply changes incrementally**
4. **Test each change** before proceeding
5. **Document working configuration**

### Emergency Rollback

If deployment is completely broken:

1. **Identify last working version** or configuration
2. **Revert environment variables** to previous state
3. **Redeploy previous Docker images** if necessary
4. **Restore database** from backup if needed
5. **Verify system functionality**
6. **Document issues** for future prevention

## Prevention Best Practices

### Regular Maintenance

1. **Monitor resource usage** weekly
2. **Review logs** for warnings and errors
3. **Update dependencies** regularly
4. **Test backup and recovery** procedures
5. **Document configuration changes**

### Monitoring Setup

1. **Set up uptime monitoring** (external service)
2. **Configure alerts** for service failures
3. **Monitor resource thresholds**
4. **Track performance metrics**
5. **Regular health check validation**

### Security Maintenance

1. **Rotate secrets** regularly (SECRET_KEY, passwords)
2. **Update Docker images** for security patches
3. **Review access logs** for suspicious activity
4. **Keep SSL certificates** updated
5. **Monitor security headers** and CORS configuration

## Getting Help

### Information to Collect

When seeking help, collect:

1. **Error messages** from logs
2. **Environment variable configuration** (sanitized)
3. **Docker Compose configuration**
4. **Validation script output**
5. **Verification script output**
6. **Resource usage statistics**
7. **Timeline of changes** made before issue

### Useful Commands

```bash
# Check service status
docker ps

# View logs
docker logs <container_name>

# Check resource usage
docker stats

# Test connectivity
curl -v https://yourdomain.com/api/health

# Validate configuration
python scripts/validate-deployment.py --strict

# Verify deployment
python scripts/verify-deployment.py --base-url https://yourdomain.com --verbose
```

### Support Resources

1. **Dokploy Documentation**: Official deployment guides
2. **Docker Documentation**: Container troubleshooting
3. **Flask Documentation**: Backend framework issues
4. **React Documentation**: Frontend framework issues
5. **PostgreSQL Documentation**: Database issues

Remember to always test changes in a development environment before applying them to production!