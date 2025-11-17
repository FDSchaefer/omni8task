#!/bin/bash
# Test script for Docker deployment

set -e

echo "=========================================="
echo "Docker Deployment Test Suite"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    FAILED=$((FAILED + 1))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
}

# Test 1: Check Docker is installed
echo "Test 1: Docker installation"
if command -v docker &> /dev/null; then
    pass "Docker is installed"
else
    fail "Docker is not installed"
    exit 1
fi

# Test 2: Check directory structure
echo "Test 2: Directory structure"
if [ -d "src" ]; then
    pass "src/ directory exists"
else
    fail "src/ directory not found"
fi

if [ -f "Dockerfile" ]; then
    pass "Dockerfile exists"
else
    fail "Dockerfile not found"
fi

if [ -f "requirements.txt" ]; then
    pass "requirements.txt exists"
else
    fail "requirements.txt not found"
fi

if [ -f "process_mri.py" ]; then
    pass "process_mri.py exists"
else
    fail "process_mri.py not found"
fi

# Test 3: Check source files
echo "Test 3: Source files"
for file in utils.py preprocessing.py registration.py quality_assessment.py; do
    if [ -f "src/$file" ]; then
        pass "src/$file exists"
    else
        warn "src/$file not found (may be optional)"
    fi
done

# Test 4: Check atlas
echo "Test 4: MNI152 Atlas"
if [ -d "MNI_atlas" ] && [ "$(ls -A MNI_atlas)" ]; then
    pass "MNI_atlas directory exists and is not empty"
else
    warn "MNI_atlas not found or empty - download required"
    echo "      Download: https://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_sym_09a_nifti.zip"
fi

# Test 5: Try building image
echo "Test 5: Docker image build"
echo "Building image (this may take a few minutes)..."
if docker build -t mri-pipeline:test -f Dockerfile . &> /tmp/docker_build.log; then
    pass "Docker image built successfully"
else
    fail "Docker image build failed"
    echo "Check log: /tmp/docker_build.log"
    cat /tmp/docker_build.log
fi

# Test 6: Check image exists
echo "Test 6: Docker image"
if docker images | grep -q "mri-pipeline"; then
    pass "Docker image is available"
else
    fail "Docker image not found"
fi

# Test 7: Test help command
echo "Test 7: Container help command"
if docker run --rm mri-pipeline:test --help &> /dev/null; then
    pass "Container runs and shows help"
else
    fail "Container failed to run"
fi

# Test 8: Check data directories
echo "Test 8: Data directories"
mkdir -p data/input data/output

if [ -d "data/input" ] && [ -d "data/output" ]; then
    pass "Data directories exist"
else
    fail "Failed to create data directories"
fi

# Test 9: Check Python syntax
echo "Test 9: Python syntax check"
if python3 -m py_compile process_mri.py &> /dev/null; then
    pass "process_mri.py syntax is valid"
else
    fail "process_mri.py has syntax errors"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Place MRI scans in data/input/"
    echo "2. Run: docker run --rm \\"
    echo "     -v \$(pwd)/data/input:/data/input:ro \\"
    echo "     -v \$(pwd)/data/output:/data/output \\"
    echo "     -v \$(pwd)/MNI_atlas:/data/atlas:ro \\"
    echo "     mri-pipeline:test \\"
    echo "     --input /data/input/scan.nii.gz \\"
    echo "     --output /data/output/result.nii.gz"
    echo ""
    exit 0
else
    echo -e "${RED}Some tests failed. Please fix issues before proceeding.${NC}"
    exit 1
fi
