# src/core/tampering_detector.py
"""
Image tampering detection module.

This module provides functions to detect various types of image tampering
using techniques like Error Level Analysis (ELA) and histogram analysis.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, Optional, Union
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, UnidentifiedImageError
import cv2
import os
import json
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

def validate_image_path(image_path: Union[str, Path]) -> None:
    """
    Validate the image path and file.
    
    Args:
        image_path: Path to the image file
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If there's no read permission
        ValueError: If the file is not a valid image
    """
    path = Path(image_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    if not os.access(str(path), os.R_OK):
        raise PermissionError(f"No read permission for file: {image_path}")
    
    # Check file size is reasonable (between 1KB and 50MB)
    file_size = path.stat().st_size
    if file_size < 1024 or file_size > 50 * 1024 * 1024:  # 1KB to 50MB
        raise ValueError(f"Invalid file size: {file_size} bytes. Expected between 1KB and 50MB")

def error_level_analysis(
    image_path: Union[str, Path], 
    quality: int = 90, 
    scale: int = 10
) -> Dict[str, Any]:
    """
    Perform Error Level Analysis (ELA) to detect potential image tampering.
    
    Args:
        image_path: Path to the image file
        quality: JPEG compression quality for recompression (1-100)
        scale: Brightness scaling factor for difference visualization
        
    Returns:
        Dictionary containing ELA results and analysis
        
    Raises:
        ValueError: If quality or scale parameters are invalid
        IOError: If there's an error reading the image
    """
    # Validate parameters
    if not (1 <= quality <= 100):
        raise ValueError("Quality must be between 1 and 100")
    if scale <= 0:
        raise ValueError("Scale factor must be positive")
    
    temp_path = None
    try:
        # Validate image path and permissions
        validate_image_path(image_path)
        
        # Load original image with explicit error handling
        try:
            with Image.open(image_path) as img:
                original = img.convert('RGB')
        except (UnidentifiedImageError, OSError) as e:
            raise IOError(f"Failed to load image: {e}")
        
        # Create a temporary file in the same directory as the original
        temp_dir = os.path.dirname(os.path.abspath(image_path)) or '.'
        
        # Create temporary recompressed image with a random name to prevent collisions
        import tempfile
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='_ela.jpg',
            dir=temp_dir,
            prefix='tmp_'
        )
        os.close(temp_fd)  # Close the file descriptor as PIL will open the file
        
        try:
            # Save with explicit quality and optimization
            original.save(
                temp_path, 
                'JPEG', 
                quality=quality,
                optimize=True,
                progressive=False
            )
            
            # Load recompressed image with validation
            try:
                recompressed = Image.open(temp_path)
                recompressed.load()  # Force loading to catch any errors
            except (UnidentifiedImageError, OSError) as e:
                raise IOError(f"Failed to load recompressed image: {e}")
            
            # Calculate pixel-wise difference
            difference = ImageChops.difference(original, recompressed)
            
            # Enhance the difference for visualization
            extrema = difference.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            
            if max_diff == 0:
                max_diff = 1  # Avoid division by zero
                
            scale_factor = 255.0 / max_diff * scale / 100.0
            
            # Apply scaling and auto-contrast
            difference = ImageEnhance.Brightness(difference).enhance(scale_factor)
            difference = difference.convert('L')  # Convert to grayscale
            
        finally:
            # Clean up temporary file if it exists
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError as e:
                    logger.warning(f"Failed to remove temporary file {temp_path}: {e}")
        
        # Calculate statistics
        diff_array = np.array(difference)
        stats = {
            'mean_error': float(np.mean(diff_array)),
            'std_error': float(np.std(diff_array)),
            'max_error': float(np.max(diff_array)),
            'min_error': float(np.min(diff_array)),
            'suspicious_pixels': int(np.sum(diff_array > np.percentile(diff_array, 95))),
            'total_pixels': int(diff_array.size)
        }
        
        # Tampering likelihood based on error distribution
        high_error_ratio = stats['suspicious_pixels'] / stats['total_pixels']
        tampering_score = min(high_error_ratio * 100, 100)  # Cap at 100%
        
        return {
            'method': 'Error Level Analysis',
            'quality_used': quality,
            'scale_factor': scale,
            'statistics': stats,
            'tampering_score': round(tampering_score, 2),
            'interpretation': _interpret_ela_score(tampering_score),
            'ela_image_array': diff_array.tolist()  # For saving/visualization
        }
        
    except Exception as e:
        error_msg = f"Error Level Analysis failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'method': 'Error Level Analysis',
            'error': error_msg,
            'tampering_score': 0,
            'interpretation': 'Analysis failed',
            'success': False
        }

def histogram_analysis(image_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Analyze image histogram for tampering indicators.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing histogram analysis results
        
    Raises:
        ValueError: If the image cannot be loaded or processed
        IOError: If there's an error reading the image
    """
    try:
        # Validate image path and permissions
        validate_image_path(image_path)
        
        # Load image with OpenCV
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError("OpenCV could not load the image")
            
        # Check if image was loaded properly
        if image.size == 0:
            raise ValueError("Loaded image is empty")
            
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Calculate histograms for each channel
        hist_r = cv2.calcHist([image_rgb], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([image_rgb], [1], None, [256], [0, 256])
        hist_b = cv2.calcHist([image_rgb], [2], None, [256], [0, 256])
        
        # Analyze histogram characteristics
        def analyze_channel(hist, channel_name):
            hist_flat = hist.flatten()
            
            # Check for unusual spikes or gaps
            spikes = np.sum(hist_flat > np.percentile(hist_flat, 99))
            gaps = np.sum(hist_flat == 0)
            
            # Calculate histogram entropy (randomness measure)
            prob = hist_flat / np.sum(hist_flat)
            prob = prob[prob > 0]  # Remove zeros for log calculation
            entropy = -np.sum(prob * np.log2(prob))
            
            # Detect histogram truncation or stretching
            non_zero_range = np.where(hist_flat > 0)[0]
            if len(non_zero_range) > 0:
                dynamic_range = non_zero_range[-1] - non_zero_range[0]
            else:
                dynamic_range = 0
                
            return {
                'spikes': int(spikes),
                'gaps': int(gaps),
                'entropy': float(entropy),
                'dynamic_range': int(dynamic_range),
                'histogram': hist_flat.tolist()
            }
        
        r_analysis = analyze_channel(hist_r, 'red')
        g_analysis = analyze_channel(hist_g, 'green')  
        b_analysis = analyze_channel(hist_b, 'blue')
        
        # Overall tampering indicators
        total_spikes = r_analysis['spikes'] + g_analysis['spikes'] + b_analysis['spikes']
        total_gaps = r_analysis['gaps'] + g_analysis['gaps'] + b_analysis['gaps']
        avg_entropy = (r_analysis['entropy'] + g_analysis['entropy'] + b_analysis['entropy']) / 3
        
        # Simple tampering score based on anomalies
        tampering_indicators = 0
        if total_spikes > 10:  # Unusual histogram spikes
            tampering_indicators += 1
        if total_gaps > 20:   # Too many histogram gaps
            tampering_indicators += 1
        if avg_entropy < 6.0:  # Low entropy (over-processed)
            tampering_indicators += 1
        if min(r_analysis['dynamic_range'], g_analysis['dynamic_range'], b_analysis['dynamic_range']) < 200:
            tampering_indicators += 1  # Limited dynamic range
            
        tampering_score = (tampering_indicators / 4.0) * 100
        
        return {
            'method': 'Histogram Analysis',
            'channels': {
                'red': r_analysis,
                'green': g_analysis,
                'blue': b_analysis
            },
            'overall': {
                'total_spikes': total_spikes,
                'total_gaps': total_gaps,
                'average_entropy': round(avg_entropy, 3),
                'tampering_score': round(tampering_score, 2),
                'interpretation': _interpret_histogram_score(tampering_score)
            }
        }
        
    except Exception as e:
        error_msg = f"Histogram Analysis failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'method': 'Histogram Analysis', 
            'error': error_msg,
            'tampering_score': 0,
            'interpretation': 'Analysis failed',
            'success': False
        }

