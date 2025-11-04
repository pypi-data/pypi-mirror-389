"""
RyoFaker Proxy - Extended Faker with Enterprise Features
========================================================

This module provides the RyoFaker class, which extends Faker's proxy
with additional enterprise data generation capabilities.
"""

from typing import Any, Dict, List, Optional, Union

from faker import Faker

from ryofaker.exceptions import RyoFakerException


class RyoFaker(Faker):
    """
    Extended Faker proxy with enterprise data generation features.
    
    RyoFaker maintains 100% backward compatibility with Faker while adding:
    - Schema-driven generation via JSON/YAML
    - Referential integrity management
    - Data quality testing (nulls, duplicates, violations)
    - Time-series and CDC simulation
    - Custom enterprise providers (India-specific, telecom, healthcare, etc.)
    
    All standard Faker methods work identically:
        >>> rf = RyoFaker('en_US')
        >>> rf.name()  # Standard Faker method
        >>> rf.address()  # Standard Faker method
    
    Plus RyoFaker-specific features:
        >>> rf.pan()  # Custom India provider
        >>> rf.from_schema('schema.json', rows=1000)  # Schema-driven
        >>> rf.with_relationships({...})  # FK management
    
    Args:
        locale: Locale string (e.g., 'en_US', 'en_IN') or list of locales
        providers: List of provider modules to load
        generator: Custom generator instance
        includes: Additional provider modules to include
        use_weighting: Use weighted random selection for multi-locale
        **config: Additional configuration parameters
    
    Example:
        >>> from ryofaker import RyoFaker
        >>> rf = RyoFaker('en_IN')
        >>> 
        >>> # Standard Faker methods
        >>> print(rf.name())  # "Ravi Kumar"
        >>> 
        >>> # RyoFaker custom providers
        >>> print(rf.pan())  # "ABCDE1234F"
        >>> print(rf.aadhaar())  # "1234 5678 9012"
        >>> 
        >>> # Schema-driven generation
        >>> data = rf.from_schema('customer.json', rows=100)
    """
    
    def __init__(
        self,
        locale: Optional[Union[str, List[str], Dict[str, Union[int, float]]]] = None,
        providers: Optional[List[str]] = None,
        generator: Optional[Any] = None,
        includes: Optional[List[str]] = None,
        use_weighting: bool = True,
        **config: Any,
    ):
        """Initialize RyoFaker with Faker base and add RyoFaker extensions."""
        # Initialize base Faker
        super().__init__(
            locale=locale,
            providers=providers,
            generator=generator,
            includes=includes,
            use_weighting=use_weighting,
            **config,
        )
        
        # Lazy-load RyoFaker feature modules to avoid circular imports
        self._schema_generator = None
        self._relationship_manager = None
        self._quality_injector = None
        self._temporal_generator = None
        
        # Load custom enterprise providers
        self._load_custom_providers()
    
    def _load_custom_providers(self) -> None:
        """Load RyoFaker custom providers (India, telecom, healthcare, etc.)."""
        try:
            # Import and add custom providers
            from ryofaker.providers.enterprise.india_identity import Provider as IndiaIdentityProvider
            from ryofaker.providers.enterprise.telecom import Provider as TelecomProvider
            
            # Add providers to generator
            self.add_provider(IndiaIdentityProvider)
            self.add_provider(TelecomProvider)
            
        except ImportError:
            # Providers not yet implemented - gracefully ignore
            pass
    
    @property
    def schema(self):
        """Lazy-load SchemaGenerator for schema-driven data generation."""
        if self._schema_generator is None:
            from ryofaker.schema import SchemaGenerator
            self._schema_generator = SchemaGenerator(self)
        return self._schema_generator
    
    @property
    def relationships(self):
        """Lazy-load RelationshipManager for FK management."""
        if self._relationship_manager is None:
            from ryofaker.relationships import RelationshipManager
            self._relationship_manager = RelationshipManager(self)
        return self._relationship_manager
    
    @property
    def quality(self):
        """Lazy-load QualityInjector for data quality testing."""
        if self._quality_injector is None:
            from ryofaker.quality import QualityInjector
            self._quality_injector = QualityInjector(self)
        return self._quality_injector
    
    @property
    def temporal(self):
        """Lazy-load TemporalGenerator for time-series and CDC simulation."""
        if self._temporal_generator is None:
            from ryofaker.temporal import TemporalGenerator
            self._temporal_generator = TemporalGenerator(self)
        return self._temporal_generator
    
    # -------------------------------------------------------------------------
    # High-Level API Methods
    # -------------------------------------------------------------------------
    
    def from_schema(
        self,
        schema_path: str,
        rows: Optional[int] = None,
        format: str = "pandas",
        output: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Dict, Any]:
        """
        Generate data from JSON/YAML schema file.
        
        Args:
            schema_path: Path to schema file (.json or .yaml)
            rows: Number of rows to generate (overrides schema)
            format: Output format ('pandas', 'pyspark', 'parquet', 'csv', 'sql')
            output: Output file path (for file formats)
            **kwargs: Additional parameters passed to schema generator
        
        Returns:
            dict: Dictionary of table_name → DataFrame/data
            
        Example:
            >>> rf = RyoFaker()
            >>> data = rf.from_schema('customer_order.json', rows=1000, format='pandas')
            >>> print(data.keys())  # dict_keys(['customers', 'orders'])
            >>> print(data['customers'].shape)  # (100, 5)
        """
        return self.schema.generate_from_file(
            schema_path=schema_path,
            rows=rows,
            format=format,
            output=output,
            **kwargs,
        )
    
    def with_relationships(
        self,
        tables: Dict[str, Dict[str, Any]],
        format: str = "pandas",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate multiple related tables with guaranteed FK integrity.
        
        Args:
            tables: Dictionary defining tables, schemas, and relationships
                    Example: {
                        'users': {'rows': 100, 'schema': {...}},
                        'orders': {'rows': 500, 'schema': {...}, 'fk': {'user_id': 'users.id'}},
                    }
            format: Output format ('pandas', 'pyspark', etc.)
            **kwargs: Additional parameters
        
        Returns:
            dict: Dictionary of table_name → DataFrame
            
        Example:
            >>> rf = RyoFaker()
            >>> data = rf.with_relationships({
            ...     'customers': {
            ...         'rows': 100,
            ...         'schema': {'id': 'uuid4', 'name': 'name'}
            ...     },
            ...     'orders': {
            ...         'rows': 500,
            ...         'schema': {'id': 'uuid4', 'customer_id': 'fk:customers.id', 'amount': 'pydecimal'}
            ...     }
            ... })
        """
        return self.relationships.generate_related(
            tables=tables,
            format=format,
            **kwargs,
        )
    
    def inject_nulls(
        self,
        data: Any,
        columns: List[str],
        null_rate: float = 0.1,
        **kwargs: Any,
    ) -> Any:
        """
        Inject NULL values into data for quality testing.
        
        Args:
            data: DataFrame or dict to inject nulls into
            columns: List of column names to affect
            null_rate: Percentage of rows to set NULL (0.0 to 1.0)
            **kwargs: Additional parameters
        
        Returns:
            Modified data with injected nulls
            
        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'name': ['A', 'B', 'C'], 'age': [25, 30, 35]})
            >>> df_nulls = rf.inject_nulls(df, columns=['age'], null_rate=0.33)
        """
        return self.quality.inject_nulls(
            data=data,
            columns=columns,
            null_rate=null_rate,
            **kwargs,
        )
    
    def inject_duplicates(
        self,
        data: Any,
        duplicate_rate: float = 0.05,
        **kwargs: Any,
    ) -> Any:
        """
        Inject duplicate rows for deduplication testing.
        
        Args:
            data: DataFrame or dict to inject duplicates into
            duplicate_rate: Percentage of rows to duplicate (0.0 to 1.0)
            **kwargs: Additional parameters
        
        Returns:
            Modified data with injected duplicates
            
        Example:
            >>> df_dupes = rf.inject_duplicates(df, duplicate_rate=0.1)
        """
        return self.quality.inject_duplicates(
            data=data,
            duplicate_rate=duplicate_rate,
            **kwargs,
        )
    
    def cdc_stream(
        self,
        schema: Dict[str, Any],
        duration_seconds: int = 60,
        operations: Optional[List[str]] = None,
        **kwargs: Any,
    ):
        """
        Generate CDC (Change Data Capture) event stream.
        
        Args:
            schema: Data schema for CDC events
            duration_seconds: How long to generate events
            operations: List of operations to include ['INSERT', 'UPDATE', 'DELETE']
            **kwargs: Additional parameters
        
        Yields:
            dict: CDC event with operation, timestamp, and data
            
        Example:
            >>> for event in rf.cdc_stream({'user_id': 'uuid4', 'name': 'name'}, duration_seconds=10):
            ...     print(event['operation'], event['timestamp'])
        """
        return self.temporal.cdc_stream(
            schema=schema,
            duration_seconds=duration_seconds,
            operations=operations,
            **kwargs,
        )
    
    def __repr__(self) -> str:
        """String representation of RyoFaker instance."""
        locale = getattr(self, "locale", "unknown")
        return f"<RyoFaker(locale='{locale}')>"
