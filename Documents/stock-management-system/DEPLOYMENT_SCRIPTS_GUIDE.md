# Deployment Scripts Guide

This guide explains how to use the deployment validation and verification scripts for the Stock Management System.

## Overview

The deployment scripts help ensure successful deployment to Dokploy by:

1. **Validating configuration** before deployment
2. **Verifying functionality** after deployment
3. **Providing troubleshooting guidance** for common issues

## Available Scripts

### 1. Pre-Deployment Validation (`validate-deployment.py`)

Validates environment variables, Docker configuration, and system requirements before deployment.

**Usage:**
```bash
python scripts/validate-deployment.py [--env-file .env.production] [--strict]
```

**Options:**
- `--env-file`: Path to environment file (default: `.env.production`)
- `--strict`: Fail on warnings (default: false)

**What it checks:**
- ✅ Required environment variables (SECRET_KEY, POSTGRES_PASSWORD, CORS_ORIGINS)
- ✅ Security configuration (DEBUG=false, FLASK_ENV=production, etc.)
- ✅ Database connection settings
- ✅ Performance and resource settings
- ✅ Docker configuration files
- ✅ System requirements (Docker, Docker Compose)

**Example:**
```bash
# Basic validation
python scripts/validate-deployment.py

# Strict validation with custom env file
python scripts/validate-deployment.py --env-file .env.prod --strict
```

### 2. Post-Deployment Verification (`verify-deployment.py`)

Verifies that all services are running correctly after deployment.

**Usage:**
```bash
python scripts/verify-deployment.py [--base-url https://yourdomain.com] [--timeout 30] [--verbose]
```

**Options:**
- `--base-url`: Base URL of deployed application (default: `http://localhost`)
- `--timeout`: Request timeout in seconds (default: 30)
- `--verbose`: Enable detailed output

**What it checks:**
- ✅ Frontend accessibility
- ✅ API health endpoints
- ✅ Database connectivity
- ✅ CORS configuration
- ✅ Security headers
- ✅ Performance metrics

**Example:**
```bash
# Basic verification
python scripts/verify-deployment.py --base-url https://myapp.com

# Verbose verification with custom timeout
python scripts/verify-deployment.py --base-url https://myapp.com --timeout 60 --verbose
```

### 3. Deployment Check Wrapper (`deployment-check.sh`)

Convenient shell script that runs validation and/or verification with a single command.

**Usage:**
```bash
./scripts/deployment-check.sh [validate|verify|both] [options]
```

**Commands:**
- `validate`: Run pre-deployment validation only
- `verify`: Run post-deployment verification only
- `both`: Run both validation and verification (default)
- `help`: Show help message

**Options:**
- `--env-file FILE`: Environment file to validate
- `--base-url URL`: Base URL for verification
- `--strict`: Enable strict validation mode
- `--verbose`: Enable verbose output

**Examples:**
```bash
# Run both validation and verification
./scripts/deployment-check.sh

# Run validation only
./scripts/deployment-check.sh validate --strict

# Run verification only
./scripts/deployment-check.sh verify --base-url https://myapp.com

# Run both with all options
./scripts/deployment-check.sh both --env-file .env.prod --base-url https://myapp.com --strict --verbose
```

## Quick Start Guide

### Before Deployment

1. **Create production environment file:**
   ```bash
   cp .env.production .env.prod
   # Edit .env.prod with your actual values
   ```

2. **Run validation:**
   ```bash
   ./scripts/deployment-check.sh validate --env-file .env.prod --strict
   ```

3. **Fix any issues** reported by the validation script

4. **Deploy to Dokploy** using your configured environment variables

### After Deployment

1. **Wait for services to start** (usually 2-3 minutes)

2. **Run verification:**
   ```bash
   ./scripts/deployment-check.sh verify --base-url https://yourdomain.com --verbose
   ```

3. **Check results** and fix any issues found

### Complete Deployment Check

Run both validation and verification in one command:

```bash
./scripts/deployment-check.sh both --env-file .env.prod --base-url https://yourdomain.com --strict --verbose
```

## Common Validation Issues

### Missing Required Variables

**Error:** `Missing required variable: Flask secret key for session management`

**Solution:**
```bash
# Generate a secure secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Add to your environment file
SECRET_KEY=your_generated_secret_key_here
```

### Weak Security Configuration

**Error:** `SECRET_KEY contains weak pattern 'change_this'`

**Solution:**
```bash
# Generate a new secure key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Replace the weak key with the generated one
```

### Incorrect Database Configuration

**Error:** `For Dokploy, DATABASE_URL hostname should be 'database'`

**Solution:**
```bash
# Use 'database' as hostname for Docker Compose
DATABASE_URL=postgresql://postgres:your_password@database:5432/stock_management
```

### CORS Configuration Issues

**Error:** `CORS_ORIGINS should not use '*' in production`

