"""
Setup script for bccr-exchange-rates.

This file is provided for backwards compatibility with older pip versions.
Modern installations should use pyproject.toml.
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bccr-exchange-rates",
    version="1.0.0",
    author="Mauricio Loría",
    description="Python library for scraping Costa Rican exchange rates from BCCR",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jloria13/bccr-exchange-rates",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/jloria13/bccr-exchange-rates/issues",
        "Source": "https://github.com/jloria13/bccr-exchange-rates",
    },
)
