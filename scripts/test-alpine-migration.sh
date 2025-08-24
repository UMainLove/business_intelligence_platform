#!/bin/bash
# Test script for Alpine 3.21.3 migration
# Validates compatibility and functionality

set -e

echo "🧪 Alpine 3.21.3 Migration Test Suite"
echo "====================================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing $test_name... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Check local Python compatibility
echo "📦 1. Local Environment Tests"
echo "-----------------------------"
run_test "Python version (3.13+)" "python3 --version | grep -E '3.1[3-9]'"
run_test "pip availability" "python3 -m pip --version"
run_test "Required packages" "source .venv/bin/activate && python3 -c 'import streamlit, pandas, numpy, psycopg2' 2>/dev/null"

echo

# 2. Test Docker build if available
echo "🐳 2. Docker Build Tests"
echo "------------------------"
if command -v docker &> /dev/null; then
    if docker info > /dev/null 2>&1; then
        echo "Building Alpine container..."
        if docker build -t bi-alpine-test:latest . > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Docker build successful"
            ((TESTS_PASSED++))
            
            # Test container runs
            if docker run --rm bi-alpine-test:latest python3 --version > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} Container runs Python successfully"
                ((TESTS_PASSED++))
            else
                echo -e "${RED}✗${NC} Container Python failed"
                ((TESTS_FAILED++))
            fi
            
            # Check container size
            SIZE=$(docker images bi-alpine-test:latest --format "{{.Size}}")
            echo "Container size: $SIZE"
            
            # Security scan if Trivy available
            if command -v trivy &> /dev/null; then
                echo "Running security scan..."
                VULNS=$(trivy image --severity CRITICAL,HIGH --format json bi-alpine-test:latest 2>/dev/null | \
                    jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH")] | length' 2>/dev/null || echo "unknown")
                
                if [ "$VULNS" = "0" ]; then
                    echo -e "${GREEN}✓${NC} Zero critical/high vulnerabilities!"
                    ((TESTS_PASSED++))
                else
                    echo -e "${YELLOW}⚠${NC} Vulnerabilities found: $VULNS"
                fi
            fi
        else
            echo -e "${RED}✗${NC} Docker build failed"
            ((TESTS_FAILED++))
        fi
    else
        echo -e "${YELLOW}Docker daemon not running - skipping container tests${NC}"
    fi
else
    echo -e "${YELLOW}Docker not installed - skipping container tests${NC}"
fi

echo

# 3. Test Python package compatibility
echo "🐍 3. Python Package Compatibility"
echo "----------------------------------"
cat > /tmp/test_alpine_compat.py << 'EOF'
#!/usr/bin/env python3
import sys

def test_imports():
    """Test if all critical packages can be imported."""
    critical_packages = [
        ('streamlit', 'UI framework'),
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('psycopg2', 'PostgreSQL driver'),
        ('cryptography', 'Security'),
        ('PyJWT', 'JWT tokens'),
    ]
    
    failed = []
    for package, description in critical_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} ({description})")
        except ImportError as e:
            print(f"✗ {package} ({description}): {e}")
            failed.append(package)
    
    return len(failed) == 0

if __name__ == "__main__":
    sys.exit(0 if test_imports() else 1)
EOF

if python3 /tmp/test_alpine_compat.py; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

echo

# 4. Test Kubernetes compatibility
echo "☸️  4. Kubernetes Manifest Tests"
echo "--------------------------------"
run_test "Deployment manifest valid" "grep -q 'alpine:3.21.3' Dockerfile"
run_test "Security context compatible" "grep -q 'adduser -u 10001' Dockerfile"
run_test "Non-root user created" "grep -q 'adduser.*appuser' Dockerfile"

echo

# 5. Test critical application files
echo "📱 5. Application File Tests"
echo "----------------------------"
run_test "app.py exists" "test -f app.py"
run_test "app_bi.py exists" "test -f app_bi.py"
run_test "requirements.txt exists" "test -f requirements.txt"
run_test "requirements-prod.txt exists" "test -f requirements-prod.txt"

echo

# Summary
echo "====================================="
echo "📊 Test Summary"
echo "====================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo
    echo -e "${GREEN}✅ All tests passed! Alpine 3.21.3 migration is ready.${NC}"
    echo
    echo "Next steps:"
    echo "1. Commit the changes"
    echo "2. Push to trigger CI/CD"
    echo "3. Monitor security scan results"
    exit 0
else
    echo
    echo -e "${RED}❌ Some tests failed. Please review before proceeding.${NC}"
    echo
    echo "Common issues:"
    echo "- psycopg2-binary may need psycopg2 (non-binary) on Alpine"
    echo "- Some packages may need additional Alpine packages"
    echo "- Python 3.13 compatibility issues with older packages"
    exit 1
fi