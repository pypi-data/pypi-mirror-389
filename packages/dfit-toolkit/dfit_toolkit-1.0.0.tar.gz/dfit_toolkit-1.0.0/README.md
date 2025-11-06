# 🔍 DFIT - Digital Image Forensics Toolkit

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive **command-line forensics toolkit** for digital image analysis. Detect tampering, extract hidden data, analyze metadata, and identify steganography.

## 🎯 Key Features

- **Metadata Extraction** - EXIF data, GPS coordinates, timestamps, file hashes
- **Tampering Detection** - Error Level Analysis (ELA) for pixel-level anomalies
- **Steganography Detection** - LSB analysis and statistical detection
- **Hidden Data Extraction** - Extract embedded data from images
- **Batch Processing** - Process entire directories recursively
- **Professional Output** - Color-coded console, JSON export, HTML reports

## 📋 Requirements

- Python 3.8+
- PIL/Pillow, OpenCV, NumPy, Click, ExifRead

## 🚀 Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Simple installation
pip install dfit-toolkit

# Or with pipx for isolated environment
pipx install dfit-toolkit

# Verify installation
dfit --version
```

### Option 2: Install from Source

```bash
git clone https://github.com/C0d3-cr4f73r/DFIT.git
cd DFIT
pip install -e .

# Or with virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## 📖 Usage

```bash
# Extract metadata
dfit metadata -i image.jpg

# Detect tampering
dfit detect-tampering -i image.jpg

# Scan for steganography
dfit scan-stego -i image.jpg

# Extract hidden data
dfit extract -i image.jpg -o secret.bin

# Comprehensive analysis
dfit analyze -i image.jpg

# Batch processing
dfit batch -i ./images --recursive

# Export results to JSON
dfit metadata -i image.jpg -o report.json
```

## 🧪 Testing

```bash
python3 -m pytest tests/ -v
# Expected: 23/23 tests passing
```

## 🐳 Docker

```bash
docker build -t dfit:latest .
docker run --rm dfit:latest --help
docker-compose up --build
```

## 📚 Documentation

- **[CLI Guide](docs/CLI_GUIDE.md)** - Detailed command reference
- **[Docker Guide](docs/DOCKER_GUIDE.md)** - Docker setup
- **[Quick Start](docs/QUICK_START.md)** - Get started in 5 minutes
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Architecture overview

## 🎓 Real-World Use Cases

- **Law Enforcement** - Verify evidence authenticity
- **Journalism** - Verify image authenticity before publication
- **Cybersecurity** - Analyze malware delivery images
- **Insurance & Legal** - Verify claim authenticity

## 📁 Project Structure

```
src/
├── cli/          # CLI interface
├── core/         # Analysis modules
└── utils/        # Utilities

tests/            # Test suite (23 tests)
docs/             # Documentation
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.


---

**Made with ❤️ for digital forensics professionals**