def detect_tampering(image_path: Union[str, Path], ela_quality: int = 90) -> Dict[str, Any]:
    """
    Detect potential tampering in an image using multiple analysis techniques.
    
    This is the main function that should be called to perform tampering detection.
    It combines multiple analysis methods and provides a comprehensive result.
    
    Args:
        image_path: Path to the image file
        ela_quality: JPEG quality for ELA recompression (1-100)
        
    Returns:
        Dictionary containing comprehensive tampering analysis results
        
    Example:
        >>> results = detect_tampering("suspicious.jpg")
        >>> print(f"Tampering score: {results['combined_score']}%")
    """
    try:
        # Validate input parameters
        if not isinstance(ela_quality, int) or not (1 <= ela_quality <= 100):
            raise ValueError("ela_quality must be an integer between 1 and 100")
            
        # Initialize result structure
        result = {
            'success': True,
            'image_path': str(image_path),
            'analysis_methods': {},
            'warnings': []
        }
        
        # Run ELA analysis
        try:
            ela_results = error_level_analysis(image_path, quality=ela_quality)
            result['analysis_methods']['ela'] = ela_results
            if 'error' in ela_results:
                result['warnings'].append(f"ELA analysis had issues: {ela_results['error']}")
        except Exception as e:
            logger.error(f"Error during ELA analysis: {str(e)}", exc_info=True)
            result['analysis_methods']['ela'] = {
                'error': str(e),
                'success': False
            }
            result['warnings'].append(f"ELA analysis failed: {str(e)}")
        
        # Run histogram analysis
        try:
            hist_results = histogram_analysis(image_path)
            result['analysis_methods']['histogram'] = hist_results
            if 'error' in hist_results:
                result['warnings'].append(f"Histogram analysis had issues: {hist_results['error']}")
        except Exception as e:
            logger.error(f"Error during histogram analysis: {str(e)}", exc_info=True)
            result['analysis_methods']['histogram'] = {
                'error': str(e),
                'success': False
            }
            result['warnings'].append(f"Histogram analysis failed: {str(e)}")
        
        # Calculate combined score if we have both analyses
        ela_result = result['analysis_methods'].get('ela', {})
        hist_result = result['analysis_methods'].get('histogram', {})
        
        # Check if both analyses succeeded (no 'error' key means success)
        ela_success = 'error' not in ela_result
        hist_success = 'error' not in hist_result
        
        if ela_success and hist_success:
            ela_score = ela_result.get('tampering_score', 0)
            hist_score = hist_result.get('overall', {}).get('tampering_score', 0)
            
            # Weighted average (60% ELA, 40% histogram)
            combined_score = (ela_score * 0.6) + (hist_score * 0.4)
            
            result['combined_score'] = round(combined_score, 2)
            result['confidence'] = _get_confidence_level(combined_score)
            result['recommendation'] = _get_recommendation(combined_score)
            result['success'] = True
        else:
            result['success'] = False
            result['error'] = "One or more analysis methods failed"
        
        return result
        
    except Exception as e:
        error_msg = f"Tampering detection failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg,
            'image_path': str(image_path),
            'analysis_methods': {}
        }

