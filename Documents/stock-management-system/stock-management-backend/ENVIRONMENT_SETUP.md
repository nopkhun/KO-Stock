# Environment Configuration Guide

This guide explains how to properly configure environment variables for the Stock Management System.

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file with your values:**
   ```bash
   # Required: Set a strong secret key (32+ characters)
   SECRET_KEY=your_random_32_plus_character_secret_key_here
   
   # Required: Set a secure database password
   POSTGRES_PASSWORD=your_secure_database_password
   
   # Required for production: Set your domain
   CORS_ORIGINS=https://yourdomain.com
   ```

3. **Validate your configuration:**
   ```bash
   python validate_env.py
   ```

## Environment Validation

The system includes comprehensive environment validation that:

- ✅ Checks all required variables are present
- ✅ Validates variable formats and security requirements
- ✅ Provides clear error messages for issues
- ✅ Warns about potential security concerns
- ✅ Supports both individual DB settings and DATABASE_URL

### Running Validation

```bash
# Validate current environment
python validate_env.py

# Validate with specific .env file
python validate_env.py --env-file /path/to/.env

# Quiet mode (only errors/warnings)
python validate_env.py --quiet
```

## Required Variables

### SECRET_KEY
- **Purpose:** Flask session management and CSRF protection
- **Requirements:** 
  - Minimum 32 characters
  - Must not use default/example values
  - Should have good entropy (diverse characters)
- **Example:** `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### POSTGRES_PASSWORD
- **Purpose:** Database authentication
- **Requirements:**
  - Minimum 8 characters
  - Must not use common/weak passwords
- **Example:** `secure_production_password_123`

## Database Configuration

Choose **ONE** of these approaches:

### Option 1: DATABASE_URL (Recommended)
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

### Option 2: Individual Settings
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=stock_management
POSTGRES_HOST=database  # For Docker Compose
POSTGRES_PORT=5432
```

## Production Settings

For production deployment, ensure these settings:

```bash
# Security
SECRET_KEY=your_random_32_plus_character_secret_key
POSTGRES_PASSWORD=strong_database_password

# Environment
FLASK_ENV=production
DEBUG=false

# HTTPS/Cookies (for HTTPS domains)
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=None

# CORS (set to your actual domain)
CORS_ORIGINS=https://yourdomain.com

# Password hashing
BCRYPT_LOG_ROUNDS=12
```

## Dokploy Deployment

When deploying with Dokploy:

1. **Set environment variables in Dokploy's interface** (don't include .env file in image)
2. **Use `database` as POSTGRES_HOST** (Docker Compose service name)
3. **Ensure HTTPS settings** for production domains
4. **Validate before deployment:**
   ```bash
   python validate_env.py --quiet
   ```

## Common Issues

### Missing Required Variables
```
❌ Missing required environment variable: SECRET_KEY
```
**Solution:** Set the missing variable in your .env file or environment

### Weak Secret Key
```
❌ Invalid value for SECRET_KEY: Must be at least 32 characters long
```
**Solution:** Generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database Connection Issues
```
❌ Either DATABASE_URL or individual database settings required
```
**Solution:** Provide either DATABASE_URL or all individual DB settings

### CORS Warnings
```
⚠️ CORS_ORIGINS='*' allows all origins
```
**Solution:** Set specific domains for production:
```bash
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Security Best Practices

1. **Never commit .env files** to version control
2. **Use strong, unique passwords** for database
3. **Generate random secret keys** (don't reuse across environments)
4. **Restrict CORS origins** to your actual domains
5. **Enable secure cookies** for HTTPS environments
6. **Validate configuration** before deployment

## Development vs Production

### Development
```bash
FLASK_ENV=development
DEBUG=true
SESSION_COOKIE_SECURE=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production
```bash
FLASK_ENV=production
DEBUG=false
SESSION_COOKIE_SECURE=true
CORS_ORIGINS=https://yourdomain.com
```

## Troubleshooting

If you encounter issues:

1. **Run validation:** `python validate_env.py`
2. **Check the logs** for specific error messages
3. **Verify all required variables** are set
4. **Ensure values meet requirements** (length, format, etc.)
5. **For Dokploy:** Check environment variables in the Dokploy interface

## Support

For additional help:
- Check the validation error messages (they include specific guidance)
- Refer to `.env.example` for proper format
- Review the troubleshooting tips in validation output