# Environment Variables Documentation

This document provides comprehensive documentation for all environment variables used in the Stock Management System, with specific guidance for Dokploy deployment.

## Table of Contents

- [Required Variables](#required-variables)
- [Database Configuration](#database-configuration)
- [Security Configuration](#security-configuration)
- [Session and Cookie Settings](#session-and-cookie-settings)
- [CORS Configuration](#cors-configuration)
- [Application Settings](#application-settings)
- [Frontend Configuration](#frontend-configuration)
- [Logging and Monitoring](#logging-and-monitoring)
- [Security Headers](#security-headers)
- [Performance Settings](#performance-settings)
- [Dokploy-Specific Settings](#dokploy-specific-settings)
- [Optional Features](#optional-features)
- [Environment Validation](#environment-validation)

## Required Variables

These variables MUST be set for the application to function properly in production:

### `SECRET_KEY`
- **Type**: String
- **Required**: Yes
- **Minimum Length**: 32 characters
- **Description**: Flask secret key used for session management, CSRF protection, and cryptographic operations
- **Security**: Must be cryptographically secure random string
- **Generation**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Example**: `xvz9k2m8n7b6v5c4x3z2a1s9d8f7g6h5j4k3l2m1n0p9`
- **Dokploy**: Set in environment variables interface, never in code

### `POSTGRES_PASSWORD`
- **Type**: String
- **Required**: Yes
- **Minimum Length**: 8 characters (recommended: 12+)
- **Description**: PostgreSQL database password
- **Security**: Use strong password with mixed case, numbers, and symbols
- **Example**: `MySecureDbPass123!`
- **Dokploy**: Set in environment variables interface as sensitive value

### `CORS_ORIGINS`
- **Type**: String (comma-separated URLs)
- **Required**: Yes for production
- **Description**: Allowed origins for Cross-Origin Resource Sharing
- **Format**: `https://domain1.com,https://domain2.com`
- **Security**: Never use `*` in production
- **Example**: `https://myapp.com,https://app.myapp.com`
- **Dokploy**: Set to your actual domain(s)

## Database Configuration

### Connection Methods

#### Option 1: DATABASE_URL (Recommended)
```
DATABASE_URL=postgresql://username:password@host:port/database
```
- **Description**: Complete PostgreSQL connection string
- **Advantage**: Overrides individual database settings, simpler configuration
- **Dokploy Example**: `postgresql://postgres:MySecurePass123@database:5432/stock_management`

#### Option 2: Individual Settings
```
POSTGRES_DB=stock_management
POSTGRES_USER=postgres
POSTGRES_PASSWORD=MySecurePass123
POSTGRES_HOST=database
POSTGRES_PORT=5432
```

### Connection Pool Settings

#### `DB_POOL_SIZE`
- **Type**: Integer
- **Default**: 20
- **Description**: Maximum number of database connections in pool
- **Recommendation**: 2-4 per CPU core
- **Dokploy**: Adjust based on VPS specifications

#### `DB_MAX_OVERFLOW`
- **Type**: Integer
- **Default**: 30
- **Description**: Additional connections beyond pool size
- **Recommendation**: 1.5x pool size

#### `DB_POOL_TIMEOUT`
- **Type**: Integer (seconds)
- **Default**: 30
- **Description**: Timeout for getting connection from pool
- **Range**: 10-60 seconds

#### `DB_POOL_RECYCLE`
- **Type**: Integer (seconds)
- **Default**: 3600 (1 hour)
- **Description**: Time after which connections are recycled
- **Purpose**: Prevents stale connections

## Security Configuration

### Authentication and Encryption

#### `BCRYPT_LOG_ROUNDS`
- **Type**: Integer
- **Default**: 12
- **Range**: 8-15
- **Description**: BCrypt hashing rounds for password security
- **Performance**: Higher = more secure but slower
- **Production**: 12-14 recommended

#### `JWT_SECRET_KEY` (Optional)
- **Type**: String
- **Required**: If using JWT authentication
- **Description**: Secret key for JWT token signing
- **Security**: Must be different from SECRET_KEY
- **Generation**: Same as SECRET_KEY

#### `JWT_ACCESS_TOKEN_EXPIRES`
- **Type**: Integer (seconds)
- **Default**: 3600 (1 hour)
- **Description**: JWT access token expiration time
- **Security**: Shorter = more secure, longer = better UX

#### `JWT_REFRESH_TOKEN_EXPIRES`
- **Type**: Integer (seconds)
- **Default**: 2592000 (30 days)
- **Description**: JWT refresh token expiration time

## Session and Cookie Settings

### `SESSION_COOKIE_SECURE`
- **Type**: Boolean
- **Default**: true (production)
- **Description**: Require HTTPS for session cookies
- **Production**: MUST be true with HTTPS
- **Development**: false for HTTP testing

### `SESSION_COOKIE_HTTPONLY`
- **Type**: Boolean
- **Default**: true
- **Description**: Prevent JavaScript access to session cookies
- **Security**: Protects against XSS attacks

### `SESSION_COOKIE_SAMESITE`
- **Type**: String
- **Options**: `None`, `Lax`, `Strict`
- **Default**: `None` (for cross-origin)
- **Description**: SameSite cookie policy
- **Cross-origin**: Use `None` with `SESSION_COOKIE_SECURE=true`
- **Same-origin**: Use `Lax` or `Strict`

### `PERMANENT_SESSION_LIFETIME`
- **Type**: Integer (seconds)
- **Default**: 86400 (24 hours)
- **Description**: Session timeout duration
- **Security**: Shorter = more secure

### `SESSION_COOKIE_DOMAIN`
- **Type**: String
- **Optional**: Yes
- **Description**: Cookie domain scope
- **Example**: `.yourdomain.com` (includes subdomains)
- **Dokploy**: Set to your domain if using subdomains

## CORS Configuration

### `CORS_ALLOW_CREDENTIALS`
- **Type**: Boolean
- **Default**: true
- **Description**: Allow credentials in CORS requests
- **Required**: For session-based authentication

### `CORS_MAX_AGE`
- **Type**: Integer (seconds)
- **Default**: 86400 (24 hours)
- **Description**: Preflight request cache duration
- **Performance**: Longer = fewer preflight requests

## Application Settings

### `FLASK_ENV`
- **Type**: String
- **Options**: `development`, `production`, `testing`
- **Production**: MUST be `production`
- **Description**: Flask environment mode

### `DEBUG`
- **Type**: Boolean
- **Production**: MUST be false
- **Description**: Enable Flask debug mode
- **Security**: Never enable in production

### `APP_NAME`
- **Type**: String
- **Default**: Stock Management System
- **Description**: Application name for logging and monitoring

### `APP_VERSION`
- **Type**: String
- **Default**: 1.0.0
- **Description**: Application version for tracking

### `APP_ENVIRONMENT`
- **Type**: String
- **Default**: production
- **Description**: Environment identifier for monitoring

## Server Configuration

### `HOST`
- **Type**: String
- **Default**: 0.0.0.0
- **Description**: Server bind address
- **Docker**: Must be 0.0.0.0 for container access

### `PORT`
- **Type**: Integer
- **Default**: 5000
- **Description**: Server port number
- **Dokploy**: Usually 5000 for backend

### Gunicorn Settings

#### `GUNICORN_WORKERS`
- **Type**: Integer
- **Default**: 4
- **Formula**: (2 × CPU cores) + 1
- **Description**: Number of worker processes

#### `GUNICORN_WORKER_CLASS`
- **Type**: String
- **Default**: sync
- **Options**: sync, gevent, eventlet
- **Description**: Worker process type

#### `GUNICORN_TIMEOUT`
- **Type**: Integer (seconds)
- **Default**: 30
- **Description**: Worker timeout for requests

#### `GUNICORN_KEEPALIVE`
- **Type**: Integer (seconds)
- **Default**: 2
- **Description**: Keep-alive timeout for connections

## Frontend Configuration

### `VITE_API_BASE_URL`
- **Type**: String
- **Default**: /api
- **Description**: Base URL for API requests from frontend
- **Same-domain**: Use `/api`
- **Cross-domain**: Use full URL like `https://api.yourdomain.com`

### `VITE_APP_TITLE`
- **Type**: String
- **Default**: Stock Management System
- **Description**: Application title displayed in browser

### `VITE_APP_VERSION`
- **Type**: String
- **Default**: 1.0.0
- **Description**: Frontend version for display

## Logging and Monitoring

### `LOG_LEVEL`
- **Type**: String
- **Options**: ERROR, WARNING, INFO, DEBUG
- **Production**: INFO
- **Troubleshooting**: DEBUG (temporarily)
- **Description**: Minimum log level to output

### `LOG_FORMAT`
- **Type**: String
- **Default**: Structured format with timestamp, function, line number
- **Description**: Log message format pattern

### `REQUEST_LOGGING`
- **Type**: Boolean
- **Default**: true
- **Description**: Enable HTTP request logging
- **Monitoring**: Useful for traffic analysis

### Health Check Settings

#### `HEALTH_CHECK_ENABLED`
- **Type**: Boolean
- **Default**: true
- **Description**: Enable health check endpoints

#### `HEALTH_CHECK_DATABASE`
- **Type**: Boolean
- **Default**: true
- **Description**: Include database connectivity in health checks

#### `HEALTH_CHECK_DETAILED`
- **Type**: Boolean
- **Default**: true
- **Description**: Include system metrics in health checks

## Security Headers

### Content Security Policy (CSP)

#### `CSP_DEFAULT_SRC`
- **Default**: 'self'
- **Description**: Default source policy for all content types

#### `CSP_SCRIPT_SRC`
- **Default**: 'self' 'unsafe-inline'
- **Description**: Allowed sources for JavaScript

#### `CSP_STYLE_SRC`
- **Default**: 'self' 'unsafe-inline'
- **Description**: Allowed sources for CSS

#### `CSP_IMG_SRC`
- **Default**: 'self' data: https:
- **Description**: Allowed sources for images

#### `CSP_FONT_SRC`
- **Default**: 'self' https:
- **Description**: Allowed sources for fonts

### Security Headers

#### `FORCE_HTTPS`
- **Type**: Boolean
- **Default**: true
- **Description**: Redirect HTTP to HTTPS

#### `HSTS_MAX_AGE`
- **Type**: Integer (seconds)
- **Default**: 31536000 (1 year)
- **Description**: HTTP Strict Transport Security duration

#### `HSTS_INCLUDE_SUBDOMAINS`
- **Type**: Boolean
- **Default**: true
- **Description**: Apply HSTS to subdomains

#### `X_CONTENT_TYPE_OPTIONS`
- **Default**: nosniff
- **Description**: Prevent MIME type sniffing

#### `X_FRAME_OPTIONS`
- **Default**: DENY
- **Description**: Prevent clickjacking attacks

#### `X_XSS_PROTECTION`
- **Default**: 1; mode=block
- **Description**: Enable XSS filtering

## Performance Settings

### Rate Limiting

#### `RATE_LIMIT_DEFAULT`
- **Type**: Integer (requests per minute)
- **Default**: 100
- **Description**: Default rate limit for API endpoints

#### `RATE_LIMIT_LOGIN`
- **Type**: Integer (requests per minute)
- **Default**: 10
- **Description**: Rate limit for login attempts

#### `RATE_LIMIT_API`
- **Type**: Integer (requests per minute)
- **Default**: 200
- **Description**: Rate limit for API endpoints

#### `RATE_LIMIT_STORAGE`
- **Type**: String
- **Options**: memory, redis
- **Default**: memory
- **Description**: Storage backend for rate limiting

### File Upload Settings

#### `MAX_CONTENT_LENGTH`
- **Type**: Integer (bytes)
- **Default**: 16777216 (16MB)
- **Description**: Maximum file upload size

#### `UPLOAD_FOLDER`
- **Type**: String
- **Default**: /app/uploads
- **Description**: Directory for uploaded files
- **Dokploy**: Use persistent volume

#### `ALLOWED_EXTENSIONS`
- **Type**: String (comma-separated)
- **Default**: jpg,jpeg,png,gif,pdf,xlsx,csv
- **Description**: Allowed file extensions for uploads

## Dokploy-Specific Settings

### Resource Limits

#### `MEMORY_LIMIT`
- **Type**: String
- **Default**: 512m
- **Description**: Container memory limit
- **Format**: 512m, 1g, 2g
- **Dokploy**: Adjust based on VPS specs

#### `CPU_LIMIT`
- **Type**: Float
- **Default**: 1.0
- **Description**: Container CPU limit
- **Format**: 0.5, 1.0, 2.0 (CPU cores)

### Health Check Configuration

#### `HEALTH_CHECK_INTERVAL`
- **Type**: Integer (seconds)
- **Default**: 30
- **Description**: Health check frequency

#### `HEALTH_CHECK_TIMEOUT`
- **Type**: Integer (seconds)
- **Default**: 10
- **Description**: Health check timeout

#### `HEALTH_CHECK_RETRIES`
- **Type**: Integer
- **Default**: 3
- **Description**: Health check failure retries

#### `HEALTH_CHECK_START_PERIOD`
- **Type**: Integer (seconds)
- **Default**: 60
- **Description**: Grace period before health checks start

### Container Configuration

#### `RESTART_POLICY`
- **Type**: String
- **Default**: unless-stopped
- **Options**: no, always, on-failure, unless-stopped
- **Description**: Container restart behavior

#### `NETWORK_MODE`
- **Type**: String
- **Default**: bridge
- **Description**: Docker network mode

#### `INTERNAL_NETWORK`
- **Type**: String
- **Default**: stock_management_network
- **Description**: Internal Docker network name

### Volume Configuration

#### `POSTGRES_DATA_VOLUME`
- **Type**: String
- **Default**: postgres_data
- **Description**: PostgreSQL data volume name

#### `UPLOAD_DATA_VOLUME`
- **Type**: String
- **Default**: upload_data
- **Description**: File upload volume name

## Optional Features

### Email Configuration

#### `MAIL_SERVER`
- **Type**: String
- **Example**: smtp.gmail.com
- **Description**: SMTP server hostname

#### `MAIL_PORT`
- **Type**: Integer
- **Default**: 587 (TLS), 465 (SSL)
- **Description**: SMTP server port

#### `MAIL_USE_TLS`
- **Type**: Boolean
- **Default**: true
- **Description**: Use TLS encryption

#### `MAIL_USERNAME`
- **Type**: String
- **Description**: SMTP authentication username

#### `MAIL_PASSWORD`
- **Type**: String
- **Description**: SMTP authentication password
- **Security**: Use app-specific password

#### `MAIL_DEFAULT_SENDER`
- **Type**: String
- **Example**: noreply@yourdomain.com
- **Description**: Default sender email address

### Backup Configuration

#### `BACKUP_ENABLED`
- **Type**: Boolean
- **Default**: false
- **Description**: Enable automatic database backups

#### `BACKUP_SCHEDULE`
- **Type**: String (cron format)
- **Default**: 0 2 * * * (daily at 2 AM)
- **Description**: Backup schedule

#### `BACKUP_RETENTION_DAYS`
- **Type**: Integer
- **Default**: 30
- **Description**: Number of days to keep backups

#### `BACKUP_S3_BUCKET`
- **Type**: String
- **Description**: S3 bucket for backup storage

### Maintenance Mode

#### `MAINTENANCE_MODE`
- **Type**: Boolean
- **Default**: false
- **Description**: Enable maintenance mode

#### `MAINTENANCE_MESSAGE`
- **Type**: String
- **Default**: System is under maintenance. Please try again later.
- **Description**: Message displayed during maintenance

## Environment Validation

### `VALIDATE_ENV_ON_STARTUP`
- **Type**: Boolean
- **Default**: true
- **Description**: Validate environment variables on application startup

### `STRICT_ENV_VALIDATION`
- **Type**: Boolean
- **Default**: true
- **Description**: Use strict validation rules

### `FAIL_ON_MISSING_ENV`
- **Type**: Boolean
- **Default**: true
- **Description**: Fail startup if required variables are missing

## Dokploy Deployment Examples

### Basic Production Setup
```bash
# Required variables
SECRET_KEY=xvz9k2m8n7b6v5c4x3z2a1s9d8f7g6h5j4k3l2m1n0p9
POSTGRES_PASSWORD=MySecureDbPass123!
CORS_ORIGINS=https://myapp.com

# Security settings
SESSION_COOKIE_SECURE=true
DEBUG=false
FLASK_ENV=production

# Database connection
DATABASE_URL=postgresql://postgres:MySecureDbPass123!@database:5432/stock_management
```

### High-Performance Setup
```bash
# All basic settings plus:
GUNICORN_WORKERS=8
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50
MEMORY_LIMIT=1g
CPU_LIMIT=2.0
```

### Multi-Domain Setup
```bash
# Multiple domains
CORS_ORIGINS=https://app.mycompany.com,https://admin.mycompany.com
SESSION_COOKIE_DOMAIN=.mycompany.com

# Subdomain support
CSP_DEFAULT_SRC='self' *.mycompany.com
```

## Security Best Practices

1. **Never commit production values** to version control
2. **Use Dokploy's environment variables interface** for all sensitive values
3. **Generate strong random values** for SECRET_KEY and passwords
4. **Enable HTTPS** and set SESSION_COOKIE_SECURE=true
5. **Use specific domains** in CORS_ORIGINS, never '*'
6. **Regularly rotate** SECRET_KEY and database passwords
7. **Monitor logs** for security events and errors
8. **Keep containers updated** with security patches
9. **Use strong passwords** and enable 2FA for Dokploy access
10. **Backup configuration** and database regularly

## Troubleshooting

### Common Issues

#### Database Connection Failures
- Check POSTGRES_PASSWORD matches in all services
- Verify POSTGRES_HOST is set to 'database' for Docker Compose
- Ensure database service starts before backend

#### CORS Errors
- Verify CORS_ORIGINS includes your domain with correct protocol (https://)
- Check SESSION_COOKIE_SAMESITE setting for cross-origin requests
- Ensure SESSION_COOKIE_SECURE=true with HTTPS

#### Session Issues
- Verify SECRET_KEY is set and consistent across restarts
- Check cookie settings match your deployment (HTTP vs HTTPS)
- Ensure session timeout settings are appropriate

#### Health Check Failures
- Check all required environment variables are set
- Verify database connectivity
- Review application logs for startup errors

### Debug Mode
To enable debug logging temporarily:
```bash
LOG_LEVEL=DEBUG
DEBUG=false  # Keep false even in debug mode for security
```

### Validation Errors
If environment validation fails:
1. Check the application logs for specific missing variables
2. Verify all required variables are set in Dokploy
3. Ensure variable names match exactly (case-sensitive)
4. Check for extra spaces or special characters in values