"""
RyoFaker Type Hints
===================

Custom type aliases and type definitions for RyoFaker library.
"""

from typing import Any, Callable, Dict, List, TypeAlias, Union

import pandas as pd

# Schema types
SchemaDict: TypeAlias = Dict[str, Any]
ColumnSpec: TypeAlias = Dict[str, Any]
TableSpec: TypeAlias = Dict[str, Any]
RelationshipSpec: TypeAlias = Dict[str, Any]

# Data types
DataFrameType: TypeAlias = pd.DataFrame
RecordList: TypeAlias = List[Dict[str, Any]]
RecordDict: TypeAlias = Dict[str, Any]

# Output types
OutputFormat: TypeAlias = str  # 'pandas', 'pyspark', 'csv', etc.
OutputData: TypeAlias = Union[DataFrameType, RecordList, str]

# Provider types
ProviderMethod: TypeAlias = Callable[..., Any]
ProviderClass: TypeAlias = type

# Locale types
LocaleStr: TypeAlias = str  # e.g., 'en_US', 'en_IN'
LocaleList: TypeAlias = List[LocaleStr]
LocaleWeights: TypeAlias = Dict[LocaleStr, Union[int, float]]
LocaleSpec: TypeAlias = Union[LocaleStr, LocaleList, LocaleWeights]

# Seed types (from Faker)
SeedType: TypeAlias = Union[int, float, str, bytes, bytearray, None]

# File types
FilePath: TypeAlias = str
SchemaPath: TypeAlias = FilePath
OutputPath: TypeAlias = FilePath

# Quality injection types
NullRate: TypeAlias = float  # 0.0 to 1.0
DuplicateRate: TypeAlias = float  # 0.0 to 1.0

# CDC types
CDCOperation: TypeAlias = str  # 'INSERT', 'UPDATE', 'DELETE'
CDCEvent: TypeAlias = Dict[str, Any]

# Relationship types
ForeignKeySpec: TypeAlias = str  # e.g., 'customers.customer_id'
PKValue: TypeAlias = Any

# Configuration types
ConfigDict: TypeAlias = Dict[str, Any]
