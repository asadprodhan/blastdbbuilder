#!/usr/bin/env python3
# setup.py for blastdbbuilder
from setuptools import setup, find_packages

setup(
    name="blastdbbuilder",
    version="1.0.0",
    author="Asad Prodhan",
    author_email="prodhan82@gmail.com",
    description="Automated genome download, concatenation, and BLAST database builder",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AsadProdhan/blastdbbuilder",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Add any runtime dependencies your package needs
        # e.g., "requests>=2.30", "pandas>=2.0"
    ],
    entry_points={
        "console_scripts": [
            "blastdbbuilder=blastdbbuilder.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
