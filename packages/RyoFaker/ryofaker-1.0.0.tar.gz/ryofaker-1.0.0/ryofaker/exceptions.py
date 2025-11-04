"""
RyoFaker Exceptions
===================

Custom exception classes for RyoFaker library.
"""


class RyoFakerException(Exception):
    """Base exception for all RyoFaker errors."""
    pass


class SchemaValidationError(RyoFakerException):
    """Raised when schema validation fails."""
    
    def __init__(self, message: str, schema_path: str = None, errors: list = None):
        self.schema_path = schema_path
        self.errors = errors or []
        super().__init__(message)


class ForeignKeyNotFoundError(RyoFakerException):
    """Raised when a foreign key reference cannot be resolved."""
    
    def __init__(self, message: str, table: str = None, column: str = None, reference: str = None):
        self.table = table
        self.column = column
        self.reference = reference
        super().__init__(message)


class ProviderNotFoundError(RyoFakerException):
    """Raised when a requested provider is not available."""
    
    def __init__(self, message: str, provider_name: str = None):
        self.provider_name = provider_name
        super().__init__(message)


class InvalidSchemaFormatError(RyoFakerException):
    """Raised when schema file format is not supported."""
    
    def __init__(self, message: str, format: str = None, supported_formats: list = None):
        self.format = format
        self.supported_formats = supported_formats or []
        super().__init__(message)


class InvalidOutputFormatError(RyoFakerException):
    """Raised when requested output format is not supported."""
    
    def __init__(self, message: str, format: str = None, supported_formats: list = None):
        self.format = format
        self.supported_formats = supported_formats or []
        super().__init__(message)


class CircularReferenceError(RyoFakerException):
    """Raised when circular FK references are detected."""
    
    def __init__(self, message: str, cycle: list = None):
        self.cycle = cycle or []
        super().__init__(message)


class DataQualityError(RyoFakerException):
    """Raised when data quality injection parameters are invalid."""
    
    def __init__(self, message: str, parameter: str = None, value: any = None):
        self.parameter = parameter
        self.value = value
        super().__init__(message)


class CloudStorageError(RyoFakerException):
    """Raised when cloud storage operations fail."""
    
    def __init__(self, message: str, provider: str = None, operation: str = None):
        self.provider = provider
        self.operation = operation
        super().__init__(message)
