# src/pipeline.py
"""
Main pipeline orchestrator for dockerized skull stripping with watch mode.
"""
import argparse
import json
import time
import logging
from pathlib import Path
from typing import Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from utils import load_nifti, save_nifti, setup_logging
from preprocessing import preprocess_image
from registration import atlas_based_skull_strip
from quality_assessment import assess_quality, print_quality_report

logger = logging.getLogger(__name__)


def process_single_file(input_file: Path, config: dict, output_dir: Path):
    """Process a single MRI file."""
    try:
        logger.info(f"Processing: {input_file.name}")
        
        # Load
        img = load_nifti(input_file)
        
        # Preprocess
        preprocessed = preprocess_image(
            img,
            normalize_method=config.get('normalize_method', 'zscore'),
            sigma=config.get('gaussian_sigma', 1.0)
        )
        
        # Skull strip
        result = atlas_based_skull_strip(
            preprocessed,
            atlas_dir=Path(config['atlas_dir']),
            registration_type=config.get('registration_type', 'rigid')
        )
        
        # Save result
        output_file = output_dir / f"{input_file.stem}_skull_stripped.nii.gz"
        save_nifti(result, output_file)
        logger.info(f"Saved result: {output_file.name}")
        
        # Quality assessment
        quality_results = assess_quality(result)
        
        # Save report
        report_file = output_dir / f"{input_file.stem}_quality_report.txt"
        with open(report_file, 'w') as f:
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_quality_report(quality_results)
            sys.stdout = old_stdout
        
        logger.info(f"Saved quality report: {report_file.name}")
        
        # Create processing marker
        marker_file = output_dir / f".{input_file.name}.processed"
        marker_file.touch()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {input_file.name}: {e}", exc_info=True)
        
        # Create error marker
        error_file = output_dir / f".{input_file.name}.error"
        with open(error_file, 'w') as f:
            f.write(str(e))
        
        return False


def is_valid_nifti(filepath: Path) -> bool:
    """Check if file is a valid NIFTI file."""
    valid_extensions = ['.nii', '.nii.gz']
    return any(str(filepath).endswith(ext) for ext in valid_extensions)


def is_already_processed(filepath: Path, output_dir: Path) -> bool:
    """Check if file has already been processed."""
    marker = output_dir / f".{filepath.name}.processed"
    error_marker = output_dir / f".{filepath.name}.error"
    return marker.exists() or error_marker.exists()


class MRIFileHandler(FileSystemEventHandler):
    """Handler for new MRI files."""
    
    def __init__(self, config: dict, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.processing: Set[Path] = set()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Check if valid NIFTI
        if not is_valid_nifti(filepath):
            return
        
        # Avoid processing same file twice
        if filepath in self.processing:
            return
        
        # Wait for file to be fully written
        self._wait_for_file_ready(filepath)
        
        # Check if already processed
        if is_already_processed(filepath, self.output_dir):
            logger.info(f"Skipping already processed file: {filepath.name}")
            return
        
        # Process the file
        self.processing.add(filepath)
        logger.info(f"New file detected: {filepath.name}")
        
        success = process_single_file(filepath, self.config, self.output_dir)
        
        self.processing.discard(filepath)
        
        if success:
            logger.info(f"Successfully processed: {filepath.name}")
        else:
            logger.error(f"Failed to process: {filepath.name}")
    
    def _wait_for_file_ready(self, filepath: Path, timeout: int = 30):
        """Wait until file is fully written (size stops changing)."""
        if not filepath.exists():
            return
        
        start_time = time.time()
        prev_size = -1
        
        while time.time() - start_time < timeout:
            try:
                curr_size = filepath.stat().st_size
                if curr_size == prev_size and curr_size > 0:
                    # Size stable, file ready
                    time.sleep(1)  # Extra safety margin
                    return
                prev_size = curr_size
                time.sleep(0.5)
            except OSError:
                time.sleep(0.5)
        
        logger.warning(f"Timeout waiting for {filepath.name} to be ready")


def run_watch_mode(config_path: Path, input_dir: Path, output_dir: Path):
    """Run pipeline in watch mode."""
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
    setup_logging(config.get('log_level', 'INFO'))
    
    logger.info("="*60)
    logger.info("SKULL STRIPPING PIPELINE - WATCH MODE")
    logger.info("="*60)
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Configuration: {config_path}")
    logger.info("")
    logger.info("Watching for new files...")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)
    
    # Process existing files first
    logger.info("Processing existing files...")
    existing_files = [f for f in input_dir.glob('*.nii*') if is_valid_nifti(f)]
    
    for input_file in existing_files:
        if not is_already_processed(input_file, output_dir):
            logger.info(f"Found existing file: {input_file.name}")
            process_single_file(input_file, config, output_dir)
    
    logger.info("Finished processing existing files")
    logger.info("")
    
    # Set up file system watcher
    event_handler = MRIFileHandler(config, output_dir)
    observer = Observer()
    observer.schedule(event_handler, str(input_dir), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watch mode...")
        observer.stop()
    
    observer.join()
    logger.info("Shutdown complete")


def run_batch_mode(config_path: Path, input_dir: Path, output_dir: Path):
    """Run pipeline in batch mode (process once and exit)."""
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
    setup_logging(config.get('log_level', 'INFO'))
    
    logger.info("="*60)
    logger.info("SKULL STRIPPING PIPELINE - BATCH MODE")
    logger.info("="*60)
    
    # Process all files
    input_files = [f for f in input_dir.glob('*.nii*') if is_valid_nifti(f)]
    
    if not input_files:
        logger.warning("No NIFTI files found in input directory")
        return
    
    logger.info(f"Found {len(input_files)} file(s) to process")
    
    success_count = 0
    for input_file in input_files:
        if is_already_processed(input_file, output_dir):
            logger.info(f"Skipping already processed: {input_file.name}")
            continue
        
        if process_single_file(input_file, config, output_dir):
            success_count += 1
    
    logger.info("")
    logger.info(f"Batch processing complete: {success_count}/{len(input_files)} succeeded")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MRI Skull Stripping Pipeline"
    )
    parser.add_argument(
        '--config', 
        type=Path, 
        default=Path('/data/config/config.json'),
        help='Path to configuration file'
    )
    parser.add_argument(
        '--input-dir', 
        type=Path, 
        default=Path('/data/input'),
        help='Input directory containing MRI files'
    )
    parser.add_argument(
        '--output-dir', 
        type=Path, 
        default=Path('/data/output'),
        help='Output directory for results'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Run in watch mode (continuously monitor for new files)'
    )
    
    args = parser.parse_args()
    
    # Create output directory if needed
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.watch:
        run_watch_mode(args.config, args.input_dir, args.output_dir)
    else:
        run_batch_mode(args.config, args.input_dir, args.output_dir)