#!/usr/bin/env python3
"""
DFIT - Digital Image Forensics Toolkit
Setup script for package installation
"""

from setuptools import setup, find_packages
import os

# Read the long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dfit-toolkit",
    version="1.0.0",
    author="C0d3-cr4f73r",
    author_email="",
    description="A comprehensive command-line forensics toolkit for digital image analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/C0d3-cr4f73r/DFIT",
    project_urls={
        "Bug Tracker": "https://github.com/C0d3-cr4f73r/DFIT/issues",
        "Documentation": "https://github.com/C0d3-cr4f73r/DFIT#readme",
        "Source Code": "https://github.com/C0d3-cr4f73r/DFIT",
    },
    packages=find_packages(exclude=["tests", "tests.*", "*.tests", "*.tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Legal Industry",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "dfit=src.cli.main:cli",
        ],
    },
    keywords=[
        "forensics", "image-analysis", "steganography", "tampering-detection",
        "metadata", "EXIF", "digital-forensics", "security", "CLI"
    ],
    include_package_data=True,
    zip_safe=False,
)
