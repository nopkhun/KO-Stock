# Dokploy Deployment Quick Fix

## Issues Fixed

1. **Removed obsolete `version` attribute** from Docker Compose files
2. **Fixed network connectivity issues** by removing static IP assignments
3. **Simplified network configuration** to use Docker's default networking
4. **Updated service communication** to use service names instead of IP addresses

## Files Modified

- `docker-compose.yml` - Removed version attribute and static IPs
- `docker-compose.dokploy.yml` - Removed version attribute
- `docker-compose.dokploy-clean.yml` - New clean file for Dokploy deployment

## Quick Deployment Steps

### Option 1: Use the Clean Dokploy File (Recommended)

```bash
# Use the clean Dokploy-optimized compose file
cp docker-compose.dokploy-clean.yml docker-compose.yml
```

### Option 2: Use the Fixed Original File

The original `docker-compose.yml` has been fixed and should work with Dokploy.

## Key Changes Made

### Network Configuration
- **Before**: Static IP assignments (172.20.0.10, 172.20.0.20, 172.20.0.30)
- **After**: Service discovery using service names (`database`, `backend`, `frontend`)

### Database Connection
- **Before**: `postgresql://postgres:password@172.20.0.10:5432/db`
- **After**: `postgresql://postgres:password@database:5432/db`

### Docker Compose Version
- **Before**: `version: '3.8'` (obsolete)
- **After**: No version attribute (modern format)

## Environment Variables for Dokploy

Set these in Dokploy's environment variables interface:

```bash
# Required
SECRET_KEY=your-32-plus-character-secret-key
POSTGRES_PASSWORD=your-secure-database-password

# Database (use service name)
DATABASE_URL=postgresql://postgres:your-password@database:5432/stock_management

# Security (for HTTPS domains)
SESSION_COOKIE_SECURE=true
CORS_ORIGINS=https://yourdomain.com

# Optional
FLASK_ENV=production
DEBUG=false
```

## Troubleshooting

If you still encounter network issues:

1. **Check Dokploy logs** for network creation errors
2. **Verify service names** are resolving correctly
3. **Ensure no port conflicts** with other applications
4. **Check Dokploy's network management** settings

## Testing the Fix

After deployment, verify:

```bash
# Check if services can communicate
docker exec -it <backend-container> ping database
docker exec -it <frontend-container> curl http://backend:5000/api/health
```

## Next Steps

1. Deploy using the fixed compose file
2. Monitor the deployment logs
3. Verify all services start successfully
4. Test the application functionality