#!/usr/bin/env python
"""
RyoFaker Setup Configuration
Enterprise data generation library extending Faker with schema-driven,
referential integrity, and data quality features for QA, ETL, and compliance.
"""

from pathlib import Path
from setuptools import find_packages, setup

# Read version from VERSION file
here = Path(__file__).resolve().parent
VERSION = (here / "VERSION").read_text(encoding="utf-8").strip()

# Read long description from README
README = (here / "README.md").read_text(encoding="utf-8")

# Core dependencies
INSTALL_REQUIRES = [
    "Faker>=20.0.0",           # Base Faker library
    "pandas>=2.0.0",            # DataFrame operations
    "pyarrow>=10.0.0",          # Parquet support
    "pyyaml>=6.0",              # YAML schema parsing
    "jsonschema>=4.0.0",        # JSON schema validation
    "networkx>=3.0",            # Dependency graph resolution
    "tqdm>=4.65.0",             # Progress bars
]

# Optional dependencies for specific features
EXTRAS_REQUIRE = {
    "spark": [
        "pyspark>=3.4.0",
    ],
    "cloud": [
        "oci>=2.100.0",             # Oracle Cloud Infrastructure
        "azure-storage-blob>=12.0.0",  # Azure Blob Storage
        "boto3>=1.26.0",            # AWS S3
    ],
    "dev": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "black>=23.0.0",
        "mypy>=1.5.0",
        "sphinx>=7.0.0",
        "sphinx-rtd-theme>=1.3.0",
        "twine>=4.0.0",
        "build>=0.10.0",
        "ruff>=0.1.0",              # Fast linter
    ],
    "all": [
        "pyspark>=3.4.0",
        "oci>=2.100.0",
        "azure-storage-blob>=12.0.0",
        "boto3>=1.26.0",
    ],
}

# Check if the package can be zip-safe
try:
    import pkgutil
    import zipimport
    zip_safe = (
        hasattr(zipimport.zipimporter, "iter_modules")
        or zipimport.zipimporter in pkgutil.iter_importer_modules.registry.keys()
    )
except (ImportError, AttributeError):
    zip_safe = False

setup(
    # Package metadata
    name="RyoFaker",
    version=VERSION,
    description="Enterprise data generation library extending Faker with schema-driven generation, referential integrity, and data quality features.",
    long_description=README,
    long_description_content_type="text/markdown",
    
    # Author information
    author="ADA Data Science Team",
    author_email="data-science@ada.com",
    url="https://github.com/ada/ryofaker",
    project_urls={
        "Documentation": "https://ryofaker.readthedocs.io",
        "Source": "https://github.com/ada/ryofaker",
        "Tracker": "https://github.com/ada/ryofaker/issues",
        "Changelog": "https://github.com/ada/ryofaker/blob/main/CHANGELOG.md",
    },
    
    # License
    license="MIT",
    
    # Package discovery
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "docs"]),
    include_package_data=True,
    zip_safe=zip_safe,
    
    # Python version requirement
    python_requires=">=3.9",
    
    # Dependencies
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    
    # Entry points
    entry_points={
        "console_scripts": [
            "ryofaker=ryofaker.cli:execute_from_command_line",
        ],
        "pytest11": [
            "ryofaker=ryofaker.contrib.pytest.plugin",
        ],
    },
    
    # PyPI classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: Mocking",
        "Topic :: Database",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "faker",
        "fake",
        "data",
        "test",
        "mock",
        "generator",
        "fixtures",
        "synthetic",
        "qa",
        "etl",
        "schema",
        "database",
        "enterprise",
        "india",
        "compliance",
        "gdpr",
        "referential-integrity",
    ],
)
