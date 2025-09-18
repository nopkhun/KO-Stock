# Dokploy Network Connectivity Troubleshooting

## Current Error
```
Error response from daemon: container 059294ebc1391ac4f668cc4ea33420d893824f53802082ef10a56e3ed2921a44 is not connected to the network kostock-kostock-shg4ih_stock_management_network
```

## Root Cause
Dokploy is trying to connect containers to a custom network that either:
1. Doesn't exist
2. Wasn't created properly
3. Has naming conflicts with the project structure

## Solutions (Try in Order)

### Solution 1: Use Minimal Compose File (Recommended)
```bash
# Use the network-free compose file
cp docker-compose.minimal.yml docker-compose.yml
```

### Solution 2: Clean Up Dokploy Project
1. **Stop and remove the current deployment** in Dokploy
2. **Delete the project** completely
3. **Create a new project** with a simpler name (e.g., "kostock")
4. **Deploy with the updated compose file**

### Solution 3: Manual Network Cleanup
If you have access to the server:

```bash
# List all networks
docker network ls

# Remove the problematic network (if it exists)
docker network rm kostock-kostock-shg4ih_stock_management_network

# Remove all stopped containers
docker container prune -f

# Remove unused networks
docker network prune -f
```

### Solution 4: Force Recreate in Dokploy
1. Go to your Dokploy project
2. **Stop all services**
3. **Remove all containers** (if option available)
4. **Redeploy** with the updated compose file

## Updated Compose Files Available

1. **docker-compose.yml** - Updated with no custom networks
2. **docker-compose.minimal.yml** - Minimal version with only essential configs
3. **docker-compose.dokploy-clean.yml** - Clean version for Dokploy

## Environment Variables to Set in Dokploy

```bash
# Required
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-32-character-secret-key

# Database connection (using service name)
DATABASE_URL=postgresql://postgres:your-password@database:5432/stock_management

# Optional
FLASK_ENV=production
DEBUG=false
```

## Verification Steps

After deployment, check:

1. **Container Status**: All containers should be running
2. **Network Connectivity**: Services should communicate via service names
3. **Health Checks**: All health checks should pass
4. **Logs**: No network-related errors in logs

## If Still Failing

1. **Check Dokploy logs** for network creation errors
2. **Verify Docker version** compatibility
3. **Contact Dokploy support** with the specific error message
4. **Consider using Docker Swarm mode** if available in Dokploy

## Prevention

- Always use service names for inter-service communication
- Avoid custom network configurations in Dokploy
- Let Dokploy manage networking automatically
- Use minimal compose files for better compatibility