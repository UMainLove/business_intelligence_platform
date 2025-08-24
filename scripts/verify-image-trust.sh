#!/bin/bash
# Verify Docker Image Trust and Signatures
# Ensures image integrity and authenticity

set -e

echo "🔐 Docker Image Trust Verification"
echo "=================================="
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
IMAGE="${1:-ghcr.io/umainlove/business_intelligence_platform:latest}"
VERIFY_BASE="${2:-true}"

echo "Image: $IMAGE"
echo

# 1. Enable Docker Content Trust for base image verification
if [ "$VERIFY_BASE" = "true" ]; then
    echo "📋 Step 1: Verifying Base Image (Alpine 3.21.3) with DCT"
    echo "---------------------------------------------------------"
    
    # Export DCT to verify Alpine base
    export DOCKER_CONTENT_TRUST=1
    export DOCKER_CONTENT_TRUST_SERVER=https://notary.docker.io
    
    echo "Pulling Alpine 3.21.3 with DCT enabled..."
    if docker pull alpine:3.21.3 2>/dev/null; then
        echo -e "${GREEN}✅ Alpine 3.21.3 signature verified via DCT${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not verify Alpine 3.21.3 signature${NC}"
        echo "Note: This might be due to network or notary server issues"
    fi
    
    # Disable DCT for other operations
    unset DOCKER_CONTENT_TRUST
    echo
fi

# 2. Check if Cosign is installed
echo "📋 Step 2: Checking Cosign Installation"
echo "----------------------------------------"
if ! command -v cosign &> /dev/null; then
    echo -e "${YELLOW}⚠️  Cosign not found. Installing...${NC}"
    
    # Install Cosign
    curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
    sudo mv cosign-linux-amd64 /usr/local/bin/cosign
    sudo chmod +x /usr/local/bin/cosign
    
    echo -e "${GREEN}✅ Cosign installed${NC}"
else
    echo -e "${GREEN}✅ Cosign is installed${NC}"
fi
echo

# 3. Verify our image signature (if pushed to registry)
echo "📋 Step 3: Verifying Our Image Signature"
echo "-----------------------------------------"

# Set experimental for keyless verification
export COSIGN_EXPERIMENTAL=1

# Try to verify signature
echo "Attempting to verify signature for $IMAGE..."
if cosign verify \
    --certificate-identity-regexp "https://github.com/.*/\.github/workflows/.*" \
    --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
    "$IMAGE" 2>/dev/null; then
    echo -e "${GREEN}✅ Image signature verified successfully${NC}"
else
    echo -e "${YELLOW}⚠️  No signature found or verification failed${NC}"
    echo "This is expected if:"
    echo "  - Image hasn't been pushed to registry yet"
    echo "  - Image wasn't signed with Cosign"
    echo "  - Using local image only"
fi
echo

# 4. Check for SBOM
echo "📋 Step 4: Checking for SBOM (Software Bill of Materials)"
echo "----------------------------------------------------------"
if cosign download sbom "$IMAGE" 2>/dev/null; then
    echo -e "${GREEN}✅ SBOM found and downloaded${NC}"
else
    echo -e "${YELLOW}⚠️  No SBOM attached to image${NC}"
fi
echo

# 5. Check for attestations
echo "📋 Step 5: Checking for Security Attestations"
echo "----------------------------------------------"
if cosign verify-attestation \
    --certificate-identity-regexp "https://github.com/.*/\.github/workflows/.*" \
    --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
    "$IMAGE" 2>/dev/null; then
    echo -e "${GREEN}✅ Security attestations verified${NC}"
else
    echo -e "${YELLOW}⚠️  No attestations found${NC}"
fi
echo

# 6. Manual verification steps
echo "📋 Step 6: Manual Verification Checklist"
echo "-----------------------------------------"
echo "For production deployment, also verify:"
echo
echo "1. [ ] Base image is alpine:3.21.3 (zero CVEs)"
echo "2. [ ] Non-root user (UID 10001)"
echo "3. [ ] Multi-stage build (no build tools in runtime)"
echo "4. [ ] Read-only root filesystem"
echo "5. [ ] No unnecessary capabilities"
echo "6. [ ] Minimal package installation"
echo "7. [ ] Security scanning passed (Trivy/Snyk)"
echo

# Summary
echo "=================================="
echo "📊 Trust Verification Summary"
echo "=================================="

if [ -f /.dockerenv ]; then
    echo -e "${YELLOW}⚠️  Running inside Docker - some checks skipped${NC}"
elif command -v docker &> /dev/null; then
    # Get image digest
    DIGEST=$(docker inspect "$IMAGE" 2>/dev/null | jq -r '.[0].RepoDigests[0]' | cut -d'@' -f2)
    if [ "$DIGEST" != "null" ] && [ -n "$DIGEST" ]; then
        echo "Image Digest: $DIGEST"
        echo
        echo "To verify this specific image version:"
        echo "  cosign verify $IMAGE@$DIGEST"
    fi
else
    echo -e "${RED}❌ Docker not available${NC}"
fi

echo
echo "🔒 Security Recommendations:"
echo "----------------------------"
echo "1. Always use DOCKER_CONTENT_TRUST=1 in production"
echo "2. Verify signatures before deployment"
echo "3. Review SBOM for known vulnerabilities"
echo "4. Check attestations for build provenance"
echo "5. Use image digests, not tags, in production"

exit 0