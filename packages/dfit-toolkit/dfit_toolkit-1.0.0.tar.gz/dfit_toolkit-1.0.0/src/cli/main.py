# src/cli/main.py - Complete DIFT CLI with all modules
import json
import os
import click
from src.core.metadata_analyzer import extract_metadata
from src.core.tampering_detector import detect_tampering, save_ela_visualization
from src.core.steganography_detector import detect_steganography, extract_lsb_data
from src.core.gps_utilities import extract_gps_coordinates_exifread, generate_gps_html_map
from src.core.file_utils import process_directory, save_results_to_json
from src.cli.utils import (
    print_header, print_success, print_error, print_warning, print_info,
    print_section, print_key_value, print_data,
    print_tampering_results, print_steganography_results, print_metadata_results,
    Colors
)
from src.cli.completion import PathCompleter

@click.group()
@click.version_option(version="1.0.0", prog_name="DFIT")
def cli():
    """
    🔍 DFIT - Digital Image Forensics Toolkit
    
    A comprehensive CLI tool for digital image forensics analysis.
    
    Features:
    • Metadata extraction (EXIF, GPS, timestamps, hashes)
    • Tampering detection (ELA, histogram analysis)
    • Steganography detection (LSB, statistical, header analysis)
    • Batch processing for multiple images
    • HTML and JSON report generation
    
    Examples:
    
      # Analyze metadata
      dfit metadata -i image.jpg --pretty
      
      # Detect tampering
      dfit detect-tampering -i image.jpg --save-visualization
      
      # Scan for steganography
      dfit scan-stego -i image.jpg --extract
      
      # Comprehensive analysis
      dfit analyze -i image.jpg --output-dir ./results
      
      # Batch process directory
      dfit batch -i ./images --recursive --modules all
      
      # Interactive guided analysis
      dfit interactive
    
    For detailed help on any command, use: dfit COMMAND --help
    """
    pass

@cli.command("metadata")
@click.option("--input", "-i", "input_path", required=True, type=click.Path(exists=True), 
              help="Image file to analyze", shell_complete=PathCompleter.complete_image_files)
