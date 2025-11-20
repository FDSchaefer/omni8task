# MRI Skull Stripping Pipeline
> Atlas-based brain extraction within the context of neurological MRI preprocessing

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project is a production-ready Python pipeline for automated skull stripping of T1-weighted MRI scans using atlas-based registration. This tool implements preprocessing, registration, and quality assessment workflows. With a functional docker deployment, for immidate use in a production context.

**Key Features:**
- Atlas-based skull stripping using MNI152 template
- Flexible preprocessing (Z-score/min-max normalization, Gaussian smoothing)
- Rigid and affine registration options
- Automated quality assessment with JSON reports
- Interactive and lightweight visualization tools
- Complete Docker integration for production deployment
- Comprehensive unit tests

---

## Table of Contents


---

## Installation

### Prerequisites
- Python 3.11 or higher

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd omni8task
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **MNI152 atlas:**
A stripped down version of the atlas exists within the repository (T1 Only)
If the entire atlas is required see following commands and point the config to the unzip location: 

```bash
mkdir -p MNI_atlas
cd MNI_atlas
wget http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_sym_09a_nifti.zip
unzip mni_icbm152_nlin_sym_09a_nifti.zip
cd ..
```

---

## Docker Deployment

### Production Context

In clinical environments, MRI processing pipelines need to run continuously and reliably across different hospital IT infrastructures. Docker solves several real-world problems:

**Infrastructure independence:** Hospitals use diverse systems (Windows servers, Linux clusters, cloud VMs). Docker ensures the pipeline runs identically everywhere without dependency conflicts or manual configuration.

**Continuous processing:** MRI scanners produce images throughout the day. The watch mode container monitors an input directory and automatically processes new scans as they arrive - no manual intervention needed. This matches the actual workflow where technologists save scans to a shared folder and expect automated processing.

**Isolation and safety:** Medical systems require strict separation from other hospital IT. Containerization provides process isolation, preventing pipeline failures from affecting other systems and vice versa.

**Easy deployment:** A single `docker compose up` command deploys the entire pipeline. IT departments can integrate this into their PACS/RIS infrastructure without installing Python, dependencies, or downloading atlases manually.

### Workflow Integration

A typical deployment scenario:
1. Hospital IT mounts a shared network drive to `/data/input`
2. MRI technologists save scans to this directory (standard PACS export)
3. Docker container detects new files and processes automatically
4. Results appear in `/data/output` for clinicians or downstream systems
5. Container logs provide audit trail for quality assurance

This eliminates the batch processing bottleneck - scans are processed as soon as they arrive rather than waiting for someone to manually trigger batch jobs.

### Running the Container

**Plug and Play:**
```bash
bash POC_Stage4.sh
```

This script demonstrates the default configuration running in watch mode. The container will:
- Process any existing scans in `./data/input`
- Continue monitoring for new files
- Save results to `./data/output`
- Generate quality reports for each scan

**Configuration:**
The `docker-compose.yml` and `docker_config.json` files define the default behavior. Modify these to adjust preprocessing parameters, atlas location, or enable/disable watch mode.

**Image details:**
- Base: Python 3.11-slim (minimal footprint)
- MNI152 atlas downloaded during build (no runtime dependencies)
- Restarts automatically if crashed (production reliability)

See `Dockerfile` for build details and `docker-compose.yml` for service configuration.

---

## CLI Usage

Process a single MRI scan:
```bash
python pipeline_CLI.py \
  --input data/sample_data/test_sample.nii \
  --output results/brain_extracted.nii.gz
```

**Expected output:**
- `results/brain_extracted.nii.gz` - Skull-stripped brain
- `results/brain_extracted_quality_report.json` - Quality metrics

For A comprehensive understanding of its usage please read|run POC_Stage3_CLI.py

---

## Usage

### Single File Processing

**Basic usage:**
```bash
python process_mri.py --input scan.nii.gz --output result.nii.gz
```

**With custom parameters:**
Note that any values not set will be drawn from: data/config/config.json

```bash
python process_mri.py \
  --input scan.nii.gz \
  --output result.nii.gz \
  --sigma 1.5 \
  --normalize minmax \
  --registration affine
```

