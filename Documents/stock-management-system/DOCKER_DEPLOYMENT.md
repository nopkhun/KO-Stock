# Docker Deployment Guide

This guide covers the optimized Docker Compose configuration for deploying the Stock Management System, particularly for Dokploy environments.

## Configuration Files

### Main Configuration
- `docker-compose.yml` - Base configuration with production optimizations
- `docker-compose.prod.yml` - Production-specific overrides
- `docker-compose.dokploy.yml` - Dokploy-specific configurations

### Deployment Options

#### 1. Standard Deployment
```bash
# Initialize volumes and permissions
./scripts/init-volumes.sh

# Deploy with base configuration
docker-compose up -d
```

#### 2. Production Deployment
```bash
# Deploy with production optimizations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 3. Dokploy Deployment
```bash
# Deploy with Dokploy-specific settings
docker-compose -f docker-compose.yml -f docker-compose.dokploy.yml up -d
```

## Key Features

### Resource Management
- **CPU Limits**: Prevents resource exhaustion
- **Memory Limits**: Optimized for VPS environments
- **Resource Reservations**: Ensures minimum resource allocation

### Health Checks
- **Database**: PostgreSQL readiness check with 30s start period
- **Backend**: API health endpoint with 60s start period
- **Frontend**: HTTP availability check with 30s start period

### Security Enhancements
- **No New Privileges**: Prevents privilege escalation
- **Read-only Containers**: Frontend runs in read-only mode
- **Temporary Filesystems**: Secure temporary storage
- **Network Isolation**: Internal Docker networking with specific IP ranges

### Networking
- **Subnet**: 172.20.0.0/16 with gateway at 172.20.0.1
- **Static IPs**: 
  - Database: 172.20.0.10
  - Backend: 172.20.0.20
  - Frontend: 172.20.0.30
- **Internal Communication**: Services communicate via internal network

### Volume Management
- **Named Volumes**: Configurable volume names for Dokploy
- **External Volumes**: Support for pre-existing volumes
- **Persistent Storage**: Database data persists across deployments

## Environment Variables

### Required Variables
```bash
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your_32_character_secret_key
DATABASE_URL=postgresql://postgres:password@172.20.0.10:5432/stock_management
```

### Optional Variables
```bash
# Database Configuration
POSTGRES_DB=stock_management
POSTGRES_USER=postgres
POSTGRES_VOLUME_NAME=stock_management_postgres_data
POSTGRES_VOLUME_EXTERNAL=false

# Frontend Configuration
FRONTEND_PORT=80

# Dokploy-specific
DOKPLOY_PORT=80
DOKPLOY_DOMAIN=yourdomain.com
```

## Monitoring and Logging

### Log Configuration
- **Driver**: JSON file driver
- **Max Size**: 10MB per log file
- **Max Files**: 3 files retained
- **Rotation**: Automatic log rotation

### Health Check Intervals
- **Database**: Every 15s (timeout: 10s, retries: 5)
- **Backend**: Every 20s (timeout: 15s, retries: 5)
- **Frontend**: Every 20s (timeout: 15s, retries: 3)

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Fix PostgreSQL data directory permissions
sudo chown -R 999:999 data/postgres
sudo chmod 700 data/postgres
```

#### 2. Network Conflicts
If the 172.20.0.0/16 subnet conflicts with existing networks:
```bash
# Edit docker-compose.yml and change the subnet
# Example: 172.21.0.0/16 or 10.20.0.0/16
```

#### 3. Volume Issues
```bash
# Remove and recreate volumes
docker-compose down -v
docker volume prune
docker-compose up -d
```

#### 4. Health Check Failures
```bash
# Check service logs
docker-compose logs database
docker-compose logs backend
docker-compose logs frontend

# Check health status
docker-compose ps
```

### Dokploy-Specific Troubleshooting

#### 1. Environment Variable Injection
Ensure Dokploy is configured to inject required environment variables:
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `DATABASE_URL`

#### 2. Volume Mounting
Verify that Dokploy has access to create and mount volumes:
```bash
# Check volume status
docker volume ls
docker volume inspect stock_management_postgres_data
```

#### 3. Port Conflicts
If port 80 is already in use:
```bash
# Set custom port in Dokploy
DOKPLOY_PORT=8080
```

## Performance Optimization

### Resource Allocation
- **Database**: 1 CPU, 512MB RAM (reserved: 0.25 CPU, 256MB)
- **Backend**: 1 CPU, 512MB RAM (reserved: 0.25 CPU, 128MB)
- **Frontend**: 0.5 CPU, 256MB RAM (reserved: 0.1 CPU, 64MB)

### Scaling Recommendations
For high-traffic environments, consider:
- Increasing CPU limits to 2.0 for database and backend
- Adding memory limits up to 1GB for database
- Using external load balancer for frontend scaling

## Security Considerations

### Container Security
- All containers run with `no-new-privileges`
- Frontend container is read-only
- Temporary filesystems for secure temporary storage
- Non-root user execution where possible

### Network Security
- Internal Docker network isolation
- No direct database port exposure in production
- Backend API only accessible via frontend proxy
- Configurable CORS policies

### Data Security
- Encrypted environment variable support
- Secure session cookie configuration
- Database connection encryption ready
- Proper secret management practices