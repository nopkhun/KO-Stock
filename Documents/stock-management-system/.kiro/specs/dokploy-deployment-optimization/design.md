# Design Document

## Overview

การออกแบบการปรับปรุงระบบ Stock Management System เพื่อให้พร้อมสำหรับการ deploy บน Dokploy โดยเน้นความเสถียร ความปลอดภัย และประสิทธิภาพ การออกแบบนี้จะปรับปรุงไฟล์ configuration ต่างๆ เพิ่ม monitoring และปรับปรุง security settings

## Architecture

### Current Architecture Analysis
ระบบปัจจุบันประกอบด้วย:
- **Frontend**: React.js + Vite + Nginx (Port 80)
- **Backend**: Flask + Gunicorn (Port 5000) 
- **Database**: PostgreSQL 15 (Port 5432)
- **Orchestration**: Docker Compose

### Dokploy Deployment Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        Dokploy VPS                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Frontend      │  │    Backend      │  │  Database   │ │
│  │   (Nginx)       │  │   (Flask)       │  │ (PostgreSQL)│ │
│  │   Port 80       │  │   Port 5000     │  │  Port 5432  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                   │       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            Docker Internal Network                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Persistent Volumes                         │ │
│  │  - postgres_data (Database storage)                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Environment Configuration Enhancement

**Current Issues:**
- ไม่มี validation สำหรับ required environment variables
- Security settings ไม่เหมาะสำหรับ production
- ไม่มี Dokploy-specific configurations

**Design Solution:**
- เพิ่ม environment validation ใน backend startup
- ปรับปรุง security defaults สำหรับ production
- เพิ่ม Dokploy-friendly environment variables
- สร้าง production-ready .env template

### 2. Docker Configuration Optimization

**Current Issues:**
- Backend Dockerfile ไม่มี proper health check command
- Frontend build อาจไม่ optimize สำหรับ production
- ไม่มี resource limits

**Design Solution:**
- ปรับปรุง Dockerfile ให้ production-ready
- เพิ่ม proper health check commands
- Optimize build process และ image size
- เพิ่ม resource limits และ security settings

### 3. Database Connection Resilience

**Current Issues:**
- ไม่มี connection retry mechanism
- Database initialization อาจล้มเหลวใน slow environments
- ไม่มี proper connection pooling

**Design Solution:**
- เพิ่ม database connection retry logic
- ปรับปรุง database initialization process
- เพิ่ม connection timeout และ pool settings
- เพิ่ม database health monitoring

### 4. Nginx Configuration Enhancement

**Current Issues:**
- Security headers ไม่ครบถ้วน
- ไม่มี rate limiting
- Cache settings อาจไม่เหมาะสม

**Design Solution:**
- เพิ่ม comprehensive security headers
- ปรับปรุง caching strategy
- เพิ่ม request timeout settings
- Optimize proxy settings สำหรับ Dokploy

### 5. Monitoring and Logging

**Current Issues:**
- Health checks ไม่ครอบคลุมทุก aspects
- Logging ไม่เพียงพอสำหรับ troubleshooting
- ไม่มี metrics collection

**Design Solution:**
- ปรับปรุง health check endpoints
- เพิ่ม structured logging
- เพิ่ม performance metrics
- เพิ่ม startup และ readiness probes

## Data Models

### Environment Configuration Model
```yaml
Environment Variables:
  Required:
    - POSTGRES_PASSWORD: Database password
    - SECRET_KEY: Flask secret key (min 32 chars)
    - DATABASE_URL: Full database connection string
  
  Optional with Defaults:
    - POSTGRES_DB: stock_management
    - POSTGRES_USER: postgres
    - FLASK_ENV: production
    - SESSION_COOKIE_SECURE: true (for HTTPS)
    - SESSION_COOKIE_SAMESITE: None (for cross-origin)
    - CORS_ORIGINS: https://yourdomain.com
```

### Health Check Model
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "ISO 8601 timestamp",
  "service": "service name",
  "version": "1.0.0",
  "database": "connected|disconnected",
  "system": {
    "cpu_percent": "number",
    "memory_percent": "number", 
    "disk_percent": "number"
  }
}
```

## Error Handling

### Database Connection Errors
- **Retry Logic**: 5 attempts with exponential backoff
- **Timeout Settings**: 30 seconds connection timeout
- **Fallback**: Graceful degradation with error logging
- **Recovery**: Automatic reconnection on health check

### Service Startup Errors
- **Validation**: Check all required environment variables
- **Dependencies**: Wait for database before starting backend
- **Logging**: Detailed error messages with troubleshooting hints
- **Exit Codes**: Proper exit codes for container orchestration

### Runtime Errors
- **API Errors**: Structured error responses with proper HTTP codes
- **Frontend Errors**: Error boundaries with user-friendly messages
- **Network Errors**: Retry mechanisms with circuit breaker pattern
- **Resource Errors**: Graceful handling of memory/disk limitations

## Testing Strategy

### Container Testing
1. **Build Tests**: Verify all Docker images build successfully
2. **Health Check Tests**: Validate all health endpoints respond correctly
3. **Integration Tests**: Test service-to-service communication
4. **Performance Tests**: Verify resource usage within limits

### Deployment Testing
1. **Environment Tests**: Test with various environment configurations
2. **Network Tests**: Verify internal and external connectivity
3. **Persistence Tests**: Validate data survives container restarts
4. **Security Tests**: Verify security headers and CORS policies

### Dokploy-Specific Testing
1. **Stack Deployment**: Test complete stack deployment via Dokploy
2. **Volume Mounting**: Verify persistent volumes work correctly
3. **Environment Injection**: Test environment variable management
4. **Service Discovery**: Verify internal service communication

## Security Considerations

### Container Security
- **Non-root Users**: All containers run as non-root users
- **Minimal Images**: Use Alpine-based images where possible
- **Security Scanning**: Regular vulnerability scanning
- **Resource Limits**: Prevent resource exhaustion attacks

### Network Security
- **Internal Networks**: Services communicate via internal Docker network
- **CORS Policies**: Strict CORS configuration for production
- **Security Headers**: Comprehensive security headers in Nginx
- **TLS Configuration**: Ready for HTTPS/TLS termination

### Data Security
- **Environment Variables**: Secure handling of sensitive configuration
- **Database Encryption**: Support for encrypted database connections
- **Session Security**: Secure session management with proper cookie settings
- **Input Validation**: Comprehensive input validation and sanitization

## Performance Optimizations

### Build Optimization
- **Multi-stage Builds**: Minimize final image sizes
- **Layer Caching**: Optimize Docker layer caching
- **Dependency Management**: Efficient dependency installation
- **Asset Optimization**: Minification and compression

### Runtime Optimization
- **Connection Pooling**: Efficient database connection management
- **Caching**: Proper HTTP caching headers
- **Compression**: Gzip compression for all text content
- **Resource Management**: Appropriate memory and CPU limits

### Monitoring Integration
- **Metrics Collection**: CPU, memory, and database metrics
- **Log Aggregation**: Structured logging for analysis
- **Health Monitoring**: Comprehensive health check endpoints
- **Performance Tracking**: Response time and throughput monitoring