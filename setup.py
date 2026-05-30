#!/usr/bin/env python3
"""Setup script for MiroFish."""

from setuptools import setup, find_packages

setup(
    name="mirofish",
    version="0.1.0",
    author="MiroFish Team",
    description="Production-grade swarm-intelligence prediction engine",
    long_description=open("README.md").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "mypy>=0.900",
        ],
        "nlp": [
            "nltk>=3.6.0",
            "spacy>=3.0.0",
        ],
        "pdf": [
            "PyPDF2>=2.0.0",
        ],
    },
)
