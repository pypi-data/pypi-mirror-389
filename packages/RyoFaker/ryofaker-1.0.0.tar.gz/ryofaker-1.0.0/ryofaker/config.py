"""
RyoFaker Configuration
======================

Global configuration constants for RyoFaker library.
"""

from typing import List

# RyoFaker version (read from VERSION file at runtime)
RYOFAKER_VERSION = "1.0.0"

# Default locale for RyoFaker
DEFAULT_LOCALE = "en_US"

# Schema configuration
DEFAULT_SCHEMA_DIR = "schemas/"
DEFAULT_SCHEMA_FORMAT = "json"
SUPPORTED_SCHEMA_FORMATS = ["json", "yaml", "yml"]

# Output configuration
DEFAULT_OUTPUT_FORMAT = "pandas"
SUPPORTED_OUTPUT_FORMATS = [
    "pandas",
    "pyspark",
    "dict",
    "list",
    "parquet",
    "csv",
    "json",
    "jsonl",
    "sql",
]

# Relationship configuration
MAX_FK_RETRIES = 100
DEFAULT_FK_RATIO = 5  # Average number of child records per parent

# Quality injection configuration
DEFAULT_NULL_RATE = 0.1  # 10% nulls
DEFAULT_DUPLICATE_RATE = 0.05  # 5% duplicates
MAX_NULL_RATE = 0.5  # Maximum 50% nulls allowed
MAX_DUPLICATE_RATE = 0.3  # Maximum 30% duplicates allowed

# Temporal configuration
DEFAULT_CDC_OPERATIONS = ["INSERT", "UPDATE", "DELETE"]
DEFAULT_CDC_INSERT_WEIGHT = 0.7  # 70% inserts
DEFAULT_CDC_UPDATE_WEIGHT = 0.2  # 20% updates
DEFAULT_CDC_DELETE_WEIGHT = 0.1  # 10% deletes

# Performance configuration
DEFAULT_BATCH_SIZE = 1000
MAX_BATCH_SIZE = 100000
SHOW_PROGRESS_THRESHOLD = 10000  # Show progress bar for >10k rows

# Custom RyoFaker providers to load
RYOFAKER_PROVIDERS: List[str] = [
    "ryofaker.providers.enterprise.india_identity",
    "ryofaker.providers.enterprise.telecom",
    "ryofaker.providers.enterprise.healthcare",
    "ryofaker.providers.enterprise.retail",
    "ryofaker.providers.enterprise.banking",
    "ryofaker.providers.enterprise.ecommerce",
    "ryofaker.providers.testing.edge_cases",
    "ryofaker.providers.testing.stress",
    "ryofaker.providers.testing.regression",
]

# Cloud storage configuration
CLOUD_PROVIDERS = ["oci", "azure", "aws"]
DEFAULT_CLOUD_PROVIDER = "oci"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
