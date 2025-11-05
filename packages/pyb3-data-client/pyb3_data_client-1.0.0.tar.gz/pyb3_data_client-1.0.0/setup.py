"""
Setup script for pyb3-data-client Python SDK
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="pyb3-data-client",
    version="1.0.0",
    description="Python client for B3 Market Data API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pedro Todescan",
    author_email="pedrotodescan@gmail.com",
    url="https://github.com/PedroDnT/pyb3",
    packages=find_packages(),
    package_data={
        "pyb3_data_client": ["*.py"],
    },
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
        "polars>=0.20.0",
        "pyarrow>=15.0.0",
    ],
    extras_require={
        "pandas": ["pandas>=2.0.0"],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=24.0.0",
            "ruff>=0.1.0",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="b3 bovespa stock market data api finance brazil pyb3",
    project_urls={
        "Documentation": "https://api.b3data.com/docs",
        "Source": "https://github.com/PedroDnT/pyb3",
        "Tracker": "https://github.com/PedroDnT/pyb3/issues",
        "Homepage": "https://github.com/PedroDnT/pyb3",
    },
    zip_safe=False,
)
