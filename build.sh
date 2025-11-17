#!/bin/bash
# Build and run script for MRI pipeline

set -e

echo "=========================================="
echo "MRI Pipeline Docker Setup"
echo "=========================================="

# Check if atlas exists
if [ ! -d "MNI_atlas" ] || [ -z "$(ls -A MNI_atlas)" ]; then
    echo "Warning: MNI_atlas directory not found or empty"
    echo "Please download the atlas:"
    echo "  mkdir -p MNI_atlas"
    echo "  cd MNI_atlas"
    echo "  wget https://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_sym_09a_nifti.zip"
    echo "  unzip mni_icbm152_nlin_sym_09a_nifti.zip"
    exit 1
fi

# Create directories
mkdir -p data/input data/output

echo ""
echo "Building Docker image..."
docker build -t mri-pipeline:latest .

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo ""
echo "Usage examples:"
echo ""
echo "1. Process single file:"
echo "   docker run --rm \\"
echo "     -v \$(pwd)/data/input:/data/input:ro \\"
echo "     -v \$(pwd)/data/output:/data/output \\"
echo "     -v \$(pwd)/MNI_atlas:/data/atlas:ro \\"
echo "     mri-pipeline:latest \\"
echo "     --input /data/input/scan.nii.gz \\"
echo "     --output /data/output/result.nii.gz \\"
echo "     --report /data/output/report.txt"
echo ""
echo "2. Using docker-compose:"
echo "   Edit docker-compose.yml, then: docker-compose up"
echo ""
echo "3. View help:"
echo "   docker run --rm mri-pipeline:latest --help"
echo ""
