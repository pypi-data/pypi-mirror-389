"""
File utility functions for batch processing and file operations.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .metadata_analyzer import extract_metadata
from .tampering_detector import detect_tampering
from .steganography_detector import comprehensive_steganography_analysis

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif'}

def is_supported_file(filepath: str) -> bool:
    """Check if the file has a supported image extension."""
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS

def find_image_files(directory: str, recursive: bool = True) -> Generator[str, None, None]:
    """
    Find all image files in the specified directory.
    
    Args:
        directory: Directory to search for image files
        recursive: If True, search recursively in subdirectories
        
    Yields:
        str: Path to each image file found
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Directory not found: {directory}")
    
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if is_supported_file(file):
                    yield os.path.join(root, file)
    else:
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path) and is_supported_file(item):
                yield full_path

def process_single_image(image_path: str, 
                        analyze_metadata: bool = True,
                        check_tampering: bool = True,
                        check_steganography: bool = True) -> Dict[str, Any]:
    """
    Process a single image file with the specified analysis options.
    
    Args:
        image_path: Path to the image file
        analyze_metadata: Whether to extract metadata
        check_tampering: Whether to check for image tampering
        check_steganography: Whether to check for steganography
        
    Returns:
        Dict containing analysis results
    """
    result = {"file_path": image_path, "error": None}
    
    try:
        if analyze_metadata:
            result["metadata"] = extract_metadata(image_path)
            
        if check_tampering:
            result["tampering_analysis"] = detect_tampering(image_path)
            
        if check_steganography:
            result["steganography_analysis"] = comprehensive_steganography_analysis(image_path)
            
    except Exception as e:
        logger.error(f"Error processing {image_path}: {str(e)}", exc_info=True)
        result["error"] = str(e)
        
    return result

def process_directory(directory: str, 
                    recursive: bool = True,
                    analyze_metadata: bool = True,
                    check_tampering: bool = True,
                    check_steganography: bool = True,
                    max_workers: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Process all images in a directory with the specified analysis options.
    
    Args:
        directory: Directory containing images to process
        recursive: If True, process images in subdirectories as well
        analyze_metadata: Whether to extract metadata
        check_tampering: Whether to check for image tampering
        check_steganography: Whether to check for steganography
        max_workers: Maximum number of worker threads (default: min(32, os.cpu_count() + 4))
        
    Returns:
        List of analysis results for each processed image
    """
    image_files = list(find_image_files(directory, recursive=recursive))
    results = []
    
    if not image_files:
        logger.warning(f"No supported image files found in {directory}")
        return results
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(
                process_single_image, 
                img_path,
                analyze_metadata,
                check_tampering,
                check_steganography
            ): img_path for img_path in image_files
        }
        
        # Process results as they complete
        for future in as_completed(future_to_path):
            img_path = future_to_path[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Processed: {img_path}")
            except Exception as e:
                logger.error(f"Error processing {img_path}: {str(e)}", exc_info=True)
                results.append({"file_path": img_path, "error": str(e)})
    
    return results

def save_results_to_json(results: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        results: List of analysis results
        output_file: Path to the output JSON file
    """
    import json
    from datetime import datetime
    
    output = {
        "analysis_date": datetime.utcnow().isoformat(),
        "total_files_processed": len(results),
        "successful_analyses": sum(1 for r in results if "error" not in r or not r["error"]),
        "failed_analyses": sum(1 for r in results if "error" in r and r["error"]),
        "results": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    logger.info(f"Analysis results saved to {output_file}")
