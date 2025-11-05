"""
Setup configuration for SafeKey Lab Python SDK
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="safekeylab",
    version="1.0.0",
    author="SafeKey Lab",
    author_email="support@safekeylab.com",
    description="Healthcare Data Privacy & HIPAA Compliance API - Protect sensitive patient data with enterprise-grade PII detection and redaction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.safekeylab.com",
    project_urls={
        "Documentation": "https://docs.safekeylab.com",
        "API Reference": "https://api.safekeylab.com/docs",
        "Homepage": "https://www.safekeylab.com",
        "Support": "https://www.safekeylab.com/support",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "docs"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Security",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
        "async": [
            "aiohttp>=3.8.0",
            "aiofiles>=23.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "safekeylab=safekeylab.cli:main",
        ],
    },
    keywords=[
        "hipaa",
        "healthcare",
        "pii",
        "phi",
        "data-privacy",
        "compliance",
        "redaction",
        "deidentification",
        "medical",
        "patient-data",
        "gdpr",
        "data-protection",
        "mimic",
        "ehr",
        "api",
    ],
    license="Proprietary",
    include_package_data=True,
    zip_safe=False,
)