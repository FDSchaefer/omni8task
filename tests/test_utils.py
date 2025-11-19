"""
Unit tests for utils.py functions
"""
import unittest
import numpy as np
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, '/mnt/project/src')

from utils import ImageData, validate_image_data, load_nifti, save_nifti


class TestImageData(unittest.TestCase):
    """Test ImageData container class"""
    
    def test_basic_initialization(self):
        """Test basic ImageData creation"""
        data = np.random.rand(10, 10, 10)
        img = ImageData(data)
        
        self.assertEqual(img.shape, (10, 10, 10))
        self.assertTrue(np.array_equal(img.data, data))
        self.assertTrue(np.array_equal(img.affine, np.eye(4)))
        self.assertEqual(img.header, {})
    
    def test_initialization_with_affine_and_header(self):
        """Test ImageData creation with affine and header"""
        data = np.random.rand(10, 10, 10)
        affine = np.random.rand(4, 4)
        header = {'test': 'value'}
        
        img = ImageData(data, affine, header)
        
        self.assertTrue(np.array_equal(img.affine, affine))
        self.assertEqual(img.header, header)
    
    def test_dtype_property(self):
        """Test dtype property"""
        data = np.random.rand(10, 10, 10).astype(np.float32)
        img = ImageData(data)
        
        self.assertEqual(img.dtype, np.float32)


class TestValidateImageData(unittest.TestCase):
    """Test image validation function"""
    
    def test_valid_3d_image(self):
        """Test validation passes for valid 3D image"""
        data = np.random.rand(10, 10, 10)
        img = ImageData(data)
        
        self.assertTrue(validate_image_data(img))
    
    def test_invalid_dimensions(self):
        """Test validation fails for non-3D image"""
        data = np.random.rand(10, 10)  # 2D
        img = ImageData(data)
        
        with self.assertRaises(ValueError) as context:
            validate_image_data(img)
        self.assertIn("Expected 3D image", str(context.exception))
    
    def test_empty_image(self):
        """Test validation fails for empty image"""
        data = np.array([[[]]]).reshape(0, 0, 0)
        img = ImageData(data)
        
        with self.assertRaises(ValueError) as context:
            validate_image_data(img)
        self.assertIn("empty", str(context.exception))
    
    def test_nan_values(self):
        """Test validation fails for NaN values"""
        data = np.random.rand(10, 10, 10)
        data[5, 5, 5] = np.nan
        img = ImageData(data)
        
        with self.assertRaises(ValueError) as context:
            validate_image_data(img)
        self.assertIn("NaN", str(context.exception))
    
    def test_inf_values(self):
        """Test validation fails for infinite values"""
        data = np.random.rand(10, 10, 10)
        data[5, 5, 5] = np.inf
        img = ImageData(data)
        
        with self.assertRaises(ValueError) as context:
            validate_image_data(img)
        self.assertIn("infinite", str(context.exception))


class TestLoadSaveNifti(unittest.TestCase):
    """Test NIFTI loading and saving functions"""
    
    def test_save_and_load_roundtrip(self):
        """Test that save->load preserves data"""
        # Create test data
        original_data = np.random.rand(10, 10, 10)
        original_img = ImageData(original_data)
        
        # Save to temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.nii"
            save_nifti(original_img, filepath)
            
            # Load it back
            loaded_img = load_nifti(filepath)
            
            # Check data is preserved
            np.testing.assert_array_almost_equal(
                original_img.data, 
                loaded_img.data, 
                decimal=5
            )
            self.assertEqual(original_img.shape, loaded_img.shape)
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error"""
        with self.assertRaises(FileNotFoundError):
            load_nifti("/nonexistent/path/file.nii")
    
    def test_load_invalid_extension(self):
        """Test loading file with invalid extension raises error"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            with self.assertRaises(ValueError) as context:
                load_nifti(tmp.name)
            self.assertIn("Expected .nii or .nii.gz", str(context.exception))
    
    def test_save_creates_directory(self):
        """Test that save_nifti creates parent directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "test.nii"
            data = np.random.rand(10, 10, 10)
            img = ImageData(data)
            
            save_nifti(img, nested_path)
            
            self.assertTrue(nested_path.exists())


if __name__ == '__main__':
    unittest.main()
