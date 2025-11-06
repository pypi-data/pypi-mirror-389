# src/core/steganography_detector.py
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image
import os
import json
import struct
import zipfile
import tempfile
import io

def lsb_analysis(image_path: str) -> Dict[str, Any]:
    """
    Perform Least Significant Bit (LSB) analysis to detect hidden data.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing LSB analysis results
    """
    try:
        # Load image
        image = Image.open(image_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(image)
        height, width, channels = img_array.shape
        
        # Extract LSBs for each channel
        lsb_data = {}
        bit_planes = {}
        
        for channel_idx, channel_name in enumerate(['red', 'green', 'blue']):
            channel_data = img_array[:, :, channel_idx]
            
            # Extract LSBs (least significant bits)
            lsb_bits = channel_data & 1  # Bitwise AND with 1 to get LSB
            
            # Calculate statistics
            total_bits = height * width
            ones_count = np.sum(lsb_bits)
            zeros_count = total_bits - ones_count
            
            # Expected randomness for natural images (should be close to 50/50)
            expected_ratio = 0.5
            actual_ratio = ones_count / total_bits
            deviation = abs(actual_ratio - expected_ratio)
            
            # Suspicious if deviation is too low (too random) or follows patterns
            suspicion_score = 0
            if deviation < 0.01:  # Too perfectly random
                suspicion_score += 30
            elif deviation > 0.1:  # Too biased
                suspicion_score += 40
                
            # Check for sequential patterns in LSBs
            lsb_flat = lsb_bits.flatten()
            pattern_score = _detect_lsb_patterns(lsb_flat)
            suspicion_score += pattern_score
            
            lsb_data[channel_name] = {
                'total_bits': int(total_bits),
                'ones_count': int(ones_count),
                'zeros_count': int(zeros_count),
                'ones_ratio': round(actual_ratio, 4),
                'deviation_from_expected': round(deviation, 4),
                'pattern_score': pattern_score,
                'suspicion_score': min(suspicion_score, 100)
            }
            
            # Store bit plane for visualization
            bit_planes[channel_name] = lsb_bits.tolist()
        
        # Overall LSB analysis
        avg_suspicion = np.mean([lsb_data[ch]['suspicion_score'] for ch in ['red', 'green', 'blue']])
        
        return {
            'method': 'LSB Analysis',
            'channels': lsb_data,
            'bit_planes': bit_planes,
            'overall_suspicion_score': round(avg_suspicion, 2),
            'interpretation': _interpret_lsb_score(avg_suspicion),
            'image_dimensions': {'height': height, 'width': width}
        }
        
    except Exception as e:
        return {
            'method': 'LSB Analysis',
            'error': str(e),
            'suspicion_score': 0,
            'interpretation': 'Analysis failed'
        }

def statistical_analysis(image_path: str) -> Dict[str, Any]:
    """
    Perform statistical analysis to detect steganographic content.
    Uses chi-square test and entropy analysis.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing statistical analysis results
    """
    try:
        # Load image
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        img_array = np.array(image)
        
        results = {}
        
        for channel_idx, channel_name in enumerate(['red', 'green', 'blue']):
            channel_data = img_array[:, :, channel_idx].flatten()
            
            # Chi-square test for randomness in LSBs
            chi_square_result = _chi_square_test(channel_data)
            
            # Entropy analysis
            entropy_result = _entropy_analysis(channel_data)
            
            # Histogram analysis for anomalies
            hist_anomalies = _histogram_anomaly_detection(channel_data)
            
            results[channel_name] = {
                'chi_square': chi_square_result,
                'entropy': entropy_result,
                'histogram_anomalies': hist_anomalies
            }
        
        # Calculate overall statistical suspicion score
        overall_score = 0
        for channel in results.values():
            overall_score += channel['chi_square']['suspicion_score']
            overall_score += channel['entropy']['suspicion_score'] 
            overall_score += channel['histogram_anomalies']['suspicion_score']
        
        overall_score = overall_score / 9  # Average across all tests and channels
        
        return {
            'method': 'Statistical Analysis',
            'channels': results,
            'overall_statistical_score': round(overall_score, 2),
            'interpretation': _interpret_statistical_score(overall_score)
        }
        
    except Exception as e:
        return {
            'method': 'Statistical Analysis',
            'error': str(e),
            'statistical_score': 0,
            'interpretation': 'Analysis failed'
        }

def header_analysis(image_path: str) -> Dict[str, Any]:
    """
    Analyze image headers for embedded files or suspicious data segments.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing header analysis results
    """
    try:
        results = {
            'method': 'Header Analysis',
            'suspicious_signatures': [],
            'embedded_files_detected': [],
            'anomalies': []
        }
        
        with open(image_path, 'rb') as f:
            data = f.read()
        
        # Common file signatures to look for
        file_signatures = {
            b'PK\x03\x04': 'ZIP archive',
            b'Rar!': 'RAR archive',
            b'\x89PNG': 'PNG image',
            b'\xff\xd8\xff': 'JPEG image',
            b'GIF8': 'GIF image',
            b'%PDF': 'PDF document',
            b'\x00\x00\x01\x00': 'ICO file',
            b'RIFF': 'RIFF container (AVI/WAV)',
            b'\x1f\x8b\x08': 'GZIP compressed data'
        }
        
        # Look for file signatures beyond the main image header
        image_format = Image.open(image_path).format
        main_header_size = _get_expected_header_size(image_format)
        
        # Search in the data after the main header
        search_data = data[main_header_size:]
        
        for signature, file_type in file_signatures.items():
            positions = []
            start = 0
            while True:
                pos = search_data.find(signature, start)
                if pos == -1:
                    break
                positions.append(pos + main_header_size)
                start = pos + 1
                
            if positions:
                results['suspicious_signatures'].append({
                    'signature': signature.hex(),
                    'file_type': file_type,
                    'positions': positions,
                    'count': len(positions)
                })
        
        # Try to extract embedded ZIP files
        zip_extractions = _extract_embedded_archives(data)
        results['embedded_files_detected'].extend(zip_extractions)
        
        # Check for unusual padding or data at end of file
        end_analysis = _analyze_file_ending(data, image_format)
        if end_analysis['suspicious']:
            results['anomalies'].append(end_analysis)
        
        # Calculate suspicion score
        suspicion_score = 0
        if results['suspicious_signatures']:
            suspicion_score += min(len(results['suspicious_signatures']) * 20, 60)
        if results['embedded_files_detected']:
            suspicion_score += 40
        if results['anomalies']:
            suspicion_score += 20
            
        results['suspicion_score'] = min(suspicion_score, 100)
        results['interpretation'] = _interpret_header_score(suspicion_score)
        
        return results
        
    except Exception as e:
        return {
            'method': 'Header Analysis',
            'error': str(e),
            'suspicion_score': 0,
            'interpretation': 'Analysis failed'
        }

def detect_steganography(image_path: str) -> Dict[str, Any]:
    """
    Perform comprehensive steganography analysis using multiple techniques.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Combined steganography analysis results
    """
    lsb_results = lsb_analysis(image_path)
    statistical_results = statistical_analysis(image_path)
    header_results = header_analysis(image_path)
    
    # Try to extract hidden data
    extraction_results = extract_lsb_data(image_path)
    
    # Combine scores with weights
    lsb_score = lsb_results.get('overall_suspicion_score', 0)
    stat_score = statistical_results.get('overall_statistical_score', 0)
    header_score = header_results.get('suspicion_score', 0)
    
    # Weighted combination (LSB and statistical are more important)
    combined_score = (lsb_score * 0.4 + stat_score * 0.4 + header_score * 0.2)
    
    return {
        'file_analyzed': os.path.abspath(image_path),
        'timestamp': str(np.datetime64('now')),
        'lsb_analysis': lsb_results,
        'statistical_analysis': statistical_results,
        'header_analysis': header_results,
        'extracted_data': extraction_results,
        'combined_assessment': {
            'overall_steganography_score': round(combined_score, 2),
            'confidence_level': _get_stego_confidence_level(combined_score),
            'recommendation': _get_stego_recommendation(combined_score),
            'techniques_detected': _identify_likely_techniques(lsb_results, statistical_results, header_results)
        }
    }

def comprehensive_steganography_analysis(image_path: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Use detect_steganography() instead.
    """
    return detect_steganography(image_path)

def extract_lsb_data(image_path: str, output_file: str = None) -> Dict[str, Any]:
    """
    Attempt to extract hidden data from LSBs.
    
    Args:
        image_path: Path to the image file
        output_file: Optional output file for extracted data
        
    Returns:
        Extraction results
    """
    try:
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        img_array = np.array(image)
        
        # Extract LSBs from all channels
        extracted_bits = []
        for channel in range(3):  # RGB
            channel_data = img_array[:, :, channel]
            lsb_bits = channel_data & 1
            extracted_bits.extend(lsb_bits.flatten())
        
        # Convert bits to bytes
        extracted_bytes = []
        for i in range(0, len(extracted_bits) - 7, 8):
            byte_bits = extracted_bits[i:i+8]
            byte_value = 0
            for j, bit in enumerate(byte_bits):
                byte_value |= (bit << j)
            extracted_bytes.append(byte_value)
        
        # Try to interpret as text
        try:
            extracted_text = bytes(extracted_bytes).decode('utf-8', errors='ignore')
            text_portion = extracted_text[:1000]  # First 1000 chars
            printable_ratio = sum(1 for c in text_portion if c.isprintable()) / len(text_portion) if text_portion else 0
        except:
            extracted_text = ""
            printable_ratio = 0
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(bytes(extracted_bytes))
        
        return {
            'method': 'LSB Data Extraction',
            'total_bits_extracted': len(extracted_bits),
            'total_bytes_extracted': len(extracted_bytes),
            'output_file': output_file,
            'text_preview': extracted_text[:500] if extracted_text else None,
            'printable_text_ratio': round(printable_ratio, 3),
            'likely_contains_text': printable_ratio > 0.7,
            'extraction_successful': True
        }
        
    except Exception as e:
        return {
            'method': 'LSB Data Extraction',
            'error': str(e),
            'extraction_successful': False
        }

# Helper functions
def _detect_lsb_patterns(lsb_data: np.ndarray) -> int:
    """Detect patterns in LSB data that might indicate steganography."""
    # Check for runs of consecutive bits
    runs = []
    current_run = 1
    for i in range(1, len(lsb_data)):
        if lsb_data[i] == lsb_data[i-1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    
    # Long runs might indicate embedded data
    long_runs = [r for r in runs if r > 10]
    pattern_score = min(len(long_runs) * 5, 30)
    
    return pattern_score

def _chi_square_test(data: np.ndarray) -> Dict[str, Any]:
    """Perform chi-square test on pixel data."""
    # Extract LSBs
    lsb_data = data & 1
    
    # Count 0s and 1s
    ones = np.sum(lsb_data)
    zeros = len(lsb_data) - ones
    
    # Expected counts (should be roughly equal for natural images)
    expected = len(lsb_data) / 2
    
    # Chi-square statistic
    if expected > 0:
        chi_square = ((ones - expected) ** 2 + (zeros - expected) ** 2) / expected
    else:
        chi_square = 0
    
    # Suspicion score based on chi-square value
    # Lower values might indicate steganography (too random)
    # Higher values might indicate bias
    suspicion = 0
    if chi_square < 0.1:
        suspicion = 40  # Too random
    elif chi_square > 10:
        suspicion = 30  # Too biased
    
    return {
        'chi_square_value': round(chi_square, 4),
        'ones_count': int(ones),
        'zeros_count': int(zeros),
        'suspicion_score': suspicion
    }

def _entropy_analysis(data: np.ndarray) -> Dict[str, Any]:
    """Calculate entropy of pixel data."""
    # Calculate entropy
    _, counts = np.unique(data, return_counts=True)
    probabilities = counts / len(data)
    entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
    
    # High entropy might indicate compressed/encrypted hidden data
    # Low entropy might indicate simple hidden data
    max_entropy = 8.0  # Maximum entropy for 8-bit data
    normalized_entropy = entropy / max_entropy
    
    suspicion = 0
    if normalized_entropy > 0.95:  # Very high entropy
        suspicion = 35
    elif normalized_entropy < 0.1:  # Very low entropy  
        suspicion = 25
    
    return {
        'entropy': round(entropy, 4),
        'normalized_entropy': round(normalized_entropy, 4),
        'suspicion_score': suspicion
    }

def _histogram_anomaly_detection(data: np.ndarray) -> Dict[str, Any]:
    """Detect histogram anomalies that might indicate steganography."""
    hist, _ = np.histogram(data, bins=256, range=(0, 255))
    
    # Look for unusual patterns
    anomalies = 0
    
    # Check for too many zeros or peaks
    zero_bins = np.sum(hist == 0)
    if zero_bins > 100:  # Too many empty bins
        anomalies += 15
        
    # Check for unusual spikes
    mean_count = np.mean(hist)
    spikes = np.sum(hist > mean_count * 3)
    if spikes > 10:
        anomalies += 20
    
    return {
        'zero_bins': int(zero_bins),
        'histogram_spikes': int(spikes),
        'suspicion_score': min(anomalies, 50)
    }

def _get_expected_header_size(image_format: str) -> int:
    """Get expected header size for different image formats."""
    header_sizes = {
        'JPEG': 20,
        'PNG': 33,
        'GIF': 13,
        'BMP': 54,
        'TIFF': 26
    }
    return header_sizes.get(image_format, 50)

def _extract_embedded_archives(data: bytes) -> List[Dict[str, Any]]:
    """Try to extract embedded ZIP files."""
    extracted = []
    
    # Look for ZIP signature
    zip_start = data.find(b'PK\x03\x04')
    if zip_start != -1:
        try:
            # Try to extract the ZIP
            zip_data = data[zip_start:]
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(zip_data)
                temp_file.flush()
                
                with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    extracted.append({
                        'type': 'ZIP Archive',
                        'position': zip_start,
                        'files': file_list[:10],  # First 10 files
                        'total_files': len(file_list)
                    })
        except:
            # ZIP signature found but not valid ZIP
            extracted.append({
                'type': 'Suspicious ZIP signature',
                'position': zip_start,
                'note': 'ZIP signature found but archive is corrupted or incomplete'
            })
    
    return extracted

def _analyze_file_ending(data: bytes, image_format: str) -> Dict[str, Any]:
    """Analyze the end of the file for suspicious data."""
    # Look at last 1KB of file
    tail = data[-1024:] if len(data) > 1024 else data
    
    # Check for non-null bytes at the end (suspicious for some formats)
    non_null_at_end = len(tail.rstrip(b'\x00'))
    
    # For JPEG, should end with FFD9
    suspicious = False
    reason = ""
    
    if image_format == 'JPEG' and not data.endswith(b'\xff\xd9'):
        suspicious = True
        reason = "JPEG does not end with expected marker (FFD9)"
    elif non_null_at_end > 100:  # More than 100 non-null bytes in tail
        suspicious = True
        reason = f"Unusual amount of data at end of file ({non_null_at_end} bytes)"
    
    return {
        'suspicious': suspicious,
        'reason': reason,
        'tail_non_null_bytes': non_null_at_end
    }

# Interpretation functions
def _interpret_lsb_score(score: float) -> str:
    """Interpret LSB analysis score."""
    if score < 20:
        return "Low probability of LSB steganography"
    elif score < 40:
        return "Moderate probability of LSB steganography"
    elif score < 70:
        return "High probability of LSB steganography"
    else:
        return "Very high probability of LSB steganography"

def _interpret_statistical_score(score: float) -> str:
    """Interpret statistical analysis score."""
    if score < 25:
        return "Statistical properties appear normal"
    elif score < 50:
        return "Some statistical anomalies detected"
    elif score < 75:
        return "Significant statistical anomalies"
    else:
        return "Severe statistical anomalies - likely hidden data"

def _interpret_header_score(score: float) -> str:
    """Interpret header analysis score."""
    if score == 0:
        return "No embedded files or suspicious headers detected"
    elif score < 30:
        return "Minor header anomalies detected"
    elif score < 60:
        return "Suspicious headers or embedded files detected"
    else:
        return "Multiple embedded files or major header anomalies detected"

def _get_stego_confidence_level(score: float) -> str:
    """Get confidence level for steganography analysis."""
    if score < 15:
        return "High confidence - no steganography detected"
    elif score < 35:
        return "Moderate confidence - possibly clean"
    elif score < 60:
        return "Moderate confidence - possibly contains hidden data"
    else:
        return "High confidence - likely contains hidden data"

def _get_stego_recommendation(score: float) -> str:
    """Get recommendation for steganography analysis."""
    if score < 15:
        return "No steganographic content detected - image appears clean"
    elif score < 35:
        return "Low suspicion - consider additional analysis if needed"
    elif score < 60:
        return "Moderate suspicion - recommend detailed investigation"
    else:
        return "High suspicion - recommend expert steganographic analysis"

def _identify_likely_techniques(lsb_results: Dict, stat_results: Dict, header_results: Dict) -> List[str]:
    """Identify likely steganographic techniques used."""
    techniques = []
    
    if lsb_results.get('overall_suspicion_score', 0) > 40:
        techniques.append("LSB (Least Significant Bit)")
    
    if stat_results.get('overall_statistical_score', 0) > 50:
        techniques.append("Statistical steganography")
    
    if header_results.get('suspicion_score', 0) > 30:
        techniques.append("File embedding/header manipulation")
    
    if not techniques:
        techniques.append("No specific technique identified")
    
    return techniques