**Solution:**
```bash
# Set your actual domain
CORS_ORIGINS=https://yourdomain.com

# For multiple domains
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Common Verification Issues

### Frontend Not Accessible

**Error:** `Frontend not accessible: Connection error`

**Solutions:**
1. Check if domain DNS points to your server
2. Verify Dokploy proxy configuration
3. Ensure frontend container is running
4. Check SSL certificate if using HTTPS

### API Health Check Failures

**Error:** `API health check failed: Request timeout`

**Solutions:**
1. Check if backend container is running
2. Verify database connectivity
3. Check resource limits and increase if needed
4. Review backend logs for errors

### CORS Errors

**Error:** `CORS preflight failed: Connection error`

**Solutions:**
1. Verify CORS_ORIGINS matches your domain exactly
2. Check SESSION_COOKIE_SECURE=true for HTTPS
3. Ensure SESSION_COOKIE_SAMESITE=None for cross-origin

### Database Connectivity Issues

**Error:** `Database status: disconnected`

**Solutions:**
1. Check if database container is running
2. Verify database credentials match
3. Check database host is set to 'database'
4. Review database logs for connection errors

## Script Output Examples

### Successful Validation Output

```
Stock Management System - Deployment Validation
Environment file: .env.production
Strict mode: Disabled

============================================================
                REQUIRED ENVIRONMENT VARIABLES
============================================================
✓ Required Variable: SECRET_KEY: Valid Flask secret key for session management
✓ Required Variable: POSTGRES_PASSWORD: Valid PostgreSQL database password
✓ Required Variable: CORS_ORIGINS: Valid Allowed CORS origins for API access

============================================================
                   SECURITY CONFIGURATION
============================================================
✓ Security Setting: DEBUG: Correctly set to 'false'
✓ Security Setting: FLASK_ENV: Correctly set to 'production'
✓ Security Setting: SESSION_COOKIE_SECURE: Correctly set to 'true'

============================================================
                   VALIDATION SUMMARY
============================================================
✓ Passed: 15
✗ Failed: 0
⚠ Warnings: 0
Total Checks: 15

✅ VALIDATION PASSED
All checks passed. Ready for deployment!
```

### Successful Verification Output

```
Stock Management System - Deployment Verification
Base URL: https://myapp.com
Timeout: 30s
Verbose: Enabled

============================================================
                  FRONTEND ACCESSIBILITY
============================================================
✓ Frontend Main Page: Frontend is accessible (0.45s)
✓ Frontend Health Endpoint: Frontend health check passed (0.32s)

============================================================
                   API HEALTH ENDPOINTS
============================================================
✓ API Basic Health: API health check passed (0.28s)
✓ API Health Status: API reports status: healthy
✓ API Detailed Health: API detailed health check passed (0.31s)
✓ System Metrics: System metrics available
✓ Database Connectivity: Database status: connected

============================================================
                   VERIFICATION SUMMARY
============================================================
✓ Passed: 12
✗ Failed: 0
Total Checks: 12

✅ VERIFICATION PASSED
All checks passed. Deployment is healthy!
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Deploy to Dokploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Validate deployment configuration
        run: |
          python scripts/validate-deployment.py --env-file .env.production --strict
      
      - name: Deploy to Dokploy
        # Your deployment steps here
        run: echo "Deploy to Dokploy"
      
      - name: Verify deployment
        run: |
          sleep 120  # Wait for services to start
          python scripts/verify-deployment.py --base-url https://myapp.com --timeout 60
```

### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit

echo "Running deployment validation..."
if ! python scripts/validate-deployment.py --env-file .env.production; then
    echo "Deployment validation failed. Fix issues before committing."
    exit 1
fi

echo "Deployment validation passed."
```

## Troubleshooting

### Script Dependencies

The scripts require:
- Python 3.7+
- `requests` library for verification script

Install dependencies:
```bash
pip install requests
```

### Permission Issues

Make scripts executable:
```bash
chmod +x scripts/validate-deployment.py
chmod +x scripts/verify-deployment.py
chmod +x scripts/deployment-check.sh
```

### Network Issues

If verification fails with connection errors:
1. Check if the domain is accessible from your location
2. Verify DNS resolution: `nslookup yourdomain.com`
3. Test with curl: `curl -I https://yourdomain.com`
4. Check firewall and security group settings

### Environment File Issues

If validation can't read environment file:
1. Check file exists and is readable
2. Verify file format (KEY=value, no spaces around =)
3. Ensure no special characters in file path
4. Check file encoding (should be UTF-8)

## Best Practices

### Before Every Deployment

1. **Always run validation** with `--strict` flag
2. **Test with production-like environment** variables
3. **Review all warnings** even if validation passes
4. **Keep environment files secure** and never commit them

### After Every Deployment

1. **Wait for services to fully start** before verification
2. **Run verification with verbose output** for detailed information
3. **Check all endpoints** are responding correctly
4. **Monitor logs** for any errors or warnings

### Regular Maintenance

1. **Run verification weekly** to catch issues early
2. **Update validation rules** as requirements change
3. **Keep scripts updated** with new checks
4. **Document any custom validation** requirements

## Support

For issues with the deployment scripts:

1. **Check the troubleshooting guide** in `TROUBLESHOOTING_GUIDE.md`
2. **Review script output** for specific error messages
3. **Run with verbose/debug flags** for more information
4. **Check system requirements** and dependencies
5. **Verify network connectivity** and permissions

The scripts are designed to provide clear, actionable feedback to help ensure successful deployments to Dokploy.