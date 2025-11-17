#!/bin/bash
# Batch process multiple MRI scans

set -e

INPUT_DIR="data/input"
OUTPUT_DIR="data/output"
ATLAS_DIR="MNI_atlas"

# Configuration
NORMALIZE="zscore"
SIGMA="1.0"
REGISTRATION="rigid"

echo "=========================================="
echo "Batch Processing MRI Scans"
echo "=========================================="
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Count images
count=$(find "$INPUT_DIR" -name "*.nii.gz" -o -name "*.nii" | wc -l)
echo "Found $count images to process"
echo ""

# Process each image
current=0
for image in "$INPUT_DIR"/*.nii.gz "$INPUT_DIR"/*.nii; do
    # Skip if no files match
    [ -e "$image" ] || continue
    
    current=$((current + 1))
    basename=$(basename "$image")
    filename="${basename%.*}"
    filename="${filename%.*}"  # Handle .nii.gz
    
    echo "[$current/$count] Processing: $basename"
    
    docker run --rm \
        -v "$(pwd)/$INPUT_DIR:/data/input:ro" \
        -v "$(pwd)/$OUTPUT_DIR:/data/output" \
        -v "$(pwd)/$ATLAS_DIR:/data/atlas:ro" \
        mri-pipeline:latest \
        --input "/data/input/$basename" \
        --output "/data/output/${filename}_skull_stripped.nii.gz" \
        --report "/data/output/${filename}_report.txt" \
        --normalize "$NORMALIZE" \
        --sigma "$SIGMA" \
        --registration "$REGISTRATION" \
        --log-level WARNING
    
    echo "  Completed: ${filename}_skull_stripped.nii.gz"
    echo ""
done

echo "=========================================="
echo "Batch processing complete!"
echo "Results saved to: $OUTPUT_DIR"
echo "=========================================="
