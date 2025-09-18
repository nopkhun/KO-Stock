#!/bin/bash

# Deployment Testing Runner Script
# This script runs comprehensive deployment tests for the stock management system

set -e

echo "🚀 Starting Comprehensive Deployment Testing"
echo "=============================================="

# Check if required tools are available
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✅ All prerequisites are available"

# Install required Python packages if not available
echo "📦 Installing required Python packages..."
pip3 install requests psycopg2-binary > /dev/null 2>&1 || {
    echo "⚠️  Could not install Python packages. Please install manually:"
    echo "   pip3 install requests psycopg2-binary"
}

# Set up environment
echo "🔧 Setting up test environment..."

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Load production environment if available
if [ -f ".env.production" ]; then
    echo "📄 Loading production environment variables"
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Run the comprehensive deployment test
echo "🧪 Running deployment tests..."
echo ""

python3 scripts/comprehensive-deployment-test.py

# Check exit code
exit_code=$?

echo ""
echo "=============================================="

if [ $exit_code -eq 0 ]; then
    echo "✅ All deployment tests passed successfully!"
    echo "🎉 Your application is ready for production deployment"
elif [ $exit_code -eq 1 ]; then
    echo "⚠️  Some tests failed but core functionality works"
    echo "📋 Check deployment-test-report.json for details"
else
    echo "❌ Deployment tests failed"
    echo "📋 Check deployment-test-report.json and logs for details"
fi

echo ""
echo "📊 Test reports generated:"
echo "   - deployment-test-report.json (detailed results)"
echo "   - deployment-test-summary.txt (summary)"
echo "   - deployment-test.log (execution log)"

exit $exit_code