@click.option("--json-out", "-o", type=click.Path(dir_okay=False), 
              help="Write JSON output to file", shell_complete=PathCompleter.complete_path)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def metadata_cmd(input_path, json_out, verbose):
    """
    Extract and analyze image metadata.
    
    This command extracts comprehensive metadata including:
    • File information (size, format, dimensions)
    • File hashes (MD5, SHA256)
    • Camera information (make, model, lens)
    • Timestamps (creation, modification dates)
    • GPS coordinates (if available)
    • EXIF data (raw and processed)
    
    Examples:
    
      dfit metadata -i photo.jpg
      dfit metadata -i photo.jpg -o metadata.json
      dfit metadata -i photo.jpg -v
    """
    try:
        print_info(f"Analyzing metadata: {input_path}")
        data = extract_metadata(input_path)
        
        # Display formatted output
        print_metadata_results(data)
        
        # Save JSON if requested
        if json_out:
            os.makedirs(os.path.dirname(json_out) or ".", exist_ok=True)
            with open(json_out, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            print_success(f"Metadata JSON saved: {json_out}")
            
    except Exception as e:
        print_error(f"Metadata extraction failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise SystemExit(1)

@cli.command("detect-tampering")
@click.option("--input", "-i", "input_path", required=True, type=click.Path(exists=True), 
              help="Image file to analyze", shell_complete=PathCompleter.complete_image_files)
@click.option("--quality", "-q", default=90, type=click.IntRange(1, 100), help="JPEG quality for ELA (1-100)")
@click.option("--save-visualization", is_flag=True, help="Save ELA visualization image")
@click.option("--save-json", "-o", type=click.Path(dir_okay=False), 
              help="Save JSON report to file (optional)", shell_complete=PathCompleter.complete_path)
def detect_tampering_cmd(input_path, quality, save_visualization, save_json):
    """
    Detect image tampering using Error Level Analysis (ELA) and histogram analysis.
    
    Shows raw analysis data to help you determine if image has been tampered with.
    
    Examples:
    
      dfit detect-tampering -i image.jpg
      dfit detect-tampering -i image.jpg --save-visualization
      dfit detect-tampering -i image.jpg -o report.json
    """
    try:
        print_info(f"Analyzing image: {input_path}")
        print_info(f"Using ELA quality: {quality}")
        
        # Perform tampering detection
        results = detect_tampering(input_path, ela_quality=quality)
        
        # Display results using Kali Linux style (on screen immediately)
        print_tampering_results(results)
        
        # Save visualization if requested
        if save_visualization:
            try:
                output_dir = "./output"
                os.makedirs(output_dir, exist_ok=True)
                ela_path = save_ela_visualization(input_path, output_dir, quality)
                print_success(f"ELA visualization saved: {ela_path}")
            except Exception as viz_error:
                print_warning(f"Could not save visualization: {viz_error}")
        
        # Save JSON report only if explicitly requested
        if save_json:
            os.makedirs(os.path.dirname(save_json) or ".", exist_ok=True)
            with open(save_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print_success(f"JSON report saved: {save_json}")
            
    except Exception as e:
        print_error(f"Tampering analysis failed: {e}")
        raise SystemExit(1)

# ========== NEW STEGANOGRAPHY DETECTION COMMANDS ==========

@cli.command("scan-stego")
@click.option("--input", "-i", "input_path", required=True, type=click.Path(exists=True), 
              help="Image file to analyze", shell_complete=PathCompleter.complete_image_files)
@click.option("--methods", default="all", help="Analysis methods: lsb, statistical, headers, or all")
@click.option("--extract", is_flag=True, help="Attempt to extract hidden data")
@click.option("--save-json", "-o", type=click.Path(dir_okay=False), 
              help="Save JSON report to file (optional)", shell_complete=PathCompleter.complete_path)
def scan_stego_cmd(input_path, methods, extract, save_json):
    """
    Detect steganographic content using LSB, statistical, and header analysis.
    
    Shows raw analysis data to help you determine if image contains hidden data.
    
    Examples:
    
      dfit scan-stego -i image.jpg
      dfit scan-stego -i image.jpg --extract
      dfit scan-stego -i image.jpg -o report.json
    """
    try:
        print_info(f"Scanning for steganographic content: {input_path}")
        print_info(f"Methods: {methods}")
        
        # Perform steganography detection
        results = detect_steganography(input_path)
        
        # Display results using Kali Linux style (on screen immediately)
        print_steganography_results(results)
        
        # Attempt extraction if requested
        if extract:
            try:
                print_info("Attempting LSB data extraction...")
                output_dir = "./stego_output"
                os.makedirs(output_dir, exist_ok=True)
                extract_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_path))[0]}_extracted_data.bin")
                extract_results = extract_lsb_data(input_path, extract_file)
                
                if extract_results['extraction_successful']:
                    print_success(f"Extracted {extract_results['total_bytes_extracted']} bytes -> {extract_file}")
                    if extract_results['likely_contains_text']:
                        print_info(f"Likely contains text data (printable ratio: {extract_results['printable_text_ratio']})")
                        if extract_results['text_preview']:
                            print_info(f"Text preview: {extract_results['text_preview'][:100]}...")
                else:
                    print_warning(f"Extraction failed: {extract_results.get('error', 'Unknown error')}")
            except Exception as extract_error:
                print_warning(f"Could not extract data: {extract_error}")
        
        # Save JSON report only if explicitly requested
        if save_json:
            os.makedirs(os.path.dirname(save_json) or ".", exist_ok=True)
            with open(save_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print_success(f"JSON report saved: {save_json}")
            
    except Exception as e:
        print_error(f"Steganography analysis failed: {e}")
        raise SystemExit(1)

@cli.command("extract")
@click.option("--input", "-i", "input_path", required=True, type=click.Path(exists=True), 
              help="Image file to analyze", shell_complete=PathCompleter.complete_image_files)
@click.option("--output", "-o", "output_file", required=True, type=click.Path(dir_okay=False), 
              help="Output file for extracted data", shell_complete=PathCompleter.complete_path)
@click.option("--method", default="lsb", type=click.Choice(['lsb']), help="Extraction method")
def extract_cmd(input_path, output_file, method):
    """
    Extract hidden data from image using specified method.
    
    Examples:
    
      dfit extract -i image.jpg -o extracted.bin
      dfit extract -i image.jpg -o extracted.bin --method lsb
    """
    try:
        print_info(f"Extracting hidden data from: {input_path}")
        print_info(f"Method: {method.upper()}")
        print_info(f"Output: {output_file}")
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        
        if method == "lsb":
            results = extract_lsb_data(input_path, output_file)
            
            if results['extraction_successful']:
                print_header("Extraction Successful")
                print_key_value("Total Bits Extracted", f"{results['total_bits_extracted']:,}")
                print_key_value("Total Bytes Extracted", f"{results['total_bytes_extracted']:,}")
                print_key_value("Output File", output_file)
                
                if results['likely_contains_text']:
                    print_success("Likely contains text data!")
                    print_key_value("Printable Text Ratio", f"{results['printable_text_ratio']:.3f}")
                    if results['text_preview']:
                        print_key_value("Preview", results['text_preview'][:200])
                else:
                    print_warning("May contain binary data or no meaningful content")
                    
            else:
                print_error("Extraction failed")
                print_error(f"Error: {results.get('error', 'Unknown error')}")
                raise SystemExit(1)
        
    except Exception as e:
        print_error(f"Extraction failed: {e}")
        raise SystemExit(1)

# ========== COMPREHENSIVE ANALYSIS COMMAND ==========

@cli.command("analyze")
@click.option("--input", "-i", "input_path", required=True, type=click.Path(exists=True), 
              help="Image file to analyze", shell_complete=PathCompleter.complete_image_files)
@click.option("--modules", default="all", help="Modules to run: metadata, tampering, stego, or all")
@click.option("--save-visualizations", is_flag=True, help="Save all available visualizations")
@click.option("--extract-data", is_flag=True, help="Attempt to extract hidden data if detected")
@click.option("--save-json", "-o", type=click.Path(dir_okay=False), 
              help="Save JSON report to file (optional)", shell_complete=PathCompleter.complete_path)
def analyze_cmd(input_path, modules, save_visualizations, extract_data, save_json):
    """
    Run comprehensive forensic analysis using all available modules.
    
    Displays results on screen immediately. Optionally saves JSON report.
    
    Examples:
    
      dfit analyze -i image.jpg
      dfit analyze -i image.jpg --modules metadata,tampering
      dfit analyze -i image.jpg --save-visualizations
      dfit analyze -i image.jpg -o report.json
    """
    try:
        print_info(f"Running comprehensive analysis: {input_path}")
        print_info(f"Modules: {modules}")
        
        all_results = {}
        
        # Run metadata analysis
        if modules == "all" or "metadata" in modules:
            print_info("Running metadata analysis...")
            metadata_results = extract_metadata(input_path)
            all_results['metadata'] = metadata_results
            print_metadata_results(metadata_results)
            print_success("Metadata analysis complete")
        
        # Run tampering detection
        if modules == "all" or "tampering" in modules:
            print_info("Running tampering detection...")
            tampering_results = detect_tampering(input_path)
            all_results['tampering'] = tampering_results
            print_tampering_results(tampering_results)
            
            if save_visualizations:
                try:
                    output_dir = "./analysis_results"
                    os.makedirs(output_dir, exist_ok=True)
                    ela_path = save_ela_visualization(input_path, output_dir)
                    print_success(f"ELA visualization saved: {ela_path}")
                except Exception as viz_error:
                    print_warning(f"Could not save visualization: {viz_error}")
            
            print_success("Tampering detection complete")
        
        # Run steganography analysis
        if modules == "all" or "stego" in modules:
            print_info("Running steganography analysis...")
            stego_results = detect_steganography(input_path)
            all_results['steganography'] = stego_results
            print_steganography_results(stego_results)
            
            # Extract data if requested and suspicious
            if extract_data and stego_results['combined_assessment']['overall_steganography_score'] > 30:
                try:
                    output_dir = "./analysis_results"
                    os.makedirs(output_dir, exist_ok=True)
                    base_name = os.path.splitext(os.path.basename(input_path))[0]
                    extract_file = os.path.join(output_dir, f"{base_name}_extracted_data.bin")
                    extract_results = extract_lsb_data(input_path, extract_file)
                    all_results['extraction'] = extract_results
                    if extract_results['extraction_successful']:
                        print_success(f"Data extracted: {extract_file}")
                except Exception as extract_error:
                    print_warning(f"Could not extract data: {extract_error}")
            
            print_success("Steganography analysis complete")
        
        # Save JSON report only if explicitly requested
        if save_json:
            os.makedirs(os.path.dirname(save_json) or ".", exist_ok=True)
            with open(save_json, 'w', encoding='utf-8') as f:
                json.dump({
                    'file_analyzed': os.path.abspath(input_path),
                    'modules_run': modules,
                    'results': all_results
                }, f, indent=2, default=str)
            print_success(f"JSON report saved: {save_json}")
        
    except Exception as e:
        print_error(f"Comprehensive analysis failed: {e}")
        raise SystemExit(1)

# ========== BATCH PROCESSING COMMAND ==========

@cli.command("batch")
@click.option("--input-dir", "-i", "input_dir", required=True, type=click.Path(exists=True, file_okay=False), help="Directory containing images to analyze")
@click.option("--output-dir", "-o", default="./batch_results", help="Directory to save batch analysis results")
@click.option("--recursive", "-r", is_flag=True, help="Recursively process subdirectories")
@click.option("--modules", default="all", help="Modules to run: metadata, tampering, stego, or all")
@click.option("--max-workers", "-w", default=None, type=int, help="Maximum number of parallel workers")
@click.option("--save-json", is_flag=True, help="Save comprehensive JSON report")
def batch_cmd(input_dir, output_dir, recursive, modules, max_workers, save_json):
    """Batch process all images in a directory."""
    try:
        click.echo(f"[INFO] Starting batch analysis")
        click.echo(f"[INFO] Input directory: {input_dir}")
        click.echo(f"[INFO] Output directory: {output_dir}")
        click.echo(f"[INFO] Recursive: {recursive}")
        click.echo(f"[INFO] Modules: {modules}")
        
        # Determine which analyses to run
        analyze_metadata = modules == "all" or "metadata" in modules
        check_tampering = modules == "all" or "tampering" in modules
        check_steganography = modules == "all" or "stego" in modules
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Process directory
        click.echo(f"\n🔄 Processing images...")
        results = process_directory(
            input_dir,
            recursive=recursive,
            analyze_metadata=analyze_metadata,
            check_tampering=check_tampering,
            check_steganography=check_steganography,
            max_workers=max_workers
        )
        
        # Display summary
        click.echo(f"\n📊 BATCH ANALYSIS COMPLETE")
        click.echo(f"{'='*50}")
        click.echo(f"Total images processed: {len(results)}")
        
        successful = sum(1 for r in results if "error" not in r or not r["error"])
        failed = len(results) - successful
        
        click.echo(f"Successful: {successful}")
        click.echo(f"Failed: {failed}")
        
        # Save results to JSON if requested
        if save_json:
            json_file = os.path.join(output_dir, "batch_analysis_report.json")
            save_results_to_json(results, json_file)
            click.echo(f"\n📄 Comprehensive report saved: {json_file}")
        
        # Save individual results summary
        summary_file = os.path.join(output_dir, "batch_summary.json")
        summary = {
            "total_processed": len(results),
            "successful": successful,
            "failed": failed,
            "modules_run": modules,
            "results": results
        }
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        click.echo(f"📁 Results saved to: {output_dir}")
        click.echo(f"✅ Batch processing complete!")
        
    except Exception as e:
        click.echo(f"[ERROR] Batch processing failed: {e}", err=True)
        raise SystemExit(1)

if __name__ == "__main__":
    cli()
