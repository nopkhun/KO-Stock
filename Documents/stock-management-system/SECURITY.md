# Security Guide for Stock Management System

## Overview

This document outlines the security measures implemented in the Stock Management System and provides guidelines for secure deployment and operation.

## Security Features

### 1. Container Security

#### Non-Root User Execution
- **Backend**: Runs as `appuser` (UID: 1000, GID: 1000)
- **Frontend**: Runs as `nginx-user` (UID: 1001, GID: 1001)
- **Database**: Uses PostgreSQL's built-in security with restricted permissions

#### Secure File Permissions
- Application files: `644` (read-only for group/others)
- Executable files: `755` (execute permission for owner only)
- Secret files: `600` (owner read/write only)
- Directories: `755` with proper ownership

#### Image Security
- Multi-stage builds to minimize attack surface
- Regular security updates in base images
- Minimal runtime dependencies
- No unnecessary packages or tools

### 2. Application Security

#### Input Validation and Sanitization
- **Comprehensive Input Validation**: All user inputs are validated using the security middleware
- **XSS Protection**: HTML content is sanitized using the `bleach` library
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Path Traversal Protection**: File path validation and restrictions

#### Authentication and Session Management
- **Secure Session Cookies**: HttpOnly, Secure, and SameSite attributes
- **Session Timeout**: 1-hour automatic timeout
- **Session Validation**: IP consistency checks and user status validation
- **Password Security**: BCrypt hashing with configurable rounds (default: 12)

#### Rate Limiting
- **API Rate Limiting**: 100 requests per hour per IP (configurable)
- **Burst Protection**: 20 requests per minute per IP (configurable)
- **Login Protection**: Additional rate limiting on authentication endpoints

### 3. Network Security

#### Security Headers
All responses include comprehensive security headers:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self';
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
X-Permitted-Cross-Domain-Policies: none
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

#### CORS Configuration
- **Strict Origin Control**: Only configured domains are allowed
- **Credential Support**: Secure credential handling for authenticated requests
- **Preflight Handling**: Proper CORS preflight request handling

#### HTTPS/TLS
- **Secure Cookies**: Enabled for HTTPS environments
- **HSTS Headers**: HTTP Strict Transport Security for HTTPS enforcement
- **TLS Configuration**: Ready for TLS termination at reverse proxy level

### 4. Data Security

#### Database Security
- **Connection Encryption**: Support for encrypted database connections
- **Connection Pooling**: Secure connection pool management
- **Credential Management**: Environment-based credential configuration
- **Data Validation**: Input validation before database operations

#### Secret Management
- **Environment Variables**: All secrets stored as environment variables
- **Secret Generation**: Cryptographically secure random generation
- **Secret Rotation**: Built-in tools for regular secret rotation
- **No Hardcoded Secrets**: All sensitive data externalized

### 5. Monitoring and Logging

#### Security Event Logging
- **Authentication Events**: Login attempts, failures, and successes
- **Rate Limiting Events**: Blocked requests and suspicious activity
- **Input Validation Events**: Malicious input attempts
- **System Events**: Application startup, shutdown, and errors

#### Health Monitoring
- **Health Check Endpoints**: Comprehensive system health monitoring
- **Resource Monitoring**: CPU, memory, and disk usage tracking
- **Database Connectivity**: Connection status and performance monitoring

## Security Configuration

### Environment Variables

#### Required Security Variables
```bash
# Flask secret key (minimum 32 characters)
SECRET_KEY=your-secure-random-32-plus-character-string

# Database password (minimum 8 characters)
POSTGRES_PASSWORD=your-secure-database-password

# Session security
SESSION_COOKIE_SECURE=true  # For HTTPS environments
SESSION_COOKIE_SAMESITE=None  # For cross-origin requests
```

#### Optional Security Variables
```bash
# Security middleware configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_BURST=20
SECURITY_HEADERS_ENABLED=true
INPUT_VALIDATION_ENABLED=true

# Password hashing
BCRYPT_LOG_ROUNDS=12

# CORS configuration
CORS_ORIGINS=https://yourdomain.com
```

### Docker Security Configuration

#### Resource Limits
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
```

#### Security Options
```yaml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
```

## Security Tools and Scripts

### 1. Security Scanning
```bash
# Run comprehensive security scan
./scripts/security-scan.sh

