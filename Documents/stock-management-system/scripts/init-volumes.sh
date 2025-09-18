#!/bin/bash

# Initialize volumes and directories for Docker Compose deployment
# This script ensures proper permissions and directory structure

set -e

echo "Initializing Docker volumes and directories..."

# Create data directories if they don't exist
mkdir -p data/postgres
mkdir -p logs

# Set proper permissions for PostgreSQL data directory
# PostgreSQL container runs as user 999:999
if [ "$(id -u)" = "0" ]; then
    # Running as root
    chown -R 999:999 data/postgres
    chmod 700 data/postgres
else
    # Running as non-root user
    echo "Warning: Not running as root. You may need to manually set permissions:"
    echo "  sudo chown -R 999:999 data/postgres"
    echo "  sudo chmod 700 data/postgres"
fi

# Create log directories with proper permissions
chmod 755 logs

echo "Volume initialization complete!"
echo ""
echo "To deploy with Dokploy, use one of these commands:"
echo "  # Standard deployment:"
echo "  docker-compose up -d"
echo ""
echo "  # Production deployment:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo "  # Dokploy-specific deployment:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.dokploy.yml up -d"