def comprehensive_tampering_analysis(image_path: Union[str, Path], ela_quality: int = 90) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Use detect_tampering() instead for better error handling and more features.
    
    Args:
        image_path: Path to the image file
        ela_quality: JPEG quality for ELA recompression
        
    Returns:
        Combined analysis results
    """
    try:
        # Use the new detect_tampering function
        result = detect_tampering(image_path, ela_quality)
        
        # Convert to the old format for backward compatibility
        if not result.get('success', False):
            return {
                'method': 'Comprehensive Tampering Analysis',
                'error': result.get('error', 'Unknown error'),
                'tampering_score': 0,
                'interpretation': 'Analysis failed'
            }
            
        return {
            'method': 'Comprehensive Tampering Analysis',
            'ela_results': result['analysis_methods'].get('ela', {}),
            'histogram_results': result['analysis_methods'].get('histogram', {}),
            'tampering_score': result.get('combined_score', 0),
            'confidence': result.get('confidence', 'low'),
            'recommendation': result.get('recommendation', 'No recommendation available'),
            'warnings': result.get('warnings', [])
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive_tampering_analysis: {str(e)}", exc_info=True)
        return {
            'method': 'Comprehensive Tampering Analysis',
            'error': str(e),
            'tampering_score': 0,
            'interpretation': 'Analysis failed'
        }

def save_ela_visualization(image_path: str, output_dir: str, quality: int = 90) -> str:
    """
    Generate and save ELA visualization image.
    
    Args:
        image_path: Path to original image
        output_dir: Directory to save visualization
        quality: JPEG quality for ELA
        
    Returns:
        Path to saved ELA image
    """
    ela_result = error_level_analysis(image_path, quality=quality)
    
    if 'ela_image_array' in ela_result:
        ela_array = np.array(ela_result['ela_image_array'], dtype=np.uint8)
        ela_image = Image.fromarray(ela_array, mode='L')
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_ELA.png")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save ELA visualization
        ela_image.save(output_path)
        return output_path
    else:
        raise ValueError("ELA analysis failed, no visualization available")

# Helper functions for interpretation
def _interpret_ela_score(score: float) -> str:
    """Interpret ELA tampering score."""
    if score < 10:
        return "Low probability of tampering"
    elif score < 30:
        return "Moderate probability of tampering" 
    elif score < 60:
        return "High probability of tampering"
    else:
        return "Very high probability of tampering"

def _interpret_histogram_score(score: float) -> str:
    """Interpret histogram tampering score."""
    if score < 25:
        return "Histogram appears natural"
    elif score < 50:
        return "Some histogram anomalies detected"
    elif score < 75:
        return "Significant histogram anomalies"
    else:
        return "Severe histogram anomalies - likely processed"

def _get_confidence_level(score: float) -> str:
    """Get confidence level for combined analysis."""
    if score < 20:
        return "High confidence - likely authentic"
    elif score < 40:
        return "Moderate confidence - possibly authentic"
    elif score < 60:
        return "Moderate confidence - possibly tampered"
    else:
        return "High confidence - likely tampered"

def _get_recommendation(score: float) -> str:
    """Get investigation recommendation."""
    if score < 20:
        return "Image appears authentic - no further analysis needed"
    elif score < 40:
        return "Inconclusive - consider additional forensic methods"
    elif score < 60:
        return "Suspicious - recommend further investigation"
    else:
        return "Highly suspicious - recommend expert forensic analysis"
