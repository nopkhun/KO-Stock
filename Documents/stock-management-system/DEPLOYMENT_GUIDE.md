# Stock Management System - Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Stock Management System on a production server or local environment.

## System Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum, 50GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Network**: Internet connection for initial setup

### Required Software
- Docker Engine 20.10+
- Docker Compose 1.29+
- Git (for cloning repository)

## Dokploy Deployment

The project ships with production-ready Dockerfiles and a compose stack that works well with [Dokploy](https://dokploy.com/). The high-level process is:

1. **Create a new stack**
   - In the Dokploy dashboard create a project and choose *Docker Compose* deployment.
   - Point the repository URL to this project and select the branch you want to deploy.

2. **Configure environment variables**
   - Copy `.env.example` to `.env`, update secrets locally, and paste the key/value pairs into Dokploy’s environment editor.
   - At minimum set `POSTGRES_PASSWORD`, `SECRET_KEY`, `CORS_ORIGINS`, and `SESSION_COOKIE_SECURE`/`SESSION_COOKIE_SAMESITE` if you serve the frontend and backend from different domains.

3. **Volumes & persistence**
   - Map the `postgres_data` volume to persistent storage inside Dokploy so your database survives restarts.

4. **Ports and networking**
   - Expose port `80` from the `frontend` service (public HTTP) and `5000` from the `backend` service if you need direct API access.
   - Dokploy automatically wires the internal network so the frontend can reach the backend via the service name `backend`.

5. **Deploy & verify**
   - Trigger a deployment. Dokploy will build the images, start the containers, and run the built-in health checks (`/api/health` for the backend, `/` for the frontend).
   - Check application logs from the Dokploy UI if a service goes unhealthy.

6. **Domain & TLS (optional)**
   - Attach your domain to the frontend service and enable automatic HTTPS (Let’s Encrypt) from the Dokploy dashboard.

## Quick Deployment

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install -y docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again to apply group changes
```

### 2. Application Deployment

```bash
# Clone the repository (or upload files to server)
git clone <repository-url>
cd stock-management-system

# Copy environment configuration
cp .env.example .env

# Edit environment variables (IMPORTANT!)
nano .env

# Start the application
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Initial Setup

```bash
# Wait for services to be healthy (2-3 minutes)
docker-compose logs -f

# Access the application
# Frontend: http://your-server-ip
# Backend API: http://your-server-ip:5000
```

## Environment Configuration

### Critical Environment Variables

Edit the `.env` file with your production values:

```bash
# Database Security
POSTGRES_PASSWORD=your-secure-database-password

# Application Security
SECRET_KEY=your-flask-secret-key-minimum-32-characters
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=None

# CORS Configuration (adjust for your domain)
CORS_ORIGINS=https://your-domain.com

# Database Configuration
DATABASE_URL=postgresql://postgres:your-secure-database-password@database:5432/stock_management
```

### Security Best Practices

1. **Change Default Passwords**
   ```bash
   # Generate secure passwords
   openssl rand -base64 32  # For SECRET_KEY
   openssl rand -base64 16  # For POSTGRES_PASSWORD
   ```

2. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS (if using SSL)
   sudo ufw enable
   ```

3. **SSL/HTTPS Setup** (Recommended for production)
   ```bash
   # Install Certbot for Let's Encrypt
   sudo apt install certbot python3-certbot-nginx
   
   # Obtain SSL certificate
   sudo certbot --nginx -d your-domain.com
   ```

## Service Management

### Starting Services
```bash
docker-compose up -d
```

### Stopping Services
```bash
docker-compose down
```

### Restarting Services
```bash
docker-compose restart
```

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

### Updating Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Database Management

### Backup Database
```bash
# Create backup
docker exec stock_management_db pg_dump -U postgres stock_management > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker exec stock_management_db pg_dump -U postgres stock_management | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database
```bash
# Restore from backup
docker exec -i stock_management_db psql -U postgres stock_management < backup_file.sql
```

### Database Access
```bash
# Connect to database
docker exec -it stock_management_db psql -U postgres -d stock_management
```

## Monitoring and Maintenance

### Health Checks
```bash
# Check service health
curl http://localhost:5000/api/health

# Check all services
docker-compose ps
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats

# Monitor disk usage
df -h
du -sh /var/lib/docker/
```

### Log Rotation
```bash
# Configure Docker log rotation
sudo nano /etc/docker/daemon.json

# Add log rotation settings:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart Docker
sudo systemctl restart docker
```

## Troubleshooting

### Common Issues

1. **Services Won't Start**
   ```bash
   # Check Docker daemon
   sudo systemctl status docker
   
   # Check port conflicts
   sudo netstat -tulpn | grep :80
   sudo netstat -tulpn | grep :5000
   
   # Check logs
   docker-compose logs
   ```

2. **Database Connection Issues**
   ```bash
   # Check database container
   docker-compose logs database
   
   # Test database connection
   docker exec stock_management_db pg_isready -U postgres
   ```

3. **Frontend Not Loading**
   ```bash
   # Check nginx configuration
   docker exec stock_management_frontend nginx -t
   
   # Check frontend logs
   docker-compose logs frontend
   ```

4. **API Not Responding**
   ```bash
   # Check backend logs
   docker-compose logs backend
   
   # Test API endpoint
   curl http://localhost:5000/api/health
   ```

### Performance Issues

1. **High Memory Usage**
   ```bash
   # Check container memory usage
   docker stats --no-stream
   
   # Restart services if needed
   docker-compose restart
   ```

2. **Slow Database Queries**
   ```bash
   # Enable query logging (temporarily)
   docker exec stock_management_db psql -U postgres -c "ALTER SYSTEM SET log_statement = 'all';"
   docker exec stock_management_db psql -U postgres -c "SELECT pg_reload_conf();"
   ```

## Scaling and Production Considerations

### Load Balancing
For high-traffic deployments, consider:
- Multiple backend instances behind a load balancer
- Database read replicas
- Redis caching layer
- CDN for static assets

### Backup Strategy
```bash
# Automated daily backups
echo "0 2 * * * docker exec stock_management_db pg_dump -U postgres stock_management | gzip > /backups/stock_management_\$(date +\%Y\%m\%d).sql.gz" | crontab -
```

### Monitoring Setup
Consider implementing:
- Application performance monitoring (APM)
- Log aggregation (ELK stack)
- Uptime monitoring
- Resource monitoring (Prometheus + Grafana)

## Support and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Check logs and system resources
2. **Monthly**: Update system packages and Docker images
3. **Quarterly**: Review and rotate secrets/passwords
4. **Annually**: Security audit and dependency updates

### Getting Help
- Check application logs first
- Review this deployment guide
- Consult the main README.md for application features
- Check Docker and system logs for infrastructure issues

### Contact Information
For technical support or deployment assistance, please refer to the project documentation or contact the development team.
