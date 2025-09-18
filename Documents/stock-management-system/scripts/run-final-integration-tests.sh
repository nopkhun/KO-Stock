#!/bin/bash

# Final Integration Testing Runner
# Runs both comprehensive deployment tests and Dokploy compatibility tests

set -e

echo "🚀 Starting Final Integration Testing Suite"
echo "=============================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if required tools are available
for tool in docker docker-compose python3; do
    if ! command -v $tool &> /dev/null; then
        echo "❌ $tool is not installed or not in PATH"
        exit 1
    fi
done

echo "✅ All prerequisites are available"
echo ""

# Set up environment
echo "🔧 Setting up test environment..."

# Load environment variables
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file"
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -f ".env.production" ]; then
    echo "📄 Loading production environment variables"
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Install Python dependencies if needed
echo "📦 Ensuring Python dependencies are available..."
pip3 install -r scripts/test-requirements.txt > /dev/null 2>&1 || {
    echo "⚠️  Could not install Python packages. Please install manually:"
    echo "   pip3 install -r scripts/test-requirements.txt"
}

echo ""

# Run comprehensive deployment tests
echo "🧪 Phase 1: Comprehensive Deployment Testing"
echo "=============================================="
echo ""

python3 scripts/comprehensive-deployment-test.py
deployment_exit_code=$?

echo ""

# Run Dokploy compatibility tests
echo "🔧 Phase 2: Dokploy Compatibility Testing"
echo "=========================================="
echo ""

python3 scripts/dokploy-compatibility-test.py
dokploy_exit_code=$?

echo ""

# Generate combined report
echo "📊 Generating Combined Test Report"
echo "=================================="

# Create combined summary
cat > final-integration-test-summary.txt << EOF
FINAL INTEGRATION TEST SUMMARY
==============================
Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

TEST PHASES:
-----------
Phase 1 - Comprehensive Deployment: $([ $deployment_exit_code -eq 0 ] && echo "PASSED" || echo "FAILED")
Phase 2 - Dokploy Compatibility: $([ $dokploy_exit_code -eq 0 ] && echo "PASSED" || echo "FAILED")

OVERALL STATUS: $([ $deployment_exit_code -eq 0 ] && [ $dokploy_exit_code -eq 0 ] && echo "PASSED" || echo "FAILED")

DETAILED REPORTS:
----------------
- deployment-test-report.json (Deployment test details)
- deployment-test-summary.txt (Deployment test summary)
- dokploy-compatibility-report.json (Dokploy compatibility details)
- dokploy-compatibility-summary.txt (Dokploy compatibility summary)
- deployment-test.log (Deployment test execution log)
- dokploy-compatibility-test.log (Dokploy test execution log)

NEXT STEPS:
----------
EOF

# Add next steps based on results
if [ $deployment_exit_code -eq 0 ] && [ $dokploy_exit_code -eq 0 ]; then
    cat >> final-integration-test-summary.txt << EOF
✅ All tests passed! Your application is ready for Dokploy deployment.

Deployment checklist:
1. Upload your project to Dokploy
2. Configure environment variables in Dokploy interface
3. Set up persistent volumes for database storage
4. Deploy the stack using docker-compose.yml
5. Monitor health checks and logs after deployment

EOF
elif [ $deployment_exit_code -eq 0 ]; then
    cat >> final-integration-test-summary.txt << EOF
⚠️  Deployment tests passed but Dokploy compatibility needs attention.

Actions needed:
1. Review dokploy-compatibility-report.json for specific issues
2. Fix configuration issues identified in the compatibility tests
3. Re-run the Dokploy compatibility tests
4. Proceed with deployment once all tests pass

EOF
elif [ $dokploy_exit_code -eq 0 ]; then
    cat >> final-integration-test-summary.txt << EOF
⚠️  Dokploy compatibility passed but deployment tests failed.

Actions needed:
1. Review deployment-test-report.json for specific issues
2. Fix deployment configuration issues
3. Re-run the comprehensive deployment tests
4. Proceed with Dokploy deployment once all tests pass

EOF
else
    cat >> final-integration-test-summary.txt << EOF
❌ Both test phases failed. Significant issues need to be addressed.

Actions needed:
1. Review both test reports for detailed error information
2. Fix deployment and configuration issues
3. Re-run both test suites
4. Do not proceed with production deployment until all tests pass

EOF
fi

echo ""
echo "=============================================="
echo "FINAL INTEGRATION TESTING COMPLETED"
echo "=============================================="

# Display results
if [ $deployment_exit_code -eq 0 ] && [ $dokploy_exit_code -eq 0 ]; then
    echo "✅ ALL TESTS PASSED!"
    echo "🎉 Your application is ready for Dokploy deployment"
    final_exit_code=0
elif [ $deployment_exit_code -eq 0 ] || [ $dokploy_exit_code -eq 0 ]; then
    echo "⚠️  PARTIAL SUCCESS"
    echo "📋 Some tests passed, check reports for details"
    final_exit_code=1
else
    echo "❌ TESTS FAILED"
    echo "📋 Check reports and logs for detailed error information"
    final_exit_code=2
fi

echo ""
echo "📊 Test reports and logs:"
echo "   - final-integration-test-summary.txt (this summary)"
echo "   - deployment-test-report.json"
echo "   - dokploy-compatibility-report.json"
echo "   - *.log files for execution details"

exit $final_exit_code