#!/usr/bin/env python3
"""
Medical Imaging Pipeline - Command Line Interface
Performs atlas-based skull stripping with configurable preprocessing
"""
import argparse
import json
import yaml
import logging
import sys
from pathlib import Path
from datetime import datetime

# Import pipeline modules
from src.utils import (
    setup_logging, 
    load_nifti, 
    load_dicom_series,
    save_nifti,
    validate_image_data
)
from src.preprocessing import preprocess_image
from src.registration import atlas_based_skull_strip
from src.quality_assessment import assess_quality, print_quality_report


def load_config(config_path: Path) -> dict:
    """Load processing configuration from JSON or YAML file."""
    with open(config_path, 'r') as f:
        if config_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif config_path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")


def save_report(results: dict, output_path: Path) -> None:
    """Save quality assessment report to text file."""
    with open(output_path, 'w') as f:
        f.write("="*60 + "\n")
        f.write("MEDICAL IMAGING PIPELINE - QUALITY REPORT\n")
        f.write("="*60 + "\n\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n\n")
        
        f.write(f"Mask Coverage: {results['mask_coverage_percent']:.2f}%\n")
        f.write(f"Brain Volume: {results['brain_volume_cm3']:.2f} cm³\n")
        f.write(f"Connected Components: {results['connected_components']['num_components']}\n")
        f.write(f"Edge Density: {results['edge_density']:.4f}\n\n")
        
        stats = results['intensity_stats']
        f.write("Intensity Statistics:\n")
        f.write(f"  Mean: {stats['mean']:.2f}\n")
        f.write(f"  Std:  {stats['std']:.2f}\n")
        f.write(f"  Range: [{stats['min']:.2f}, {stats['max']:.2f}]\n\n")
        
        f.write(f"Quality Checks: {results['passed_checks']}/{results['total_checks']} passed\n")
        f.write(f"Overall Status: {'PASS' if results['overall_pass'] else 'FAIL'}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Medical Imaging Pipeline for skull stripping',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input/output arguments
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Input image file (NIFTI) or directory (DICOM series)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Output skull-stripped image file'
    )
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Configuration file (JSON or YAML) with processing parameters'
    )
    
    # Processing parameters
    parser.add_argument(
        '--atlas-dir',
        type=Path,
        default=Path('/data/atlas'),
        help='Directory containing MNI152 atlas (default: /data/atlas)'
    )
    parser.add_argument(
        '--normalize',
        choices=['zscore', 'minmax'],
        default='zscore',
        help='Normalization method (default: zscore)'
    )
    parser.add_argument(
        '--sigma',
        type=float,
        default=1.0,
        help='Gaussian smoothing sigma (default: 1.0)'
    )
    parser.add_argument(
        '--registration',
        choices=['rigid', 'affine'],
        default='rigid',
        help='Registration type (default: rigid)'
    )
    
    # Output options
    parser.add_argument(
        '--report',
        type=Path,
        help='Output quality report file (text format)'
    )
    parser.add_argument(
        '--save-intermediate',
        action='store_true',
        help='Save intermediate processing results'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("MEDICAL IMAGING PIPELINE - SKULL STRIPPING")
    logger.info("="*60)
    
    # Load config if provided
    if args.config:
        logger.info(f"Loading configuration from: {args.config}")
        config = load_config(args.config)
        # Override command-line args with config values
        args.normalize = config.get('normalize', args.normalize)
        args.sigma = config.get('sigma', args.sigma)
        args.registration = config.get('registration', args.registration)
    
    # Log parameters
    logger.info("\nProcessing parameters:")
    logger.info(f"  Input: {args.input}")
    logger.info(f"  Output: {args.output}")
    logger.info(f"  Atlas: {args.atlas_dir}")
    logger.info(f"  Normalization: {args.normalize}")
    logger.info(f"  Smoothing sigma: {args.sigma}")
    logger.info(f"  Registration: {args.registration}")
    
    try:
        # Load input image
        logger.info("\n1. Loading input image...")
        if args.input.is_dir():
            logger.info("   Loading DICOM series...")
            img_data = load_dicom_series(args.input)
        else:
            logger.info("   Loading NIFTI file...")
            img_data = load_nifti(args.input)
        
        # Validate
        logger.info("\n2. Validating image data...")
        validate_image_data(img_data)
        logger.info(f"   Shape: {img_data.shape}")
        
        # Preprocess
        logger.info("\n3. Preprocessing...")
        preprocessed = preprocess_image(
            img_data,
            normalize_method=args.normalize,
            sigma=args.sigma
        )
        
        if args.save_intermediate:
            intermediate_path = args.output.parent / f"{args.output.stem}_preprocessed{args.output.suffix}"
            save_nifti(preprocessed, intermediate_path)
            logger.info(f"   Saved preprocessed image: {intermediate_path}")
        
        # Skull stripping
        logger.info("\n4. Performing atlas-based skull stripping...")
        result = atlas_based_skull_strip(
            preprocessed,
            atlas_dir=args.atlas_dir,
            registration_type=args.registration
        )
        
        # Save output
        logger.info("\n5. Saving results...")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        save_nifti(result, args.output)
        logger.info(f"   Saved skull-stripped image: {args.output}")
        
        # Quality assessment
        logger.info("\n6. Quality assessment...")
        qa_results = assess_quality(result)
        print_quality_report(qa_results)
        
        # Save report if requested
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            save_report(qa_results, args.report)
            logger.info(f"   Saved quality report: {args.report}")
        
        logger.info("\n" + "="*60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        logger.error("\nPIPELINE FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