**Available parameters:**
| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| `--sigma` | 0.5-2.0 | 1.0 | Gaussian smoothing sigma |
| `--normalize` | zscore, minmax | zscore | Normalization method |
| `--registration` | rigid, affine | rigid | Registration type |
| `--mask-target` | processed, original | processed | Apply mask to preprocessed or original image |

### Batch Processing

Process multiple files in a directory:

```bash
python src/pipeline.py \
  --input-dir ./data/input \
  --output-dir ./data/output \
  --config ./data/config/config.json
```

**Configuration file (`config.json`):**
```json
{
  "normalize_method": "zscore",
  "gaussian_sigma": 1.0,
  "registration_type": "rigid",
  "mask_target": "processed",
  "atlas_dir": "./MNI_atlas",
  "log_level": "INFO"
}
```

### Watch Mode

Continuously monitor a directory for new scans:

```bash
python src/pipeline.py \
  --input-dir ./data/input \
  --output-dir ./data/output \
  --config ./data/config/config.json \
  --watch
```

This mode is the recomended approch for production environments where scans arrive dynamically.
The user is able to drop files they need processed, without the need for running python code (if docker hosted)

---

## Pipeline Architecture

**Data flow:**
1. Load input MRI (NIFTI/DICOM) and MNI152 atlas
2. Normalize intensities (Z-score or min-max)
3. Apply Gaussian smoothing (σ=1.0 default)
4. Register to atlas space using SimpleITK (rigid/affine)
5. Apply brain mask to extract brain region (from preprocessed image or original image)
6. Transform result back to original space
7. Save skull-stripped output + quality report

---
## Development Approach
I took the aproch of building in Proof of Concept Stages (POC_STAGE).
This means that I would construct a working version of a submodule, that is able to perform the required tasks to an acceptable level. (This does not mean it can not be returned to at a later date, simpily that it can be relied apon when building the next stage.) The Stage is concidered complete/passing using a POC_StageX script, that performs functional tests on all expected tasks.(Unlike unit tests, it is expeted to have a human review the outputs, the scrollview.py function is very helpful for this purpose). One the gateway is passed, the next stage can be worked apon, with bugfixes possible on previous stages as they come up. 

### Stage 1: Core Pipeline

- **Setup** project structure
- **Implement** data loading/validation (utils.py)
- **Implement** normalization and smoothing (preprocessing.py)

### Stage 2: Registration

- **Download** MNI152 atlas
- **Implement** SimpleITK-based registration (registration.py)
- **Apply** transformed mask to extract brain

### Stage 3: CLI & Integration

- **Create** command-line interface with argparse
- **Add** logging throughout pipeline
- **Error** handling for edge cases

### Stage 4: Docker Integration 

- **Host** pipline in Docker
- **Enable** production style usecases

### Stage 5: Testing & Documentation

- **Write** unit tests for key functions
- **Create** README with project description and user guide
--- 
## Pipeline Implementation

### 1. **Data Loading & Validation**
- **Library:** `nibabel` for NIFTI, `pydicom`/`SimpleITK` for DICOM
- **Validation:** Check for 3D dimensions, NaN/inf values, valid affine matrix
- **Format support:** .nii, .nii.gz, DICOM series

### 2. **Preprocessing**
- **Normalization:**
  - Z-score: `(x - μ) / σ` → mean=0, std=1
  - Min-max: `(x - min) / (max - min)` → range [0,1]
- **Smoothing:** 3D Gaussian filter via `scipy.ndimage.gaussian_filter`
  - Reduces noise while preserving edges
  - σ=1.0 provides good balance

### 3. **Atlas-Based Registration**
- **Library:** SimpleITK
- **Method:** Intensity-based registration (Mean Squares metric)
- **Registration types:**
  - **Rigid:** 6 DOF (3 rotation + 3 translation) - faster, sufficient for most cases
  - **Affine:** 12 DOF (adds scaling + shearing) - more flexible
- **Multi-resolution:** 3 levels [4x, 2x, 1x] for robustness
- **Optimization:** Gradient descent with automatic scaling

