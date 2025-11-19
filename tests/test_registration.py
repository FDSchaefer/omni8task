"""
Unit tests for registration.py functions
"""
import unittest
import numpy as np
import sys
sys.path.insert(0, '/mnt/project/src')

from utils import ImageData
from registration import numpy_to_sitk, sitk_to_numpy, skull_strip


class TestNumpySitkConversion(unittest.TestCase):
    """Test conversion between NumPy and SimpleITK formats"""
    
    def test_numpy_to_sitk_basic(self):
        """Test basic NumPy to SimpleITK conversion"""
        data = np.random.rand(10, 10, 10).astype(np.float32)
        img = ImageData(data)
        
        sitk_img = numpy_to_sitk(img)
        
        # Check that conversion succeeded
        self.assertIsNotNone(sitk_img)
        self.assertEqual(sitk_img.GetSize(), (10, 10, 10))
    
    def test_sitk_to_numpy_basic(self):
        """Test basic SimpleITK to NumPy conversion"""
        data = np.random.rand(10, 10, 10).astype(np.float32)
        img = ImageData(data)
        
        sitk_img = numpy_to_sitk(img)
        converted_back = sitk_to_numpy(sitk_img, img)
        
        # Check shape is preserved
        self.assertEqual(converted_back.shape, img.shape)
    
    def test_roundtrip_conversion(self):
        """Test that NumPy -> SITK -> NumPy preserves data"""
        data = np.random.rand(10, 10, 10)
        affine = np.eye(4)
        affine[0, 0] = 2.0  # Set spacing
        affine[1, 1] = 2.0
        affine[2, 2] = 2.0
        img = ImageData(data, affine)
        
        sitk_img = numpy_to_sitk(img)
        converted_back = sitk_to_numpy(sitk_img, img)
        
        # Check data is approximately preserved
        np.testing.assert_array_almost_equal(
            data, 
            converted_back.data, 
            decimal=5
        )
    
    def test_preserves_spacing(self):
        """Test that conversion preserves voxel spacing"""
        data = np.random.rand(10, 10, 10)
        affine = np.eye(4)
        affine[0, 0] = 2.5
        affine[1, 1] = 2.5
        affine[2, 2] = 3.0
        img = ImageData(data, affine)
        
        sitk_img = numpy_to_sitk(img)
        spacing = sitk_img.GetSpacing()
        
        # Check spacing is approximately correct
        np.testing.assert_array_almost_equal(
            spacing, 
            [2.5, 2.5, 3.0], 
            decimal=5
        )


class TestSkullStrip(unittest.TestCase):
    """Test skull stripping function"""
    
    def test_basic_skull_stripping(self):
        """Test basic skull stripping with binary mask"""
        # Create test image
        data = np.ones((10, 10, 10)) * 100
        img = ImageData(data)
        
        # Create binary mask (brain in center)
        mask_data = np.zeros((10, 10, 10))
        mask_data[3:7, 3:7, 3:7] = 1
        mask = ImageData(mask_data)
        
        result = skull_strip(img, mask)
        
        # Check that non-brain region is zeroed
        self.assertEqual(result.data[0, 0, 0], 0)
        # Check that brain region is preserved
        self.assertEqual(result.data[5, 5, 5], 100)
    
    def test_skull_strip_preserves_shape(self):
        """Test that skull stripping preserves image shape"""
        data = np.random.rand(15, 20, 25)
        img = ImageData(data)
        
        mask_data = np.ones((15, 20, 25))
        mask = ImageData(mask_data)
        
        result = skull_strip(img, mask)
        
        self.assertEqual(result.shape, img.shape)
    
    def test_skull_strip_with_zero_mask(self):
        """Test skull stripping with all-zero mask"""
        data = np.ones((10, 10, 10)) * 100
        img = ImageData(data)
        
        mask_data = np.zeros((10, 10, 10))
        mask = ImageData(mask_data)
        
        result = skull_strip(img, mask)
        
        # All voxels should be zero
        np.testing.assert_array_equal(result.data, np.zeros((10, 10, 10)))
    
    def test_skull_strip_with_full_mask(self):
        """Test skull stripping with all-one mask"""
        data = np.random.rand(10, 10, 10) * 100
        img = ImageData(data)
        
        mask_data = np.ones((10, 10, 10))
        mask = ImageData(mask_data)
        
        result = skull_strip(img, mask)
        
        # All voxels should be preserved
        np.testing.assert_array_almost_equal(result.data, data)
    
    def test_mismatched_shapes(self):
        """Test that mismatched shapes raise error"""
        data = np.random.rand(10, 10, 10)
        img = ImageData(data)
        
        mask_data = np.ones((15, 15, 15))
        mask = ImageData(mask_data)
        
        with self.assertRaises(ValueError) as context:
            skull_strip(img, mask)
        self.assertIn("doesn't match", str(context.exception))
    
    def test_skull_strip_preserves_affine(self):
        """Test that skull stripping preserves affine"""
        data = np.random.rand(10, 10, 10)
        affine = np.random.rand(4, 4)
        img = ImageData(data, affine)
        
        mask_data = np.ones((10, 10, 10))
        mask = ImageData(mask_data)
        
        result = skull_strip(img, mask)
        
        np.testing.assert_array_equal(result.affine, affine)
    
    def test_fractional_mask(self):
        """Test skull stripping with fractional mask values"""
        data = np.ones((10, 10, 10)) * 100
        img = ImageData(data)
        
        # Mask with fractional values
        mask_data = np.full((10, 10, 10), 0.5)
        mask = ImageData(mask_data)
        
        result = skull_strip(img, mask)
        
        # Result should be scaled by mask
        expected = data * mask_data
        np.testing.assert_array_almost_equal(result.data, expected)


if __name__ == '__main__':
    unittest.main()
