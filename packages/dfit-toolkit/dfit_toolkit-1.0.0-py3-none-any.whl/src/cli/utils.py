"""
CLI utility functions for Kali Linux style output.
Provides clean, professional formatting like exiftool and other security tools.
"""

import click
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


# Color scheme - Kali Linux style
class Colors:
    """ANSI color codes for terminal output."""
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def print_header(title: str) -> None:
    """Print a formatted header - Kali Linux style."""
    click.echo(f"\n{Colors.BOLD}{Colors.CYAN}[*] {title}{Colors.ENDC}")
    click.echo(f"{Colors.CYAN}{'─' * 70}{Colors.ENDC}")


def print_success(message: str) -> None:
    """Print a success message."""
    click.echo(f"{Colors.GREEN}[+] {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message."""
    click.echo(f"{Colors.RED}[-] {message}{Colors.ENDC}", err=True)


def print_warning(message: str) -> None:
    """Print a warning message."""
    click.echo(f"{Colors.YELLOW}[!] {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    """Print an info message."""
    click.echo(f"{Colors.CYAN}[*] {message}{Colors.ENDC}")


def print_section(title: str) -> None:
    """Print a section header - Kali Linux style."""
    click.echo(f"\n{Colors.BOLD}{Colors.CYAN}[*] {title}{Colors.ENDC}")


def print_key_value(key: str, value: Any, indent: int = 0) -> None:
    """Print a key-value pair - exiftool style."""
    indent_str = " " * indent
    # Format value nicely
    if value is None:
        value_str = "N/A"
    elif isinstance(value, bool):
        value_str = "Yes" if value else "No"
    elif isinstance(value, (list, dict)):
        value_str = json.dumps(value, indent=2)
    else:
        value_str = str(value)
    
    click.echo(f"{indent_str}{Colors.CYAN}{key:<30}{Colors.ENDC} {value_str}")


def print_data(data: Dict[str, Any], title: Optional[str] = None) -> None:
    """Print data in exiftool style - one item per line."""
    if title:
        print_section(title)
    
    if not data:
        print_warning("No data to display")
        return
    
    for key, value in data.items():
        print_key_value(key, value)


def print_tampering_results(results: Dict[str, Any]) -> None:
    """Print tampering analysis results - raw data, no scores."""
    print_header("Tampering Analysis")
    
    # ELA Results
    if "analysis_methods" in results:
        ela = results["analysis_methods"].get("ela", {})
        if ela and "error" not in ela:
            print_section("Error Level Analysis (ELA)")
            print_key_value("Interpretation", ela.get("interpretation", "N/A"))
            if "statistics" in ela:
                stats = ela["statistics"]
                print_key_value("Mean Error", f"{stats.get('mean_error', 0):.6f}")
                print_key_value("Std Error", f"{stats.get('std_error', 0):.6f}")
                print_key_value("Max Error", f"{stats.get('max_error', 0):.2f}")
                print_key_value("Min Error", f"{stats.get('min_error', 0):.2f}")
                print_key_value("Suspicious Pixels", f"{stats.get('suspicious_pixels', 0):,}")
                print_key_value("Total Pixels", f"{stats.get('total_pixels', 0):,}")
                if stats.get('total_pixels', 0) > 0:
                    pct = (stats.get('suspicious_pixels', 0) / stats.get('total_pixels', 1)) * 100
                    print_key_value("Suspicious %", f"{pct:.2f}%")
    
    # Histogram Results
    if "analysis_methods" in results:
        hist = results["analysis_methods"].get("histogram", {})
        if hist and "error" not in hist:
            print_section("Histogram Analysis")
            if "overall" in hist:
                overall = hist["overall"]
                print_key_value("Interpretation", overall.get("interpretation", "N/A"))
                print_key_value("Total Spikes", overall.get("total_spikes", 0))
                print_key_value("Total Gaps", overall.get("total_gaps", 0))
                print_key_value("Average Entropy", f"{overall.get('average_entropy', 0):.4f}")


def print_steganography_results(results: Dict[str, Any]) -> None:
    """Print steganography analysis results - raw data, no scores."""
    print_header("Steganography Analysis")
    
    # LSB Analysis
    if "lsb_analysis" in results:
        lsb = results["lsb_analysis"]
        if lsb and "error" not in lsb:
            print_section("LSB (Least Significant Bit) Analysis")
            print_key_value("Interpretation", lsb.get("interpretation", "N/A"))
            if "channel_analysis" in lsb:
                for channel, data in lsb["channel_analysis"].items():
                    print_key_value(f"  {channel.upper()} Chi-Square", f"{data.get('chi_square', 0):.4f}")
    
    # Statistical Analysis
    if "statistical_analysis" in results:
        stat = results["statistical_analysis"]
        if stat and "error" not in stat:
            print_section("Statistical Analysis")
            print_key_value("Interpretation", stat.get("interpretation", "N/A"))
            if "entropy" in stat:
                entropy = stat["entropy"]
                print_key_value("  Red Entropy", f"{entropy.get('red', 0):.4f}")
                print_key_value("  Green Entropy", f"{entropy.get('green', 0):.4f}")
                print_key_value("  Blue Entropy", f"{entropy.get('blue', 0):.4f}")
    
    # Header Analysis
    if "header_analysis" in results:
        header = results["header_analysis"]
        if header and "error" not in header:
            print_section("Header Analysis")
            print_key_value("Interpretation", header.get("interpretation", "N/A"))
            if header.get("embedded_files_detected"):
                print_key_value("Embedded Files Found", len(header["embedded_files_detected"]))
                for i, file in enumerate(header["embedded_files_detected"], 1):
                    print_key_value(f"  File {i}", file)
    
    # Extracted Data
    if "extracted_data" in results:
        extracted = results["extracted_data"]
        if extracted and "extraction_successful" in extracted and extracted["extraction_successful"]:
            print_section("Extracted Hidden Data")
            print_key_value("Total Bytes Extracted", f"{extracted.get('total_bytes_extracted', 0):,}")
            print_key_value("Total Bits Extracted", f"{extracted.get('total_bits_extracted', 0):,}")
            
            # Show text preview if available
            if extracted.get("text_preview"):
                text_preview = extracted["text_preview"]
                # Show first 200 chars
                preview_text = text_preview[:200] if len(text_preview) > 200 else text_preview
                print_key_value("Text Preview", f"\n{preview_text}")
            
            # Show printable ratio
            if "printable_text_ratio" in extracted:
                ratio = extracted["printable_text_ratio"]
                print_key_value("Printable Text Ratio", f"{ratio*100:.1f}%")
                if ratio > 0.7:
                    print_key_value("Contains", "Likely text data")
                else:
                    print_key_value("Contains", "Likely binary data")


def print_metadata_results(results: Dict[str, Any]) -> None:
    """Print metadata results - exiftool style."""
    print_header("Metadata Analysis")
    
    # File info
    if "file" in results:
        print_section("File Information")
        file_info = results["file"]
        print_key_value("File Path", file_info.get("path", "N/A"))
        size_kb = file_info.get('size_bytes', 0) / 1024
        print_key_value("File Size", f"{size_kb:.2f} KB" if size_kb > 0 else "N/A")
        print_key_value("File Format", file_info.get("format", "N/A"))
        print_key_value("MIME Type", file_info.get("mime", "N/A"))
        dims = file_info.get("dimensions", {})
        if dims.get('width') and dims.get('height'):
            print_key_value("Image Width", f"{dims.get('width')} px")
            print_key_value("Image Height", f"{dims.get('height')} px")
        print_key_value("Color Mode", file_info.get("mode", "N/A"))
    
    # Hashes
    if "hashes" in results:
        print_section("File Hashes")
        hashes = results["hashes"]
        print_key_value("MD5 Hash", hashes.get("md5", "N/A"))
        print_key_value("SHA256 Hash", hashes.get("sha256", "N/A"))
    
    # Camera info
    if "camera" in results:
        camera = results["camera"]
        if any(camera.values()):
            print_section("Camera Information")
            print_key_value("Camera Make", camera.get("Make", "N/A"))
            print_key_value("Camera Model", camera.get("Model", "N/A"))
            print_key_value("Lens Model", camera.get("LensModel", "N/A"))
    
    # Timestamps
    if "timestamps" in results:
        timestamps = results["timestamps"]
        if any(timestamps.values()):
            print_section("Timestamps")
            print_key_value("Date Time Original", timestamps.get("DateTimeOriginal", "N/A"))
            print_key_value("Create Date", timestamps.get("CreateDate", "N/A"))
            print_key_value("Modify Date", timestamps.get("ModifyDate", "N/A"))
            print_key_value("Software", timestamps.get("Software", "N/A"))
    
    # GPS
    if "gps" in results and results["gps"]:
        print_section("GPS Information")
        gps = results["gps"]
        lat = gps.get('lat')
        lon = gps.get('lon')
        if lat and lon:
            print_key_value("GPS Latitude", f"{lat:.8f}")
            print_key_value("GPS Longitude", f"{lon:.8f}")


