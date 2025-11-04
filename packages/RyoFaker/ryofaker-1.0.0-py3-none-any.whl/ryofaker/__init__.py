"""
RyoFaker - Enterprise Data Generation Library
==============================================

RyoFaker extends Faker with enterprise-grade features for QA, ETL, and data science workflows.

Key Features:
- Schema-driven data generation from JSON/YAML
- Referential integrity with automatic FK management
- Data quality testing (nulls, duplicates, violations)
- Time-series and CDC event simulation
- India-specific providers (PAN, Aadhaar, GSTIN, IFSC, IMEI)
- Multi-format output (Pandas, PySpark, Parquet, CSV, SQL, Cloud)

Quick Start:
    >>> from ryofaker import RyoFaker
    >>> rf = RyoFaker('en_IN')
    >>> print(rf.pan())  # ABCDE1234F
    >>> print(rf.name())  # Aryan Mullick

Schema-Driven Generation:
    >>> rf = RyoFaker()
    >>> data = rf.from_schema('customer_order.json', format='pandas')
    >>> # Returns {'customers': DataFrame, 'orders': DataFrame}

For more information, visit: https://github.com/ada/ryofaker
"""

from pathlib import Path

# Import base Faker for backward compatibility
from faker import Faker as BaseFaker

# Import RyoFaker core classes
from ryofaker.proxy import RyoFaker
from ryofaker.generator import RyoGenerator
from ryofaker.factory import RyoFactory

# Import feature modules
from ryofaker.schema import SchemaGenerator
from ryofaker.relationships import RelationshipManager
from ryofaker.quality import QualityInjector
from ryofaker.temporal import TemporalGenerator

# Import emitters
from ryofaker.emitters import (
    DataFrameEmitter,
    ParquetEmitter,
    CSVEmitter,
    JSONEmitter,
    SQLEmitter,
)

# Import exceptions for public API
from ryofaker.exceptions import (
    RyoFakerException,
    SchemaValidationError,
    ForeignKeyNotFoundError,
    ProviderNotFoundError,
)

# Read version from VERSION file
_version_file = Path(__file__).parent.parent / "VERSION"
try:
    VERSION = _version_file.read_text(encoding="utf-8").strip()
except FileNotFoundError:
    VERSION = "1.0.0"  # Fallback version

__version__ = VERSION

# Public API exports
__all__ = (
    # Core classes
    "RyoFaker",
    "RyoGenerator",
    "RyoFactory",
    "BaseFaker",
    
    # Feature modules
    "SchemaGenerator",
    "RelationshipManager",
    "QualityInjector",
    "TemporalGenerator",
    
    # Emitters
    "DataFrameEmitter",
    "ParquetEmitter",
    "CSVEmitter",
    "JSONEmitter",
    "SQLEmitter",
    
    # Exceptions
    "RyoFakerException",
    "SchemaValidationError",
    "ForeignKeyNotFoundError",
    "ProviderNotFoundError",
    
    # Version
    "VERSION",
    "__version__",
)

# Metadata
__author__ = "ADA Data Science Team"
__email__ = "data-science@ada.com"
__license__ = "MIT"
__url__ = "https://github.com/ada/ryofaker"
__description__ = "Enterprise data generation library extending Faker"
