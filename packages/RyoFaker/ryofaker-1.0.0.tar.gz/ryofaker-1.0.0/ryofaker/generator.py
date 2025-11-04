"""
RyoFaker Generator - Extended Faker Generator
==============================================

This module extends Faker's Generator to support RyoFaker-specific
functionality and provider management.
"""

from typing import Any, Dict

from faker.generator import Generator as FakerGenerator


class RyoGenerator(FakerGenerator):
    """
    Extended Faker Generator with RyoFaker-specific enhancements.
    
    This generator:
    - Maintains compatibility with Faker's generator interface
    - Supports RyoFaker custom providers
    - Adds metadata tracking for generated data
    - Provides hooks for quality injection and validation
    
    Example:
        >>> from ryofaker.generator import RyoGenerator
        >>> gen = RyoGenerator()
        >>> gen.add_provider(SomeProvider)
        >>> print(gen.name())
    """
    
    def __init__(self, **config: Dict[str, Any]):
        """
        Initialize RyoGenerator with configuration.
        
        Args:
            **config: Configuration dictionary
        """
        super().__init__(**config)
        
        # RyoFaker-specific metadata
        self._ryofaker_metadata: Dict[str, Any] = {
            "version": "1.0.0",
            "custom_providers_loaded": [],
        }
    
    def add_provider(self, provider: Any) -> None:
        """
        Add a provider to the generator.
        
        Extends Faker's add_provider to track RyoFaker custom providers.
        
        Args:
            provider: Provider class or instance to add
        """
        # Call parent to register provider
        super().add_provider(provider)
        
        # Track custom providers
        provider_name = getattr(provider, "__name__", str(provider))
        if "ryofaker.providers" in str(provider):
            self._ryofaker_metadata["custom_providers_loaded"].append(provider_name)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get RyoFaker metadata about this generator instance.
        
        Returns:
            dict: Metadata including loaded providers, version, etc.
        """
        return self._ryofaker_metadata.copy()
    
    def __repr__(self) -> str:
        """String representation of RyoGenerator."""
        num_providers = len(self.providers)
        return f"<RyoGenerator(providers={num_providers})>"
