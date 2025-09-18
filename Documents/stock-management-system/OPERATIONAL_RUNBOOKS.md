# Operational Runbooks - Stock Management System

This document provides comprehensive operational procedures for monitoring, maintaining, and troubleshooting the Stock Management System deployed on Dokploy.

## Table of Contents

- [System Monitoring Procedures](#system-monitoring-procedures)
- [Maintenance Procedures](#maintenance-procedures)
- [Backup and Recovery Procedures](#backup-and-recovery-procedures)
- [Performance Tuning Guidelines](#performance-tuning-guidelines)
- [Incident Response Procedures](#incident-response-procedures)
- [Security Operations](#security-operations)
- [Capacity Planning](#capacity-planning)

## System Monitoring Procedures

### Daily Health Checks

#### Automated Health Monitoring

**Frequency**: Every 5 minutes (automated)
**Tools**: Dokploy dashboard, health check endpoints

**Procedure**:
1. **Service Health Verification**
   ```bash
   # Check all services are healthy in Dokploy dashboard
   # Green status indicators for:
   # - Frontend service
   # - Backend service  
   # - Database service
   ```

2. **Health Endpoint Monitoring**
   ```bash
   # Test primary health endpoint
   curl -f https://yourdomain.com/api/health
   
   # Expected response:
   {
     "status": "healthy",
     "timestamp": "2024-01-01T12:00:00Z",
     "database": "connected",
     "version": "1.0.0"
   }
   ```

3. **Detailed System Metrics**
   ```bash
   # Check detailed health with system metrics
   curl https://yourdomain.com/api/health/detailed
   
   # Monitor for:
   # - CPU usage < 80%
   # - Memory usage < 85%
   # - Database connections < pool limit
   # - Response time < 2 seconds
   ```

#### Manual Daily Checks

**Frequency**: Once daily (morning)
**Responsible**: Operations team

**Checklist**:
- [ ] All services showing healthy status
- [ ] No error spikes in application logs
- [ ] Resource usage within normal ranges
- [ ] Backup completion verification
- [ ] SSL certificate validity (if expiring within 30 days)
- [ ] Disk space usage < 80%

**Procedure**:
1. **Access Dokploy Dashboard**
   - Log into Dokploy admin interface
   - Navigate to Stock Management project

2. **Service Status Review**
   ```bash
   # Check service uptime and restart counts
   # Verify no frequent restarts (> 3 in 24h indicates issue)
   # Review resource usage trends
   ```

3. **Log Analysis**
   ```bash
   # Review error logs from past 24 hours
   # Look for patterns in:
   # - Authentication failures
   # - Database connection errors
   # - API response errors
   # - Security events
   ```

4. **Performance Metrics Review**
   ```bash
   # Check average response times
   # Monitor database query performance
   # Review memory and CPU trends
   # Verify no resource limit warnings
   ```

### Weekly System Review

**Frequency**: Weekly (Monday morning)
**Duration**: 30-45 minutes

**Procedure**:
1. **Performance Trend Analysis**
   ```bash
   # Review 7-day performance trends:
   # - Average response times
   # - Peak resource usage
   # - Error rate patterns
   # - User activity trends
   ```

2. **Resource Utilization Review**
   ```bash
   # Analyze resource usage patterns:
   # - CPU utilization trends
   # - Memory usage patterns
   # - Disk I/O performance
   # - Network traffic analysis
   ```

3. **Security Event Review**
   ```bash
   # Review security-related events:
   # - Failed login attempts
   # - Unusual access patterns
   # - SSL certificate status
   # - Security header compliance
   ```

4. **Capacity Planning Assessment**
   ```bash
   # Evaluate if resource adjustments needed:
   # - Current vs allocated resources
   # - Growth trend analysis
   # - Performance bottleneck identification
   ```

### Monthly System Audit

**Frequency**: Monthly (first Monday)
**Duration**: 2-3 hours

**Procedure**:
1. **Comprehensive Performance Review**
   - Analyze 30-day performance trends
   - Identify optimization opportunities
   - Review and update resource allocations
   - Document performance improvements

2. **Security Audit**
   - Review access logs and patterns
   - Audit user permissions and roles
   - Check for security vulnerabilities
   - Update security configurations

3. **Backup and Recovery Verification**
   - Test backup restoration process
   - Verify backup integrity
   - Update recovery procedures
   - Document any issues found

4. **Documentation Updates**
   - Update operational procedures
   - Review and update contact information
   - Update configuration documentation
   - Review incident response procedures

## Maintenance Procedures

### Routine Maintenance Tasks

#### Daily Maintenance (Automated)

**Log Rotation**:
```bash
# Automated log rotation (configured in Docker)
# Logs rotated when > 10MB
# Keep 3 historical files
# Compressed storage
```

**Health Check Monitoring**:
```bash
# Automated health checks every 30 seconds
# Automatic service restart on failure
# Alert generation for persistent failures
```

**Resource Monitoring**:
```bash
# Continuous resource monitoring
# Alerts when usage > 85%
# Automatic scaling triggers (if configured)
```

#### Weekly Maintenance

**Frequency**: Sunday 2:00 AM (low traffic period)
**Duration**: 30-60 minutes
**Downtime**: None (rolling updates)

**Procedure**:
1. **System Updates Check**
   ```bash
   # Check for available updates:
   # - Base Docker images
   # - Application dependencies
   # - Security patches
   
   # Review update impact and schedule if needed
   ```

2. **Performance Optimization**
   ```bash
   # Database maintenance:
   # - Analyze query performance
   # - Update statistics
   # - Check for unused indexes
   
   # Application optimization:
   # - Review slow endpoints
   # - Optimize resource allocation
   # - Clear temporary files
   ```

3. **Log Analysis and Cleanup**
   ```bash
   # Analyze log patterns from past week
   # Archive old logs if needed
   # Clean up temporary files
   # Review disk space usage
   ```

#### Monthly Maintenance

**Frequency**: First Sunday of month, 2:00 AM
**Duration**: 2-4 hours
**Downtime**: Planned 15-30 minutes

**Procedure**:
1. **System Updates**
   ```bash
   # Update base images:
   docker-compose pull
   
   # Update application dependencies:
   # - Python packages (requirements.txt)
   # - Node.js packages (package.json)
   # - System packages in containers
   
   # Test updates in staging environment first
   ```

2. **Database Maintenance**
   ```bash
   # Database optimization:
   # - VACUUM and ANALYZE tables
   # - Reindex if needed
   # - Update table statistics
   # - Check for fragmentation
   
   # Connection pool optimization:
   # - Review connection patterns
   # - Adjust pool sizes if needed
   # - Monitor for connection leaks
   ```

3. **Security Updates**
   ```bash
   # Security maintenance:
   # - Rotate application secrets
   # - Update SSL certificates
   # - Review security configurations
   # - Audit user access
   ```

4. **Performance Tuning**
   ```bash
   # Performance optimization:
   # - Analyze 30-day performance data
   # - Adjust resource allocations
   # - Optimize slow queries
   # - Update caching strategies
   ```

### Emergency Maintenance Procedures

#### Critical Security Updates

**Trigger**: Critical security vulnerability discovered
**Response Time**: Within 4 hours
**Approval**: Security team + Operations manager

**Procedure**:
1. **Assessment Phase** (30 minutes)
   ```bash
   # Assess vulnerability impact:
   # - Affected components
   # - Exploitation risk
   # - Business impact
   # - Required downtime
   ```

2. **Preparation Phase** (60 minutes)
   ```bash
   # Prepare update:
   # - Test patch in staging
   # - Prepare rollback plan
   # - Notify stakeholders
   # - Schedule maintenance window
   ```

3. **Implementation Phase** (30-60 minutes)
   ```bash
   # Apply security update:
   # - Create system backup
   # - Apply patches
   # - Verify functionality
   # - Monitor for issues
   ```

4. **Verification Phase** (30 minutes)
   ```bash
   # Verify security fix:
   # - Test vulnerability is patched
   # - Verify system functionality
   # - Monitor system stability
   # - Document changes
   ```

#### Performance Emergency

**Trigger**: System performance degradation > 50%
**Response Time**: Within 2 hours
**Approval**: Operations team lead

**Procedure**:
1. **Immediate Assessment** (15 minutes)
   ```bash
   # Identify performance bottleneck:
   # - Check resource usage
   # - Review error logs
   # - Identify affected components
   # - Assess user impact
   ```

2. **Quick Fixes** (30 minutes)
   ```bash
   # Apply immediate fixes:
   # - Restart affected services
   # - Increase resource limits
   # - Clear caches if needed
   # - Scale services if possible
   ```

3. **Root Cause Analysis** (60 minutes)
   ```bash
   # Identify root cause:
   # - Analyze performance metrics
   # - Review recent changes
   # - Check for resource exhaustion
   # - Identify optimization opportunities
   ```

4. **Permanent Solution** (varies)
   ```bash
   # Implement permanent fix:
   # - Optimize code/queries
   # - Adjust resource allocation
   # - Update configuration
   # - Plan capacity upgrades
   ```

## Backup and Recovery Procedures

### Backup Procedures

#### Automated Daily Backups

**Schedule**: Daily at 2:00 AM UTC
**Retention**: 30 days
**Storage**: Local + offsite (if configured)

**Components Backed Up**:
1. **Database Backup**
   ```bash
   # PostgreSQL database dump
   # Includes all tables, indexes, and data
   # Compressed format for storage efficiency
   
   # Backup command (automated):
   pg_dump -U postgres -h database stock_management | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
   ```

2. **Volume Backup**
   ```bash
   # Persistent volume data
   # - postgres_data volume
   # - upload_data volume (if used)
   
   # Volume backup (automated):
   tar czf postgres_data_$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/postgres_data/_data
   ```

3. **Configuration Backup**
   ```bash
   # Environment variables
   # Docker compose configuration
   # Dokploy project settings
   
   # Configuration export (weekly):
   # Export from Dokploy dashboard
   # Save docker-compose.yml
   # Document environment variables
   ```

#### Manual Backup Procedures

**When to Use**: Before major updates, configuration changes, or migrations

**Procedure**:
1. **Pre-Backup Verification**
   ```bash
   # Verify system is stable
   # Check no active maintenance
   # Ensure sufficient storage space
   # Notify team of backup operation
   ```

2. **Database Backup**
   ```bash
   # Create manual database backup
   docker exec stock_management_database pg_dump -U postgres stock_management > manual_backup_$(date +%Y%m%d_%H%M%S).sql
   
   # Verify backup integrity
   head -n 20 manual_backup_*.sql
   tail -n 20 manual_backup_*.sql
   ```

3. **Volume Backup**
   ```bash
   # Backup persistent volumes
   docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_manual_$(date +%Y%m%d).tar.gz -C /data .
   
   # Backup upload data (if applicable)
   docker run --rm -v upload_data:/data -v $(pwd):/backup alpine tar czf /backup/upload_data_manual_$(date +%Y%m%d).tar.gz -C /data .
   ```

4. **Configuration Backup**
   ```bash
   # Export current configuration
   cp docker-compose.yml docker-compose.backup.$(date +%Y%m%d).yml
   
   # Export environment variables from Dokploy
   # Save as environment_backup_$(date +%Y%m%d).env
   ```

5. **Backup Verification**
   ```bash
   # Verify backup files exist and are not empty
   ls -la *backup*
   
   # Test database backup integrity
   docker exec -i stock_management_database psql -U postgres -c "CREATE DATABASE test_restore;"
   docker exec -i stock_management_database psql -U postgres test_restore < manual_backup_*.sql
   docker exec -i stock_management_database psql -U postgres -c "DROP DATABASE test_restore;"
   ```

### Recovery Procedures

#### Database Recovery

**Scenario**: Database corruption or data loss
**Recovery Time Objective (RTO)**: 30 minutes
**Recovery Point Objective (RPO)**: 24 hours (daily backup)

**Procedure**:
1. **Assessment Phase** (5 minutes)
   ```bash
   # Assess damage extent:
   # - Check database accessibility
   # - Identify affected tables/data
   # - Determine recovery scope
   # - Select appropriate backup
   ```

2. **Preparation Phase** (10 minutes)
   ```bash
   # Prepare for recovery:
   # - Stop application services
   docker-compose stop backend frontend
   
   # Backup current state (if partially recoverable)
   docker exec stock_management_database pg_dump -U postgres stock_management > pre_recovery_backup.sql
   
   # Identify latest good backup
   ls -la backup_*.sql.gz | tail -5
   ```

3. **Recovery Phase** (10 minutes)
   ```bash
   # Drop and recreate database
   docker exec stock_management_database psql -U postgres -c "DROP DATABASE IF EXISTS stock_management;"
   docker exec stock_management_database psql -U postgres -c "CREATE DATABASE stock_management;"
   
   # Restore from backup
   gunzip -c backup_YYYYMMDD_HHMMSS.sql.gz | docker exec -i stock_management_database psql -U postgres stock_management
   ```

4. **Verification Phase** (5 minutes)
   ```bash
   # Verify database restoration
   docker exec stock_management_database psql -U postgres stock_management -c "\dt"
   docker exec stock_management_database psql -U postgres stock_management -c "SELECT COUNT(*) FROM users;"
   
   # Start services
   docker-compose start backend frontend
   
   # Test application functionality
   curl https://yourdomain.com/api/health
   ```

#### Volume Recovery

**Scenario**: Volume corruption or accidental deletion
**Recovery Time Objective (RTO)**: 45 minutes
**Recovery Point Objective (RPO)**: 24 hours

**Procedure**:
1. **Stop Affected Services** (2 minutes)
   ```bash
   # Stop services using the volume
   docker-compose stop
   ```

2. **Assess Volume State** (3 minutes)
   ```bash
   # Check volume status
   docker volume ls
   docker volume inspect postgres_data
   
   # Identify latest backup
   ls -la postgres_data_*.tar.gz | tail -5
   ```

3. **Restore Volume Data** (15 minutes)
   ```bash
   # Remove corrupted volume (if necessary)
   docker volume rm postgres_data
   
   # Create new volume
   docker volume create postgres_data
   
   # Restore data from backup
   docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data_YYYYMMDD.tar.gz -C /data
   ```

4. **Verify and Restart** (25 minutes)
   ```bash
   # Start services
   docker-compose up -d
   
   # Wait for services to be healthy
   # Monitor logs for errors
   docker-compose logs -f
   
   # Test application functionality
   curl https://yourdomain.com/api/health
   ```

#### Complete System Recovery

**Scenario**: Complete system failure or migration
**Recovery Time Objective (RTO)**: 2 hours
**Recovery Point Objective (RPO)**: 24 hours

**Procedure**:
1. **Environment Preparation** (30 minutes)
   ```bash
   # Prepare new environment:
   # - Install Dokploy
   # - Configure basic settings
   # - Set up networking
   # - Configure storage
   ```

2. **Configuration Restoration** (30 minutes)
   ```bash
   # Restore project configuration:
   # - Create new Dokploy project
   # - Import docker-compose.yml
   # - Configure environment variables
   # - Set up volumes and networks
   ```

3. **Data Restoration** (45 minutes)
   ```bash
   # Restore volume data:
   # - Create persistent volumes
   # - Restore postgres_data from backup
   # - Restore upload_data from backup
   # - Verify volume integrity
   ```

4. **Service Deployment** (30 minutes)
   ```bash
   # Deploy services:
   # - Build and start containers
   # - Monitor service health
   # - Verify database connectivity
   # - Test application functionality
   ```

5. **Final Verification** (15 minutes)
   ```bash
   # Complete system test:
   # - Test user authentication
   # - Verify data integrity
   # - Test all major functions
   # - Monitor for errors
   ```

### Backup Monitoring and Maintenance

#### Backup Verification

**Frequency**: Daily (automated)
**Procedure**:
```bash
# Verify backup completion
# Check backup file sizes
# Test backup integrity
# Alert on backup failures
```

#### Backup Cleanup

**Frequency**: Weekly
**Procedure**:
```bash
# Remove backups older than retention period
find /backup -name "backup_*.sql.gz" -mtime +30 -delete

# Clean up temporary backup files
find /backup -name "*.tmp" -delete

# Monitor backup storage usage
df -h /backup
```

#### Offsite Backup (Optional)

**Frequency**: Daily (after local backup)
**Procedure**:
```bash
# Upload to cloud storage (if configured)
# - AWS S3
# - Google Cloud Storage
# - Azure Blob Storage

# Verify offsite backup integrity
# Monitor transfer success
# Alert on upload failures
```

## Performance Tuning Guidelines

### Performance Monitoring

#### Key Performance Indicators (KPIs)

**Application Performance**:
- API response time: < 500ms (95th percentile)
- Database query time: < 100ms (average)
- Page load time: < 2 seconds
- Error rate: < 0.1%
- Uptime: > 99.9%

**System Performance**:
- CPU utilization: < 70% (average)
- Memory utilization: < 80% (average)
- Disk I/O: < 80% capacity
- Network latency: < 50ms

**Database Performance**:
- Connection pool usage: < 80%
- Query execution time: < 100ms (average)
- Lock wait time: < 10ms
- Cache hit ratio: > 95%

#### Performance Monitoring Tools

**Built-in Monitoring**:
```bash
# Health check endpoints
curl https://yourdomain.com/api/health/detailed

# System metrics in health response:
{
  "status": "healthy",
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 34.8
  },
  "database": {
    "status": "connected",
    "pool_size": 20,
    "active_connections": 8
  }
}
```

**Dokploy Dashboard**:
- Container resource usage
- Service health status
- Log aggregation
- Performance graphs

### Resource Optimization

#### CPU Optimization

**Current Usage Assessment**:
```bash
# Monitor CPU usage patterns
# Identify peak usage times
# Analyze CPU-intensive operations
```

**Optimization Strategies**:
```bash
# Adjust Gunicorn workers based on CPU cores
GUNICORN_WORKERS=$(($(nproc) * 2 + 1))

# For 2 CPU cores:
GUNICORN_WORKERS=4

# For 4 CPU cores:
GUNICORN_WORKERS=8

# Monitor and adjust based on actual usage
```

**CPU Limit Tuning**:
```bash
# Conservative (< 50% average usage):
CPU_LIMIT=1.0

# Moderate (50-70% average usage):
CPU_LIMIT=2.0

# High performance (> 70% average usage):
CPU_LIMIT=4.0
```

#### Memory Optimization

**Memory Usage Analysis**:
```bash
# Monitor memory consumption patterns
# Identify memory leaks
# Analyze garbage collection patterns
```

**Memory Allocation Guidelines**:
```bash
# Backend service memory allocation:
# Light usage (< 100 concurrent users):
MEMORY_LIMIT=512m

# Medium usage (100-500 concurrent users):
MEMORY_LIMIT=1g

# High usage (> 500 concurrent users):
MEMORY_LIMIT=2g

# Database memory allocation:
# Small dataset (< 1GB):
DB_MEMORY_LIMIT=256m

# Medium dataset (1-10GB):
DB_MEMORY_LIMIT=512m

# Large dataset (> 10GB):
DB_MEMORY_LIMIT=1g
```

**Memory Optimization Techniques**:
```bash
# Connection pool optimization
DB_POOL_SIZE=20              # Adjust based on concurrent users
DB_MAX_OVERFLOW=30           # 1.5x pool size
DB_POOL_RECYCLE=3600         # Recycle connections hourly

# Application-level optimization
# - Implement caching strategies
# - Optimize database queries
# - Use pagination for large datasets
# - Implement lazy loading
```

#### Database Performance Tuning

**Connection Pool Optimization**:
```bash
# Pool size calculation: 2-4 connections per CPU core
# For 2 CPU cores:
DB_POOL_SIZE=8
DB_MAX_OVERFLOW=12

# For 4 CPU cores:
DB_POOL_SIZE=16
DB_MAX_OVERFLOW=24

# Monitor pool usage and adjust
```

**Query Optimization**:
```bash
# Enable query logging (temporarily for analysis)
docker exec stock_management_database psql -U postgres -c "ALTER SYSTEM SET log_statement = 'all';"
docker exec stock_management_database psql -U postgres -c "SELECT pg_reload_conf();"

# Analyze slow queries
docker exec stock_management_database psql -U postgres -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Disable query logging after analysis
docker exec stock_management_database psql -U postgres -c "ALTER SYSTEM SET log_statement = 'none';"
docker exec stock_management_database psql -U postgres -c "SELECT pg_reload_conf();"
```

**Database Maintenance**:
```bash
# Weekly database maintenance (automated)
# VACUUM and ANALYZE tables
docker exec stock_management_database psql -U postgres stock_management -c "VACUUM ANALYZE;"

# Reindex if needed (monthly)
docker exec stock_management_database psql -U postgres stock_management -c "REINDEX DATABASE stock_management;"

# Update table statistics
docker exec stock_management_database psql -U postgres stock_management -c "ANALYZE;"
```

### Application Performance Optimization

#### Caching Strategies

**Response Caching**:
```bash
# Enable response caching
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300    # 5 minutes

# Cache frequently accessed data
# - User sessions
# - Product catalogs
# - Inventory summaries
```

**Database Query Caching**:
```bash
# Implement query result caching
# Cache expensive aggregation queries
# Use Redis for distributed caching (optional)
```

**Static Asset Optimization**:
```bash
# Enable compression
COMPRESS_RESPONSES=true
COMPRESS_LEVEL=6
COMPRESS_MIN_SIZE=1024

# Set cache headers for static files
STATIC_FILE_CACHE=true
CACHE_CONTROL_MAX_AGE=86400  # 24 hours
```

#### API Performance Optimization

**Request Optimization**:
```bash
# Implement pagination for large datasets
# Default page size: 50 items
# Maximum page size: 200 items

# Use database indexes for frequently queried fields
# Optimize JOIN operations
# Implement database connection pooling
```

**Response Optimization**:
```bash
# Minimize response payload size
# Use JSON compression
# Implement field selection (sparse fieldsets)
# Cache frequently requested data
```

### Network Performance Optimization

#### Nginx Configuration Optimization

**Connection Optimization**:
```nginx
# In nginx.conf
worker_processes auto;
worker_connections 1024;

# Keep-alive connections
keepalive_timeout 65;
keepalive_requests 100;

# Buffer sizes
client_body_buffer_size 128k;
client_max_body_size 16m;
```

**Compression Configuration**:
```nginx
# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml+rss;
```

**Caching Configuration**:
```nginx
# Static file caching
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# API response caching (selective)
location /api/static-data {
    expires 1h;
    add_header Cache-Control "public";
}
```

## Incident Response Procedures

### Incident Classification

#### Severity Levels

**Critical (P1)**:
- Complete system outage
- Data loss or corruption
- Security breach
- Response Time: 15 minutes
- Resolution Time: 2 hours

**High (P2)**:
- Major functionality unavailable
- Performance degradation > 50%
- Authentication issues
- Response Time: 30 minutes
- Resolution Time: 4 hours

**Medium (P3)**:
- Minor functionality issues
- Performance degradation < 50%
- Non-critical errors
- Response Time: 2 hours
- Resolution Time: 24 hours

**Low (P4)**:
- Cosmetic issues
- Enhancement requests
- Documentation updates
- Response Time: 24 hours
- Resolution Time: 1 week

### Incident Response Process

#### Initial Response (First 15 minutes)

1. **Incident Detection**
   ```bash
   # Automated alerts from:
   # - Health check failures
   # - Resource threshold breaches
   # - Error rate spikes
   # - User reports
   ```

2. **Initial Assessment**
   ```bash
   # Quick assessment checklist:
   # - Verify incident scope and impact
   # - Check service status in Dokploy
   # - Review recent changes
   # - Determine severity level
   ```

3. **Immediate Actions**
   ```bash
   # For critical incidents:
   # - Notify incident response team
   # - Create incident ticket
   # - Begin status page updates
   # - Start incident log
   ```

#### Investigation Phase (15-60 minutes)

1. **System Status Check**
   ```bash
   # Check all system components:
   curl https://yourdomain.com/api/health/detailed
   
   # Review Dokploy dashboard:
   # - Service health status
   # - Resource usage graphs
   # - Recent deployment history
   # - Container logs
   ```

2. **Log Analysis**
   ```bash
   # Review application logs:
   docker-compose logs --tail=100 backend
   docker-compose logs --tail=100 frontend
   docker-compose logs --tail=100 database
   
   # Look for:
   # - Error patterns
   # - Performance issues
   # - Security events
   # - Resource exhaustion
   ```

3. **Root Cause Analysis**
   ```bash
   # Investigate potential causes:
   # - Recent deployments or changes
   # - Resource exhaustion
   # - Database issues
   # - Network connectivity
   # - External dependencies
   ```

#### Resolution Phase (varies by severity)

1. **Immediate Mitigation**
   ```bash
   # Quick fixes to restore service:
   # - Restart affected services
   # - Increase resource limits
   # - Rollback recent changes
   # - Enable maintenance mode
   ```

2. **Permanent Fix Implementation**
   ```bash
   # Implement permanent solution:
   # - Code fixes
   # - Configuration updates
   # - Resource adjustments
   # - Process improvements
   ```

3. **Verification and Monitoring**
   ```bash
   # Verify resolution:
   # - Test system functionality
   # - Monitor for recurring issues
   # - Validate performance metrics
   # - Update stakeholders
   ```

### Post-Incident Activities

#### Incident Documentation

1. **Incident Report Creation**
   ```markdown
   # Incident Report Template
   
   ## Incident Summary
   - Incident ID: INC-YYYY-NNNN
   - Date/Time: YYYY-MM-DD HH:MM UTC
   - Severity: P1/P2/P3/P4
   - Duration: X hours Y minutes
   - Services Affected: [list]
   - Users Affected: [number/percentage]
   
   ## Timeline
   - HH:MM - Incident detected
   - HH:MM - Investigation started
   - HH:MM - Root cause identified
   - HH:MM - Fix implemented
   - HH:MM - Service restored
   - HH:MM - Incident closed
   
   ## Root Cause
   [Detailed explanation of what caused the incident]
   
   ## Resolution
   [Description of how the incident was resolved]
   
   ## Lessons Learned
   [What was learned from this incident]
   
   ## Action Items
   - [ ] Action item 1 (Owner: Name, Due: Date)
   - [ ] Action item 2 (Owner: Name, Due: Date)
   ```

2. **Post-Incident Review (PIR)**
   ```bash
   # Schedule PIR meeting within 48 hours
   # Attendees: Incident response team, stakeholders
   # Agenda:
   # - Incident timeline review
   # - Root cause analysis
   # - Response effectiveness
   # - Improvement opportunities
   # - Action item assignment
   ```

#### Process Improvement

1. **Preventive Measures**
   ```bash
   # Implement measures to prevent recurrence:
   # - Enhanced monitoring
   # - Improved alerting
   # - Process updates
   # - Training needs
   ```

2. **Documentation Updates**
   ```bash
   # Update operational documentation:
   # - Runbook improvements
   # - Troubleshooting guides
   # - Monitoring procedures
   # - Contact information
   ```

## Security Operations

### Security Monitoring

#### Daily Security Checks

**Automated Security Monitoring**:
```bash
# Monitor for security events:
# - Failed authentication attempts
# - Unusual access patterns
# - Suspicious API requests
# - SSL certificate status
```

**Manual Security Review**:
```bash
# Daily security checklist:
# - Review authentication logs
# - Check for brute force attempts
# - Verify SSL certificate validity
# - Monitor for security alerts
```

#### Weekly Security Audit

**Access Review**:
```bash
# Review user access:
# - Active user accounts
# - Permission levels
# - Recent access patterns
# - Inactive accounts
```

**Security Configuration Review**:
```bash
# Verify security settings:
# - CORS configuration
# - Security headers
# - Session settings
# - Rate limiting
```

### Security Incident Response

#### Security Incident Classification

**Critical Security Incidents**:
- Data breach or unauthorized access
- Malware or ransomware detection
- DDoS attacks
- Privilege escalation

**Response Procedure**:
1. **Immediate Containment** (5 minutes)
   ```bash
   # Isolate affected systems
   # Block suspicious IP addresses
   # Disable compromised accounts
   # Enable enhanced logging
   ```

2. **Assessment and Investigation** (30 minutes)
   ```bash
   # Assess incident scope
   # Identify affected data/systems
   # Collect evidence
   # Determine attack vector
   ```

3. **Eradication and Recovery** (varies)
   ```bash
   # Remove threats
   # Patch vulnerabilities
   # Restore from clean backups
   # Implement additional controls
   ```

4. **Post-Incident Activities** (ongoing)
   ```bash
   # Notify stakeholders
   # Document incident
   # Improve security measures
   # Conduct lessons learned
   ```

### Security Maintenance

#### Monthly Security Tasks

**Security Updates**:
```bash
# Update security components:
# - Base Docker images
# - Application dependencies
# - SSL certificates
# - Security configurations
```

**Vulnerability Assessment**:
```bash
# Scan for vulnerabilities:
# - Container image scanning
# - Dependency vulnerability checks
# - Configuration security review
# - Penetration testing (quarterly)
```

#### Quarterly Security Review

**Comprehensive Security Audit**:
```bash
# Complete security assessment:
# - Access control review
# - Security policy updates
# - Incident response testing
# - Security training updates
```

## Capacity Planning

### Resource Usage Analysis

#### Current Usage Assessment

**CPU Usage Analysis**:
```bash
# Analyze CPU usage patterns:
# - Peak usage times
# - Average utilization
# - Growth trends
# - Bottleneck identification
```

**Memory Usage Analysis**:
```bash
# Monitor memory consumption:
# - Application memory usage
# - Database memory usage
# - Memory leak detection
# - Growth projections
```

**Storage Analysis**:
```bash
# Assess storage requirements:
# - Database growth rate
# - Log file accumulation
# - Backup storage needs
# - Archive requirements
```

#### Growth Projections

**User Growth Impact**:
```bash
# Calculate resource needs based on user growth:
# - Current users: X
# - Projected growth: Y% per month
# - Resource scaling factor: Z

# Example calculation:
# Current: 100 users, 2GB RAM
# 50% growth = 150 users
# Estimated RAM need: 3GB
```

**Data Growth Impact**:
```bash
# Project data storage needs:
# - Current database size
# - Monthly growth rate
# - Retention policies
# - Backup storage requirements
```

### Scaling Recommendations

#### Vertical Scaling (Resource Increase)

**When to Scale Up**:
- CPU usage consistently > 70%
- Memory usage consistently > 80%
- Response times increasing
- Resource limit warnings

**Scaling Guidelines**:
```bash
# CPU scaling:
# Current: 2 cores → Recommended: 4 cores
CPU_LIMIT=4.0
GUNICORN_WORKERS=8

# Memory scaling:
# Current: 2GB → Recommended: 4GB
MEMORY_LIMIT=2g
DB_MEMORY_LIMIT=1g
```

#### Horizontal Scaling (Service Replication)

**When to Scale Out**:
- Single instance performance limits reached
- High availability requirements
- Geographic distribution needs
- Load balancing benefits

**Scaling Architecture**:
```bash
# Multi-instance deployment:
# - Load balancer (nginx/HAProxy)
# - Multiple backend instances
# - Shared database
# - Session store (Redis)
```

### Capacity Planning Timeline

#### Short-term (1-3 months)

**Immediate Needs**:
```bash
# Based on current growth trends:
# - Resource adjustments
# - Performance optimizations
# - Monitoring improvements
```

#### Medium-term (3-12 months)

**Planned Upgrades**:
```bash
# Anticipated requirements:
# - Infrastructure upgrades
# - Architecture improvements
# - Feature additions impact
```

#### Long-term (1+ years)

**Strategic Planning**:
```bash
# Future considerations:
# - Technology migrations
# - Scalability architecture
# - Cost optimization
# - Business growth alignment
```

This completes the comprehensive operational runbooks for the Stock Management System. These procedures provide detailed guidance for monitoring, maintaining, and optimizing the system in production.