### 4. **Brain Extraction**
- Apply registered atlas mask to subject image
- Inverse transform to return to original space
- Optional: Apply mask to original (unprocessed) image to preserve intensities

### 5. **Quality Assessment**
Automated metrics include:
- **Mask coverage:** % of brain voxels (expected: 10-20%)
- **Brain volume:** Calculated from voxel spacing (expected: 800-2000 cm³)
- **Connected components:** Should be 1 continuous region
- **Edge density:** Smoothness of brain boundary
- **Intensity statistics:** Mean, std, quartiles of brain region

---

## Quality Assessment

Each processed scan generates a JSON quality report:
```json
{
  "metadata": {
    "report_version": "1.0",
    "generated_at": "2025-11-18T22:26:53",
    "filename": "test_sample.nii"
  },
  "summary": {
    "overall_status": "PASS",
    "checks_passed": 5,
    "total_checks": 5
  },
  "metrics": {
    "mask_coverage": {
      "value": 14.99,
      "unit": "percent",
      "status": "PASS",
      "threshold": "5.0 < value < 40.0"
    },
    "brain_volume": {
      "value": 1797.46,
      "unit": "cm3",
      "status": "PASS",
      "threshold": "800 < value < 2000"
    },
    "connected_components": {
      "count": 1,
      "status": "PASS"
    }
    // ... more metrics
  }
}
```

**Interpretation:**
- **PASS:** Brain extraction successful, meets clinical quality standards
- **FAIL:** Manual review recommended, check for registration issues

---

## Visualization

Interactive visualization tools for quality control:

### 1. **Side-by-Side Comparison**


### 2. **Checkerboard Overlay**


### 3. **Difference Map**


### 4. **Alpha Blending**

**Controls:** Left/Right arrows adjust blend ratio

**Example outputs:**

---

## Testing

### Run Unit Tests
```bash
# All tests
pytest

# With coverage report
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_preprocessing.py -v
```
---

## Assumptions & Design Decisions

### Assumptions

1. **Input data:**
   - T1-weighted anatomical MRI scans
   - Standard orientation (RAS/LAS)
   - Sufficient contrast between brain and skull
   - Resolution: ~1mm³ isotropic (typical clinical scans)

2. **Atlas:**
   - MNI152 symmetric template is appropriate for adult brains
   - Template modality matches input (T1-weighted)

3. **Processing:**
   - Rigid registration sufficient for most cases (brain shape similar to atlas)
   - Preprocessing improves registration convergence
   - Quality metrics provide adequate confidence assessment

### Design Decisions

1. **SimpleITK over ANTs/FSL:**
   - Pure Python (no external binaries)
   - Easier deployment (especially Docker)
   - Sufficient registration quality for this task
   - Trade-off: Slightly less accurate than ANTs, but faster

2. **Modular architecture:**
   - Separation of concerns (loading, preprocessing, registration)
   - Easier testing and maintenance
   - Reusable components

3. **Two mask application modes:**
   - **Processed:** Mask on normalized/smoothed image (default)
     - Better for downstream analysis requiring consistent intensities
   - **Original:** Mask on raw image
     - Preserves original intensity values for clinical interpretation

4. **JSON quality reports:**
   - Machine-readable for automated QA pipelines
   - Version-controlled format for longitudinal studies
   - Human-readable with clear pass/fail thresholds

5. **Watch mode for production:**
   - Real-world clinical workflows have continuous scan arrival
   - Automatic processing reduces manual intervention
   - File markers prevent duplicate processing

6. **Comprehensive testing:**
   - Unit tests ensure correctness
   - Integration tests verify end-to-end workflow
   - POC scripts provide regression testing

---

## Potential Improvements

### Short-term (1-2 weeks)

1. **Performance optimization:**
   - Parallelize batch processing (multiprocessing)
   - Cache atlas loading (avoid re-reading for each scan)
   - GPU acceleration for registration (if SimpleITK compiled with CUDA)

2. **Robustness:**
   - Add retry logic for failed registrations
   - Implement fallback to rigid if affine fails
   - Better handling of pathological cases (large tumors, lesions)

