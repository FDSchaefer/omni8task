"""
Quality assessment metrics for skull stripping evaluation.
"""
import logging
import numpy as np
from scipy import ndimage
from scipy.ndimage import sobel
from typing import Dict, Optional
import warnings

from utils import ImageData

logger = logging.getLogger(__name__)


def calculate_mask_coverage(img_data: ImageData) -> float:
    """
    Calculate percentage of non-zero voxels in the image.
    
    Args:
        img_data: Skull-stripped image data
        
    Returns:
        Percentage of brain voxels (0-100)
    """
    total_voxels = np.prod(img_data.shape)
    brain_voxels = np.sum(img_data.data > 0)
    coverage = (brain_voxels / total_voxels) * 100
    
    logger.info(f"Mask coverage: {coverage:.2f}% ({brain_voxels}/{total_voxels} voxels)")
    return coverage


def calculate_brain_volume(img_data: ImageData) -> float:
    """
    Calculate brain volume in cm³ using voxel spacing.
    
    Args:
        img_data: Skull-stripped image data
        
    Returns:
        Brain volume in cm³
    """
    # Extract voxel spacing from affine matrix (mm)
    voxel_dims = np.abs(np.diag(img_data.affine[:3, :3]))
    voxel_volume_mm3 = np.prod(voxel_dims)
    voxel_volume_cm3 = voxel_volume_mm3 / 1000.0  # Convert mm³ to cm³
    
    brain_voxels = np.sum(img_data.data > 0)
    volume_cm3 = brain_voxels * voxel_volume_cm3
    
    logger.info(f"Brain volume: {volume_cm3:.2f} cm³")
    logger.info(f"Voxel dimensions: {voxel_dims} mm")
    
    return volume_cm3


def check_connected_components(img_data: ImageData) -> Dict[str, any]:
    """
    Analyze connected components in the brain mask.
    
    Args:
        img_data: Skull-stripped image data
        
    Returns:
        Dictionary with component analysis results
    """
    # Create binary mask
    binary_mask = img_data.data > 0
    
    # Label connected components
    labeled_array, num_features = ndimage.label(binary_mask)
    
    # Calculate size of each component
    component_sizes = ndimage.sum(binary_mask, labeled_array, 
                                   range(1, num_features + 1))
    
    if num_features > 0:
        largest_component_size = np.max(component_sizes)
        largest_component_fraction = largest_component_size / np.sum(binary_mask)
    else:
        largest_component_size = 0
        largest_component_fraction = 0
    
    results = {
        'num_components': num_features,
        'largest_component_size': int(largest_component_size),
        'largest_component_fraction': largest_component_fraction,
        'component_sizes': component_sizes
    }
    
    logger.info(f"Connected components: {num_features}")
    logger.info(f"Largest component: {largest_component_fraction*100:.1f}% of total")
    
    if num_features > 1:
        logger.warning(f"Multiple components detected ({num_features}). "
                      f"Brain should typically be one connected region.")
    
    return results


def calculate_edge_density(img_data: ImageData) -> float:
    """
    Calculate edge density at the brain boundary using Sobel filter.
    
    Args:
        img_data: Skull-stripped image data
        
    Returns:
        Average edge magnitude at boundary
    """
    # Create binary mask
    binary_mask = img_data.data > 0
    
    # Find boundary voxels (mask edge)
    eroded = ndimage.binary_erosion(binary_mask)
    boundary = binary_mask & ~eroded
    
    # Calculate gradient magnitude using Sobel operator
    sx = sobel(img_data.data, axis=0)
    sy = sobel(img_data.data, axis=1)
    sz = sobel(img_data.data, axis=2)
    gradient_magnitude = np.sqrt(sx**2 + sy**2 + sz**2)
    
    # Calculate average edge strength at boundary
    boundary_voxels = np.sum(boundary)
    if boundary_voxels > 0:
        edge_density = np.sum(gradient_magnitude[boundary]) / boundary_voxels
    else:
        edge_density = 0
    
    logger.info(f"Edge density at boundary: {edge_density:.4f}")
    
    return edge_density