# Scan specific component
./scripts/security-scan.sh --backend
./scripts/security-scan.sh --frontend
```

### 2. Secret Management
```bash
# Generate secure secrets
./scripts/secret-management.sh generate

# Validate existing secrets
./scripts/secret-management.sh validate

# Rotate secrets
./scripts/secret-management.sh rotate

# Check for exposed secrets
./scripts/secret-management.sh check
```

### 3. Deployment Validation
```bash
# Validate deployment configuration
./scripts/validate-deployment.py

# Verify deployment security
./scripts/verify-deployment.py
```

## Security Best Practices

### 1. Development
- **Never commit secrets** to version control
- **Use environment variables** for all configuration
- **Validate all inputs** at application boundaries
- **Follow principle of least privilege**
- **Regular dependency updates**

### 2. Deployment
- **Use HTTPS/TLS** in production
- **Configure proper CORS** policies
- **Set secure session cookies**
- **Enable all security middleware**
- **Use strong, unique secrets**

### 3. Operations
- **Regular security scans**
- **Monitor security logs**
- **Rotate secrets regularly** (every 90 days)
- **Keep systems updated**
- **Backup security configurations**

### 4. Monitoring
- **Set up log aggregation**
- **Monitor for suspicious activity**
- **Alert on security events**
- **Regular security audits**

## Incident Response

### 1. Security Event Detection
- Monitor application logs for security events
- Set up alerts for failed authentication attempts
- Track rate limiting violations
- Monitor for input validation failures

### 2. Response Procedures
1. **Immediate**: Block suspicious IP addresses
2. **Short-term**: Rotate compromised secrets
3. **Medium-term**: Investigate and patch vulnerabilities
4. **Long-term**: Review and improve security measures

### 3. Recovery Steps
1. Assess the scope of the incident
2. Contain the threat (block IPs, rotate secrets)
3. Investigate root cause
4. Apply fixes and patches
5. Monitor for continued threats
6. Document lessons learned

## Compliance and Standards

### Security Standards Compliance
- **OWASP Top 10**: Protection against common web vulnerabilities
- **CIS Controls**: Implementation of critical security controls
- **NIST Framework**: Alignment with cybersecurity framework
- **ISO 27001**: Information security management principles

### Data Protection
- **Input Sanitization**: All user inputs are sanitized
- **Output Encoding**: Proper encoding of dynamic content
- **Access Controls**: Role-based access control implementation
- **Audit Logging**: Comprehensive audit trail

## Security Testing

### Automated Testing
- **Dependency Scanning**: Regular vulnerability scans of dependencies
- **Container Scanning**: Security scans of Docker images
- **Static Analysis**: Code analysis for security vulnerabilities
- **Secret Detection**: Automated detection of exposed secrets

### Manual Testing
- **Penetration Testing**: Regular security assessments
- **Code Reviews**: Security-focused code reviews
- **Configuration Reviews**: Security configuration audits
- **Access Control Testing**: Verification of access controls

## Security Updates and Maintenance

### Regular Tasks
- **Weekly**: Review security logs and alerts
- **Monthly**: Update dependencies and base images
- **Quarterly**: Rotate secrets and review configurations
- **Annually**: Comprehensive security audit and penetration testing

### Update Procedures
1. **Test updates** in development environment
2. **Scan for vulnerabilities** after updates
3. **Deploy to staging** for validation
4. **Deploy to production** with monitoring
5. **Verify security** post-deployment

## Contact and Reporting

### Security Issues
If you discover a security vulnerability, please:

1. **Do not** create a public issue
2. **Email** the security team directly
3. **Provide** detailed information about the vulnerability
4. **Allow** reasonable time for response and fix

### Security Team
- **Response Time**: 24 hours for critical issues
- **Update Frequency**: Regular updates on progress
- **Disclosure**: Coordinated disclosure after fix

## Additional Resources

### Documentation
- [OWASP Security Guidelines](https://owasp.org/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Flask Security Documentation](https://flask.palletsprojects.com/en/2.3.x/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

### Tools
- [Trivy](https://aquasecurity.github.io/trivy/) - Vulnerability scanner
- [Hadolint](https://github.com/hadolint/hadolint) - Dockerfile linter
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit) - Node.js security scanner

---

**Note**: This security guide should be reviewed and updated regularly to reflect changes in the application, infrastructure, and threat landscape.