# Final Integration Testing Guide

This document describes the comprehensive testing suite for validating the Stock Management System's readiness for Dokploy deployment.

## Overview

The final integration testing consists of two main phases:

1. **Comprehensive Deployment Testing** - Validates the complete stack deployment
2. **Dokploy Compatibility Testing** - Ensures compatibility with Dokploy platform

## Test Scripts

### 1. Comprehensive Deployment Test (`scripts/comprehensive-deployment-test.py`)

Tests the following aspects:

- **Docker Compose Deployment**: Validates complete stack deployment
- **Service Health Checks**: Tests all health check endpoints
- **Database Connectivity**: Verifies database connection and operations
- **API Endpoints**: Tests key API functionality
- **Frontend Accessibility**: Validates frontend serving and static assets
- **Database Persistence**: Tests data persistence and integrity
- **Service Restart Resilience**: Validates service recovery after restart

### 2. Dokploy Compatibility Test (`scripts/dokploy-compatibility-test.py`)

Tests the following Dokploy-specific features:

- **Environment Variable Injection**: Tests environment variable handling through Dokploy
- **Service Discovery & Networking**: Validates internal service communication
- **Persistent Volume Mounting**: Tests volume mounting and data persistence
- **Dokploy-Specific Configurations**: Validates Dokploy-friendly settings
- **Container Orchestration**: Tests service dependencies and startup order
- **Health Check Integration**: Validates health check endpoints for monitoring

## Running the Tests

### Prerequisites

1. Docker and Docker Compose installed
2. Python 3.x with pip
3. Required Python packages (automatically installed by test scripts)

### Quick Start

Run the complete test suite:

```bash
./scripts/run-final-integration-tests.sh
```

### Individual Test Execution

Run deployment tests only:
```bash
python3 scripts/comprehensive-deployment-test.py
```

Run Dokploy compatibility tests only:
```bash
python3 scripts/dokploy-compatibility-test.py
```

## Test Reports

After running tests, the following reports are generated:

### Deployment Test Reports
- `deployment-test-report.json` - Detailed test results in JSON format
- `deployment-test-summary.txt` - Human-readable summary
- `deployment-test.log` - Execution log with timestamps

### Dokploy Compatibility Reports
- `dokploy-compatibility-report.json` - Detailed compatibility results
- `dokploy-compatibility-summary.txt` - Human-readable summary
- `dokploy-compatibility-test.log` - Execution log

### Combined Report
- `final-integration-test-summary.txt` - Overall test results and next steps

## Test Results Interpretation

### Exit Codes
- `0` - All tests passed successfully
- `1` - Some tests failed (partial success)
- `2` - All tests failed
- `3` - Test execution interrupted
- `4` - Test execution error

### Status Values
- **PASS** - Test completed successfully
- **FAIL** - Test failed with errors
- **SKIP** - Test skipped (e.g., missing dependencies)
- **ERROR** - Test execution error
- **PARTIAL** - Test partially successful

## Troubleshooting

### Common Issues

1. **Docker not running**
   - Ensure Docker Desktop is running
   - Check Docker daemon status

2. **Port conflicts**
   - Stop other services using ports 80, 5000, or 5432
   - Use `docker-compose down` to stop existing containers

3. **Python dependencies missing**
   - Install requirements: `pip3 install -r scripts/test-requirements.txt`
   - On macOS, psycopg2 issues are handled gracefully (database tests will be skipped)

4. **Environment variables not set**
   - Copy `.env.example` to `.env` and configure values
   - Ensure `.env.production` exists with production settings

### Database Connection Issues

If database tests fail:
1. Check if PostgreSQL container is running
2. Verify database credentials in environment variables
3. Ensure database initialization completed successfully

### Network Issues

If service discovery tests fail:
1. Check Docker network configuration
2. Verify all services are running
3. Test manual connectivity between containers

## Pre-Deployment Checklist

Before deploying to Dokploy, ensure:

- [ ] All deployment tests pass
- [ ] All Dokploy compatibility tests pass
- [ ] Environment variables are properly configured
- [ ] Persistent volumes are correctly set up
- [ ] Health checks respond correctly
- [ ] Service networking functions properly
- [ ] Database persistence works as expected

## Dokploy Deployment Steps

Once all tests pass:

1. **Upload Project**: Upload the project to your Dokploy instance
2. **Configure Environment**: Set environment variables in Dokploy interface
3. **Set Up Volumes**: Configure persistent volumes for database storage
4. **Deploy Stack**: Use the docker-compose.yml file for deployment
5. **Monitor Health**: Check health endpoints and logs after deployment
6. **Validate Functionality**: Test the application functionality post-deployment

## Continuous Testing

For ongoing development:

1. Run tests before each deployment
2. Include tests in CI/CD pipeline
3. Monitor test results and address failures promptly
4. Update tests as new features are added

## Support

If tests continue to fail after troubleshooting:

1. Check the detailed JSON reports for specific error messages
2. Review the execution logs for additional context
3. Verify all prerequisites are met
4. Ensure the latest configuration files are being used

For Dokploy-specific issues, consult the Dokploy documentation and ensure your configuration matches the platform requirements.