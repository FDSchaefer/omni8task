# Medical Imaging Pipeline - Docker Deployment

Docker containerized medical imaging pipeline for atlas-based skull stripping.

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t mri-pipeline:latest .
```

### 2. Prepare Data Structure

```
project/
├── data/
│   ├── input/          # Place your MRI scans here
│   └── output/         # Results will be saved here
├── MNI_atlas/          # Download and extract MNI152 atlas here
└── config.yaml         # Optional configuration file
```

### 3. Download MNI152 Atlas

```bash
mkdir -p MNI_atlas
cd MNI_atlas
wget https://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_sym_09a_nifti.zip
unzip mni_icbm152_nlin_sym_09a_nifti.zip
cd ..
```

### 4. Run Processing

#### Using Docker Run

```bash
docker run --rm \
  -v $(pwd)/data/input:/data/input:ro \
  -v $(pwd)/data/output:/data/output \
  -v $(pwd)/MNI_atlas:/data/atlas:ro \
  mri-pipeline:latest \
  --input /data/input/subject.nii.gz \
  --output /data/output/skull_stripped.nii.gz \
  --report /data/output/quality_report.txt \
  --normalize zscore \
  --sigma 1.0 \
  --registration rigid
```

#### Using Docker Compose

Edit `docker-compose.yml` with your parameters, then:

```bash
docker-compose up
```

## Configuration Options

### Command Line Arguments

- `--input, -i`: Input image (NIFTI file or DICOM directory)
- `--output, -o`: Output skull-stripped image
- `--config, -c`: Configuration file (YAML/JSON)
- `--atlas-dir`: MNI152 atlas directory (default: /data/atlas)
- `--normalize`: Normalization method (zscore|minmax, default: zscore)
- `--sigma`: Gaussian smoothing sigma (default: 1.0)
- `--registration`: Registration type (rigid|affine, default: rigid)
- `--report`: Quality report output file
- `--save-intermediate`: Save intermediate processing results
- `--log-level`: Logging verbosity (DEBUG|INFO|WARNING|ERROR)

### Configuration File

Create a YAML or JSON file:

```yaml
normalize: zscore
sigma: 1.0
registration: rigid
```

Then use:

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/config.yaml:/config.yaml:ro \
  -v $(pwd)/MNI_atlas:/data/atlas:ro \
  mri-pipeline:latest \
  --input /data/input/subject.nii.gz \
  --output /data/output/result.nii.gz \
  --config /config.yaml
```

## Batch Processing

Process multiple images:

```bash
#!/bin/bash
for image in data/input/*.nii.gz; do
  basename=$(basename "$image" .nii.gz)
  docker run --rm \
    -v $(pwd)/data:/data \
    -v $(pwd)/MNI_atlas:/data/atlas:ro \
    mri-pipeline:latest \
    --input "/data/input/${basename}.nii.gz" \
    --output "/data/output/${basename}_skull_stripped.nii.gz" \
    --report "/data/output/${basename}_report.txt"
done
```

## Output Files

The pipeline generates:

1. **Skull-stripped image**: Main output with brain extracted
2. **Quality report** (optional): Text file with metrics
3. **Intermediate results** (optional): Preprocessed images

### Quality Report Contents

- Mask coverage percentage
- Brain volume (cm³)
- Connected components analysis
- Edge density metrics
- Intensity statistics
- Pass/fail status for quality checks

## Troubleshooting

### Atlas Not Found

Ensure MNI152 atlas is downloaded and mounted:

```bash
ls -la MNI_atlas/
# Should contain: mni_icbm152_t1_tal_nlin_sym_09a.nii and mask
```

### Permission Issues

If you encounter permission errors with output:

```bash
# Linux/Mac
docker run --rm --user $(id -u):$(id -g) ...

# Or fix permissions after processing
sudo chown -R $(id -u):$(id -g) data/output/
```

### Memory Issues

For large images, increase Docker memory:

```bash
docker run --rm --memory=8g ...
```

## Development

### Running Tests

```bash
docker run --rm \
  -v $(pwd)/tests:/app/tests \
  mri-pipeline:latest \
  python -m pytest tests/
```

### Interactive Shell

```bash
docker run --rm -it \
  -v $(pwd)/data:/data \
  -v $(pwd)/MNI_atlas:/data/atlas:ro \
  mri-pipeline:latest \
  /bin/bash
```

## Performance Notes

- Rigid registration: ~2-5 minutes per scan
- Affine registration: ~5-10 minutes per scan
- Processing time scales with image size
- Multi-core CPU recommended

## Support

For issues or questions, please check the documentation or contact support.
