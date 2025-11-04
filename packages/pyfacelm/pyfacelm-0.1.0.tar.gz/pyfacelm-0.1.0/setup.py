#!/usr/bin/env python3
"""
Setup script for PyfaceLM.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="pyfacelm",
    version="0.1.0",
    author="John Wilson IV",
    author_email="john@example.com",
    description="Minimal-dependency Python wrapper for OpenFace CLNF facial landmark detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/johnwilsoniv/pyfacelm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.0",
    ],
    extras_require={
        "viz": ["opencv-python-headless>=4.5.0"],
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=20.8b1",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "pyfacelm=pyfacelm.cli:main",  # Optional CLI in future
        ],
    },
    include_package_data=True,
    package_data={
        "pyfacelm": ["*.md"],
    },
    keywords=[
        "face",
        "facial landmarks",
        "openface",
        "clnf",
        "mtcnn",
        "computer vision",
        "facial analysis",
    ],
    project_urls={
        "Bug Reports": "https://github.com/johnwilsoniv/pyfacelm/issues",
        "Source": "https://github.com/johnwilsoniv/pyfacelm",
        "Documentation": "https://github.com/johnwilsoniv/pyfacelm/blob/main/README.md",
    },
)