def calculate_intensity_statistics(img_data: ImageData) -> Dict[str, float]:
    """
    Calculate intensity statistics for the brain region.
    
    Args:
        img_data: Skull-stripped image data
        
    Returns:
        Dictionary with intensity statistics
    """
    brain_voxels = img_data.data[img_data.data > 0]
    
    if len(brain_voxels) == 0:
        logger.warning("No brain voxels found!")
        return {
            'mean': 0,
            'std': 0,
            'min': 0,
            'max': 0,
            'median': 0,
            'q25': 0,
            'q75': 0
        }
    
    stats = {
        'mean': float(np.mean(brain_voxels)),
        'std': float(np.std(brain_voxels)),
        'min': float(np.min(brain_voxels)),
        'max': float(np.max(brain_voxels)),
        'median': float(np.median(brain_voxels)),
        'q25': float(np.percentile(brain_voxels, 25)),
        'q75': float(np.percentile(brain_voxels, 75))
    }
    
    logger.info(f"Intensity statistics:")
    logger.info(f"  Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")
    logger.info(f"  Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
    logger.info(f"  Median: {stats['median']:.2f}")
    
    return stats

def calculate_dice_coefficient(img_data: ImageData, 
                               ground_truth: ImageData) -> Dict[str, float]:
    """
    Calculate Dice coefficient between predicted mask and ground truth.
    
    The Dice coefficient measures overlap between two binary masks:
    Dice = 2 * |A ∩ B| / (|A| + |B|)
    
    Args:
        img_data: Skull-stripped image (predicted mask)
        ground_truth: Manual/ground truth mask
        
    Returns:
        Dictionary with Dice coefficient and related metrics
    """
    if img_data.shape != ground_truth.shape:
        raise ValueError(f"Image shapes must match: {img_data.shape} vs {ground_truth.shape}")
    
    # Create binary masks
    pred_mask = img_data.data > 0
    gt_mask = ground_truth.data > 0
    
    # Calculate intersection and union
    intersection = np.sum(pred_mask & gt_mask)
    pred_volume = np.sum(pred_mask)
    gt_volume = np.sum(gt_mask)
    
    # Dice coefficient
    if pred_volume + gt_volume == 0:
        dice = 0.0
        logger.warning("Both masks are empty!")
    else:
        dice = 2.0 * intersection / (pred_volume + gt_volume)
    
    # Jaccard index (IoU - Intersection over Union)
    union = np.sum(pred_mask | gt_mask)
    jaccard = intersection / union if union > 0 else 0.0
    
    # Sensitivity (recall, true positive rate)
    sensitivity = intersection / gt_volume if gt_volume > 0 else 0.0
    
    # Specificity (true negative rate)
    true_negatives = np.sum(~pred_mask & ~gt_mask)
    total_negatives = np.sum(~gt_mask)
    specificity = true_negatives / total_negatives if total_negatives > 0 else 0.0
    
    # Precision (positive predictive value)
    precision = intersection / pred_volume if pred_volume > 0 else 0.0
    
    results = {
        'dice': dice,
        'jaccard': jaccard,
        'sensitivity': sensitivity,
        'specificity': specificity,
        'precision': precision,
        'intersection_voxels': int(intersection),
        'pred_voxels': int(pred_volume),
        'gt_voxels': int(gt_volume)
    }
    
    logger.info(f"Dice Coefficient: {dice:.4f}")
    logger.info(f"Jaccard Index (IoU): {jaccard:.4f}")
    logger.info(f"Sensitivity: {sensitivity:.4f}, Precision: {precision:.4f}")
    
    return results

def calculate_mutual_information(img1: ImageData, img2: ImageData, 
                                 bins: int = 256) -> float:
    """
    Calculate normalized mutual information between two images.
    Useful for assessing registration quality.
    
    Args:
        img1: First image (e.g., registered subject)
        img2: Second image (e.g., atlas template)
        bins: Number of histogram bins
        
    Returns:
        Normalized mutual information value (0-1, higher is better)
    """
    if img1.shape != img2.shape:
        raise ValueError(f"Image shapes must match: {img1.shape} vs {img2.shape}")
    
    # Flatten arrays and remove zero values (background)
    mask = (img1.data > 0) & (img2.data > 0)
    data1 = img1.data[mask].flatten()
    data2 = img2.data[mask].flatten()
    
    if len(data1) == 0:
        logger.warning("No overlapping voxels for MI calculation")
        return 0.0
    
    # Suppress numpy histogram warnings for empty bins
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        # Calculate 2D histogram
        hist_2d, _, _ = np.histogram2d(data1, data2, bins=bins)
        
        # Normalize to probability distribution
        pxy = hist_2d / np.sum(hist_2d)
        
        # Marginal distributions
        px = np.sum(pxy, axis=1)
        py = np.sum(pxy, axis=0)
        
        # Calculate entropies (avoiding log(0))
        px_nonzero = px[px > 0]
        py_nonzero = py[py > 0]
        pxy_nonzero = pxy[pxy > 0]
        
        h_x = -np.sum(px_nonzero * np.log2(px_nonzero))
        h_y = -np.sum(py_nonzero * np.log2(py_nonzero))
        h_xy = -np.sum(pxy_nonzero * np.log2(pxy_nonzero))
    
    # Mutual information
    mi = h_x + h_y - h_xy
    
    # Normalized mutual information (0 to 1)
    nmi = 2 * mi / (h_x + h_y) if (h_x + h_y) > 0 else 0
    
    logger.info(f"Normalized Mutual Information: {nmi:.4f}")
    
    return nmi



def assess_quality(img_data: ImageData, 
                   reference_img: Optional[ImageData] = None,
                   ground_truth_mask: Optional[ImageData] = None) -> Dict[str, any]:
    """
    Comprehensive quality assessment of skull-stripped image.
    
    Args:
        img_data: Skull-stripped image to assess
        reference_img: Optional reference image for mutual information
        ground_truth_mask: Optional manual/ground truth mask for Dice coefficient
        
    Returns:
        Dictionary with all quality metrics and pass/fail flags
    """
    logger.info("Starting quality assessment...")
    
    results = {}
    
    # 1. Mask coverage
    coverage = calculate_mask_coverage(img_data)
    results['mask_coverage_percent'] = coverage
    results['coverage_ok'] = 5.0 < coverage < 40.0  # Typical brain is 10-20% of volume
    
    # 2. Brain volume
    volume = calculate_brain_volume(img_data)
    results['brain_volume_cm3'] = volume
    results['volume_ok'] = 800 < volume < 2000  # Typical adult brain: 1000-1500 cm³
    
    # 3. Connected components
    components = check_connected_components(img_data)
    results['connected_components'] = components
    results['components_ok'] = components['num_components'] == 1
    
    # 4. Edge density
    edge_density = calculate_edge_density(img_data)
    results['edge_density'] = edge_density
    # Lower is better - smooth boundary
    results['edge_density_ok'] = edge_density < 50.0
    
    # 5. Intensity statistics
    intensity_stats = calculate_intensity_statistics(img_data)
    results['intensity_stats'] = intensity_stats
    results['intensity_ok'] = intensity_stats['std'] > 0.01  # Has variation
    
    # 6. Mutual information (if reference provided)
    if reference_img is not None:
        mi = calculate_mutual_information(img_data, reference_img)
        results['mutual_information'] = mi
        results['registration_ok'] = mi > 0.3  # Good registration typically > 0.5
    
    # 7. Dice coefficient (if ground truth provided)
    if ground_truth_mask is not None:
        dice_results = calculate_dice_coefficient(img_data, ground_truth_mask)
        results['dice_metrics'] = dice_results
        results['dice_ok'] = dice_results['dice'] > 0.85  # Good overlap typically > 0.9
    
    # Overall pass/fail
    checks = [
        results.get('coverage_ok', False),
        results.get('volume_ok', False),
        results.get('components_ok', False),
        results.get('edge_density_ok', False),
        results.get('intensity_ok', False)
    ]
    
    results['passed_checks'] = sum(checks)
    results['total_checks'] = len(checks)
    results['overall_pass'] = results['passed_checks'] >= (len(checks) - 1)  # Allow 1 failure
    
    logger.info(f"\nQuality Assessment Summary:")
    logger.info(f"  Passed {results['passed_checks']}/{results['total_checks']} checks")
    logger.info(f"  Overall: {'PASS' if results['overall_pass'] else 'FAIL'}")
    
    return results



def print_quality_report(results: Dict[str, any]) -> None:
    """
    Print a formatted quality assessment report.
    
    Args:
        results: Dictionary from assess_quality()
    """
    print("\n" + "="*60)
    print("QUALITY ASSESSMENT REPORT")
    print("="*60)
    
    print(f"\n1. Mask Coverage: {results['mask_coverage_percent']:.2f}%")
    print(f"   Status: {'✓ PASS' if results['coverage_ok'] else '✗ FAIL'}")
    
    print(f"\n2. Brain Volume: {results['brain_volume_cm3']:.2f} cm³")
    print(f"   Status: {'✓ PASS' if results['volume_ok'] else '✗ FAIL'}")
    print(f"   Expected: 800-2000 cm³")
    
    comp = results['connected_components']
    print(f"\n3. Connected Components: {comp['num_components']}")
    print(f"   Largest component: {comp['largest_component_fraction']*100:.1f}%")
    print(f"   Status: {'✓ PASS' if results['components_ok'] else '✗ FAIL'}")
    
    print(f"\n4. Edge Density: {results['edge_density']:.4f}")
    print(f"   Status: {'✓ PASS' if results['edge_density_ok'] else '✗ FAIL'}")
    
    stats = results['intensity_stats']
    print(f"\n5. Intensity Statistics:")
    print(f"   Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")
    print(f"   Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
    print(f"   Status: {'✓ PASS' if results['intensity_ok'] else '✗ FAIL'}")
    
    if 'mutual_information' in results:
        print(f"\n6. Registration Quality (MI): {results['mutual_information']:.4f}")
        print(f"   Status: {'✓ PASS' if results['registration_ok'] else '✗ FAIL'}")
    
    if 'dice_metrics' in results:
        dice = results['dice_metrics']
        check_num = 7 if 'mutual_information' in results else 6
        print(f"\n{check_num}. Ground Truth Comparison:")
        print(f"   Dice Coefficient: {dice['dice']:.4f}")
        print(f"   Jaccard Index: {dice['jaccard']:.4f}")
        print(f"   Sensitivity: {dice['sensitivity']:.4f}")
        print(f"   Precision: {dice['precision']:.4f}")
        print(f"   Intersection: {dice['intersection_voxels']} voxels")
        print(f"   Predicted: {dice['pred_voxels']} | Ground Truth: {dice['gt_voxels']}")
        print(f"   Status: {'✓ PASS' if results['dice_ok'] else '✗ FAIL'}")
        print(f"   (Dice > 0.85 is good, > 0.9 is excellent)")
    
    print(f"\n" + "-"*60)
    print(f"Overall: {'✓✓ PASS ✓✓' if results['overall_pass'] else '✗✗ FAIL ✗✗'}")
    print(f"Passed {results['passed_checks']}/{results['total_checks']} checks")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Example usage
    from utils import load_nifti, setup_logging
    from scrollview import Scroller

    setup_logging("INFO")
    
    # Load a skull-stripped image
    img_path = "./data/sample_data/processed/skull_stripped_final.nii"
    img = load_nifti(img_path)
    
    # Optional: Load ground truth mask for comparison
    # ground_truth_path = "/mask.nii"
    # ground_truth = load_nifti(ground_truth_path)

    # Run quality assessment
    results = assess_quality(img) # Add ground_truth_mask=ground_truth if available
    
    # Print report
    print_quality_report(results)
    Scroller(img.data)