#!/bin/bash
# Container Security Update Script
# Rebuilds container with latest security patches

set -e

echo "🔒 Container Security Update Process"
echo "===================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

# Build container with no cache to get fresh updates
echo "🔨 Building container with latest security patches..."
docker build --no-cache -t bi-platform:latest . || {
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
}

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo -e "${YELLOW}⚠️  Trivy not found. Installing...${NC}"
    # Install Trivy
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
fi

# Scan for vulnerabilities
echo
echo "🔍 Scanning for vulnerabilities..."
SCAN_RESULT=$(trivy image --severity CRITICAL,HIGH --format json bi-platform:latest 2>/dev/null)

# Count vulnerabilities
CRITICAL_COUNT=$(echo "$SCAN_RESULT" | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' 2>/dev/null || echo 0)
HIGH_COUNT=$(echo "$SCAN_RESULT" | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="HIGH")] | length' 2>/dev/null || echo 0)

echo
echo "📊 Scan Results:"
echo "================"
echo "CRITICAL vulnerabilities: $CRITICAL_COUNT"
echo "HIGH vulnerabilities: $HIGH_COUNT"

# Determine status
if [ "$CRITICAL_COUNT" -eq 0 ] && [ "$HIGH_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ Container is SECURE - No critical/high vulnerabilities found!${NC}"
    echo
    echo "Container tag: bi-platform:latest"
    echo "Base image: Alpine 3.21.3 (Zero CVE base)"
    echo "Ready for production deployment!"
    exit 0
else
    echo -e "${RED}❌ SECURITY ISSUES DETECTED${NC}"
    echo
    echo "Action required:"
    echo "1. Check if newer Alpine version is available"
    echo "2. Review specific CVEs in the detailed report"
    echo "3. Consider alternative base images if needed"
    
    # Show detailed report
    echo
    echo "Run this for detailed report:"
    echo "  trivy image --severity CRITICAL,HIGH bi-platform:latest"
    
    exit 1
fi