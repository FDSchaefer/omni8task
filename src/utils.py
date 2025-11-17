"""
Utility functions for loading and validating medical imaging data.
"""
import logging
from pathlib import Path
from typing import Tuple, Union
import numpy as np


logger = logging.getLogger(__name__)


class ImageData:
    """Container for 3D medical imaging data with metadata."""
    
    def __init__(self, data: np.ndarray, affine: np.ndarray = None, header: dict = None):
        self.data = data
        self.affine = affine if affine is not None else np.eye(4)
        self.header = header if header is not None else {}
        
    @property
    def shape(self) -> Tuple[int, int, int]:
        return self.data.shape
    
    @property
    def dtype(self):
        return self.data.dtype


def validate_image_data(img_data: ImageData) -> bool:
    """
    Validate that image data meets basic requirements.
    
    Args:
        img_data: ImageData object to validate
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    if img_data.data.ndim != 3:
        raise ValueError(f"Expected 3D image, got {img_data.data.ndim}D")
    
    if img_data.data.size == 0:
        raise ValueError("Image data is empty")
    
    if not np.isfinite(img_data.data).all():
        raise ValueError("Image contains NaN or infinite values")
    
    logger.info(f"Image validation passed: shape={img_data.shape}, dtype={img_data.dtype}")
    return True


def load_nifti(filepath: Union[str, Path]) -> ImageData:
    """
    Load a NIFTI file.
    
    Args:
        filepath: Path to NIFTI file (.nii or .nii.gz)
        
    Returns:
        ImageData object containing the loaded image
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if filepath.suffix not in ['.nii', '.gz']:
        raise ValueError(f"Expected .nii or .nii.gz file, got {filepath.suffix}")
    
    try:
        import nibabel as nib
        img = nib.load(str(filepath))
        return ImageData(img.get_fdata(), img.affine, dict(img.header))
        
    except Exception as e:
        logger.error(f"Failed to load NIFTI file: {e}")
        raise


def load_dicom_series(directory: Union[str, Path]) -> ImageData:
    """
    Load a DICOM series from a directory.
    
    Args:
        directory: Path to directory containing DICOM files
        
    Returns:
        ImageData object containing the loaded series
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise ValueError(f"Expected directory, got file: {directory}")
    
    try:
        import SimpleITK as sitk
        logger.info(f"Loading DICOM series from: {directory}")
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(str(directory))
        reader.SetFileNames(dicom_names)
        image = reader.Execute()
        data = sitk.GetArrayFromImage(image)
        return ImageData(data)
        
    except Exception as e:
        logger.error(f"Failed to load DICOM series: {e}")
        raise


def save_nifti(img_data: ImageData, filepath: Union[str, Path]) -> None:
    """
    Save ImageData to a NIFTI file.
    
    Args:
        img_data: ImageData object to save
        filepath: Output path for NIFTI file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        import nibabel as nib
        nifti_img = nib.Nifti1Image(img_data.data, img_data.affine)
        nib.save(nifti_img, str(filepath))
        
        logger.info(f"Saving NIFTI file: {filepath}")

    except Exception as e:
        logger.error(f"Failed to save NIFTI file: {e}")
        raise


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
