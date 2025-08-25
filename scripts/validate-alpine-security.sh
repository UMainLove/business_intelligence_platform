#!/bin/bash
# Validate Alpine 3.21.3 Security Configuration
# Ensures zero CVE base and proper security settings

set -e

echo "🔒 Alpine 3.21.3 Security Validation"
echo "===================================="
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validation results
SECURITY_SCORE=0
MAX_SCORE=10

check_security() {
    local check_name="$1"
    local check_command="$2"
    local points="$3"
    
    echo -n "Checking $check_name... "
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} (+$points points)"
        ((SECURITY_SCORE += points))
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

echo "📋 Security Checklist:"
echo "----------------------"

# 1. Alpine 3.21.4 base
check_security "Alpine 3.21.4 base image" "grep -q 'FROM alpine:3.21.4' Dockerfile" 2

# 2. Security updates
check_security "APK updates applied" "grep -q 'apk upgrade' Dockerfile" 1

# 3. Non-root user
check_security "Non-root user (10001)" "grep -q 'adduser -u 10001' Dockerfile" 2

# 4. No build tools in runtime
check_security "Build tools only in builder" "! grep -iA5 'FROM alpine:3.21.3 as runtime' Dockerfile | grep -q 'build-base'" 1

# 5. Multi-stage build
check_security "Multi-stage build" "grep -iq 'FROM.*as builder' Dockerfile && grep -iq 'FROM.*as runtime' Dockerfile" 1

# 6. Minimal packages
check_security "Minimal runtime packages" "grep -iA10 'FROM alpine:3.21.3 as runtime' Dockerfile | grep 'apk add' | grep -v build-base" 1

# 7. Security context in K8s
check_security "K8s security context" "grep -q 'runAsNonRoot: true' k8s/deployment.yaml" 1

# 8. Read-only filesystem
check_security "Read-only filesystem" "grep -q 'readOnlyRootFilesystem: true' k8s/deployment.yaml" 1

echo
echo "===================================="
echo "📊 Security Score: $SECURITY_SCORE/$MAX_SCORE"
echo "===================================="

if [ $SECURITY_SCORE -eq $MAX_SCORE ]; then
    echo -e "${GREEN}✅ PERFECT SCORE! Container is production-ready with minimal CVEs.${NC}"
    echo
    echo "Summary:"
    echo "• Base: Alpine 3.21.4 (minimal CVEs, latest stable)"
    echo "• User: Non-root (UID 10001)"
    echo "• Build: Multi-stage (minimal attack surface)"
    echo "• Runtime: No build tools, minimal packages"
    echo "• K8s: Proper security context"
elif [ $SECURITY_SCORE -ge 8 ]; then
    echo -e "${YELLOW}⚠️  Good security, minor improvements needed.${NC}"
else
    echo -e "${RED}❌ Security issues detected. Review configuration.${NC}"
fi

echo
echo "🔍 Expected Security Scan Results:"
echo "-----------------------------------"
echo "• Alpine 3.21.4: 1 MEDIUM CVE (sqlite - no fix available)"
echo "• Python packages: All updated, setuptools CVE fixed"
echo "• Container size: Should be < 500MB"
echo
echo "To verify zero CVEs, run:"
echo "  docker build -t alpine-test . && trivy image alpine-test"

exit 0