3. **Quality metrics:**
   - Add Dice coefficient if ground truth mask available
   - Mutual information between registered and atlas
   - Automated threshold adjustment for borderline cases

### Medium-term (1-3 months)

4. **Multi-atlas registration:**
   - Use multiple templates, take consensus mask
   - More robust for anatomical variations
   - Better for pediatric or elderly populations

5. **Deep learning integration:**
   - Train U-Net or similar for direct skull stripping
   - Faster than registration-based methods
   - Could serve as fallback or primary method

6. **Additional preprocessing:**
   - N4 bias field correction (SimpleITK)
   - Gradient anisotropic diffusion denoising
   - Automatic reorientation to standard space

7. **Extended format support:**
   - DICOM RT structures (for ground truth masks)
   - Compressed NIFTI (.nii.gz) as default output
   - Support for 4D data (time series)

### Long-term (3-6 months)

8. **Web interface:**
   - Upload scans via browser
   - Real-time processing status
   - Interactive 3D visualization (VTK.js or Three.js)

9. **Clinical integration:**
   - DICOM C-STORE SCP (receive from PACS)
   - HL7 FHIR integration
   - Reporting to RIS/EMR

10. **Validation study:**
    - Compare against manual segmentations
    - Multi-site validation
    - Publication of methodology

---

## AI Usage Disclosure

### ChatGPT/Claude Usage
## AI Usage

AI assistants (Claude/ChatGPT) were used as productivity tools for:
- Generating boilerplate code structure
- Initial SimpleITK registration examples
- Documentation templates

All architectural decisions, algorithm selection, parameter tuning, 
production features (Docker, watch mode), and testing strategy were 
human-designed. AI-generated code was validated, debugged, and often 
significantly modified based on domain requirements and testing.

This reflects real-world medical imaging development where engineers 
use all available tools (Stack Overflow, documentation, AI assistants) 
to build robust systems efficiently.

---

## Sample Data

This pipeline was tested with:

**Primary test data:**
- [MEG-BIDS Subject 2 Anatomical](https://openneuro.org/datasets/ds000117/versions/1.0.0)
  - Format: NIFTI (.nii)

**Additional validation:**
- OpenNeuro dataset:
    - doi:10.18112/openneuro.ds000201.v1.0.3
    - T1 Anatomical scans (N=10 subjects)
    - Format: NIFTI (.nii)


**DICOM FORMAT:**
- I found that there was a signficant glut in DICOM formated open source data of good quality
- As a result I created 'convert2dicom.py' which converted .nii files to usable DICOM folder structures
- This could then be used for testing the DICOM ingestion. 

---

## Troubleshooting

### Common Issues

**1. Registration fails to converge:**
```
ERROR: Registration metric did not improve
```
- **Solution:** Try affine instead of rigid, or increase smoothing (sigma=2.0)

**2. Brain mask too aggressive:**
```
WARNING: Mask coverage <5%, possible registration failure
```
- **Solution:** Check input orientation, verify atlas path

**3. Out of memory:**
```
MemoryError: Unable to allocate array
```
- **Solution:** Reduce batch size or downsample images (not recommended)

**4. DICOM series not recognized:**
```
FileNotFoundError: No DICOM files found
```
- **Solution:** Ensure directory contains .dcm files or files without extensions

---

## Citation

If you use this pipeline in research, please cite:
```bibtex
@software{schaefer2025skullstrip,
  author = {Schaefer, Franz},
  title = {Atlas-Based Skull Stripping Pipeline},
  year = {2025},
  url = {https://github.com/...}
}
```

---

## Contact

For questions or issues, please open a GitHub issue or contact:
- **Email:** f.d.schaefer@gmail.com
- **LinkedIn:** [fdschaefer](https://linkedin.com/in/fdschaefer)

---

## Acknowledgments

- MNI152 atlas: [ICBM Atlas](http://www.bic.mni.mcgill.ca/ServicesAtlases/ICBM152NLin2009)
- SimpleITK developers
- O8T for the coding challenge

---

*Last updated: November 2025*
