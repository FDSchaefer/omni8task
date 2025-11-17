"""
Main pipeline orchestrator for dockerized skull stripping with file watching.
"""
import argparse
import json
import logging
import time
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import load_nifti, save_nifti, setup_logging, load_dicom_series
from preprocessing import preprocess_image
from registration import atlas_based_skull_strip
from quality_assessment import assess_quality, print_quality_report

logger = logging.getLogger(__name__)


class MRIFileHandler(FileSystemEventHandler):
    """Handle new MRI file arrivals."""
    
    def __init__(self, config_path: Path, output_dir: Path):
        self.config_path = config_path
        self.output_dir = output_dir
        self.processing = set()  # Track files being processed
        self.processed = set()   # Track completed files
        
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process .nii, .nii.gz, or DICOM series directories
        if not (file_path.suffix == '.nii' or file_path.name.endswith('.nii.gz')):
            logger.debug(f"Ignoring non-NIFTI file: {file_path}")
            return
            
        # Avoid reprocessing
        if str(file_path) in self.processing or str(file_path) in self.processed:
            logger.debug(f"File already processed or processing: {file_path}")
            return
            
        # Wait for file to be fully written (handles slow uploads/copies)
        logger.info(f"New file detected: {file_path.name}, waiting for write completion...")
        time.sleep(2)
        
        self.processing.add(str(file_path))
        
        try:
            process_single_file(file_path, self.config_path, self.output_dir)
            self.processed.add(str(file_path))
            logger.info(f"Successfully completed processing: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}", exc_info=True)
        finally:
            self.processing.discard(str(file_path))


def process_single_file(input_file: Path, config_path: Path, output_dir: Path):
    """
    Process a single MRI file through the full pipeline.
    
    Args:
        input_file: Path to input NIFTI file
        config_path: Path to JSON config file
        output_dir: Directory for output files
    """
    logger.info(f"Starting processing: {input_file.name}")
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
    # Load image
    logger.info(f"Loading image: {input_file}")
    img = load_nifti(input_file)
    logger.info(f"Loaded image shape: {img.shape}")
    
    # Preprocess
    logger.info("Starting preprocessing...")
    preprocessed = preprocess_image(
        img,
        normalize_method=config.get('normalize_method', 'zscore'),
        sigma=config.get('gaussian_sigma', 1.0)
    )
    
    # Skull strip
    logger.info("Starting skull stripping...")
    result = atlas_based_skull_strip(
        preprocessed,
        atlas_dir=Path(config.get('atlas_dir', '/app/MNI_atlas')),
        registration_type=config.get('registration_type', 'rigid')
    )
    
    # Save result
    output_file = output_dir / f"{input_file.stem}_skull_stripped.nii.gz"
    logger.info(f"Saving result to: {output_file}")
    save_nifti(result, output_file)
    
    # Quality assessment
    logger.info("Running quality assessment...")
    quality_results = assess_quality(result)
    
    # Save quality report
    report_file = output_dir / f"{input_file.stem}_quality_report.txt"
    logger.info(f"Saving quality report to: {report_file}")
    
    with open(report_file, 'w') as f:
        # Redirect stdout to file for report
        old_stdout = sys.stdout
        sys.stdout = f
        
        # Write header
        print(f"Quality Assessment Report")
        print(f"Input file: {input_file.name}")
        print(f"Processing date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # Write report
        print_quality_report(quality_results)
        
        # Restore stdout
        sys.stdout = old_stdout
    
    logger.info(f"Processing complete: {input_file.name}")


def watch_mode(config_path: Path, input_dir: Path, output_dir: Path):
    """
    Continuously watch input directory for new files.
    
    Args:
        config_path: Path to JSON config file
        input_dir: Directory to watch for new files
        output_dir: Directory for output files
    """
    logger.info("=" * 60)
    logger.info("SKULL STRIPPING PIPELINE - WATCH MODE")
    logger.info("=" * 60)
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Config file: {config_path}")
    logger.info("Watching for new .nii and .nii.gz files...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process any existing files first
    existing_files = list(input_dir.glob('*.nii*'))
    if existing_files:
        logger.info(f"Found {len(existing_files)} existing files")
        for file_path in existing_files:
            logger.info(f"Processing existing file: {file_path.name}")
            try:
                process_single_file(file_path, config_path, output_dir)
            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}", exc_info=True)
    else:
        logger.info("No existing files found")
    
    # Set up watchdog
    event_handler = MRIFileHandler(config_path, output_dir)
    observer = Observer()
    observer.schedule(event_handler, str(input_dir), recursive=False)
    observer.start()
    
    logger.info("File watching started. Waiting for new files...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        observer.stop()
        logger.info("Stopped watching directory")
    
    observer.join()
    logger.info("Pipeline stopped")


def batch_mode(config_path: Path, input_dir: Path, output_dir: Path):
    """
    Process all files in input directory once and exit.
    
    Args:
        config_path: Path to JSON config file
        input_dir: Directory containing input files
        output_dir: Directory for output files
    """
    logger.info("=" * 60)
    logger.info("SKULL STRIPPING PIPELINE - BATCH MODE")
    logger.info("=" * 60)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all input files
    input_files = list(input_dir.glob('*.nii*'))
    
    if not input_files:
        logger.warning(f"No .nii or .nii.gz files found in {input_dir}")
        return
    
    logger.info(f"Found {len(input_files)} files to process")
    
    # Process each file
    success_count = 0
    fail_count = 0
    
    for i, input_file in enumerate(input_files, 1):
        logger.info(f"Processing file {i}/{len(input_files)}: {input_file.name}")
        try:
            process_single_file(input_file, config_path, output_dir)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to process {input_file.name}: {e}", exc_info=True)
            fail_count += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info(f"Successfully processed: {success_count}/{len(input_files)}")
    logger.info(f"Failed: {fail_count}/{len(input_files)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='MRI Skull Stripping Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Watch mode (continuous)
  python -m src.pipeline --config config.json --input-dir /data/input --output-dir /data/output --watch
  
  # Batch mode (process once and exit)
  python -m src.pipeline --config config.json --input-dir /data/input --output-dir /data/output
        """
    )
    
    parser.add_argument('--config', type=Path, required=True,
                       help='Path to JSON configuration file')
    parser.add_argument('--input-dir', type=Path, required=True,
                       help='Directory containing input MRI files')
    parser.add_argument('--output-dir', type=Path, required=True,
                       help='Directory for output files')
    parser.add_argument('--watch', action='store_true',
                       help='Enable watch mode (process files as they arrive)')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Validate paths
    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)
    
    if not args.input_dir.exists():
        logger.error(f"Input directory not found: {args.input_dir}")
        sys.exit(1)
    
    # Run appropriate mode
    if args.watch:
        watch_mode(args.config, args.input_dir, args.output_dir)
    else:
        batch_mode(args.config, args.input_dir, args.output_dir)
