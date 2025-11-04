"""
RyoFaker Factory - Extended Faker Factory
==========================================

This module extends Faker's Factory to support RyoFaker custom providers
and configurations.
"""

from typing import Any, List, Optional

from faker.factory import Factory as FakerFactory

from ryofaker.config import RYOFAKER_PROVIDERS
from ryofaker.generator import RyoGenerator


class RyoFactory(FakerFactory):
    """
    Extended Faker Factory that creates RyoGenerator instances with
    custom RyoFaker providers pre-loaded.
    
    This factory handles:
    - Loading standard Faker providers
    - Loading RyoFaker custom providers (India, telecom, healthcare, etc.)
    - Provider locale resolution
    - Generator configuration
    
    Example:
        >>> from ryofaker.factory import RyoFactory
        >>> generator = RyoFactory.create('en_IN')
        >>> print(generator.pan())  # Custom RyoFaker provider
    """
    
    @classmethod
    def create(
        cls,
        locale: Optional[str] = None,
        providers: Optional[List[str]] = None,
        generator: Optional[RyoGenerator] = None,
        includes: Optional[List[str]] = None,
        use_weighting: bool = True,
        **config: Any,
    ) -> RyoGenerator:
        """
        Create a RyoGenerator instance with providers loaded.
        
        Args:
            locale: Locale string (e.g., 'en_US', 'en_IN')
            providers: List of provider module paths to load
            generator: Pre-configured generator instance (optional)
            includes: Additional provider modules to include
            use_weighting: Use weighted distribution for locales
            **config: Additional configuration
        
        Returns:
            RyoGenerator: Configured generator instance
        """
        # If providers not specified, use default + RyoFaker providers
        if providers is None:
            # Start with Faker's default providers
            from faker.config import PROVIDERS as FAKER_PROVIDERS
            providers = FAKER_PROVIDERS.copy()
            # Add RyoFaker custom providers
            providers.extend(RYOFAKER_PROVIDERS)
        
        # Create generator using parent Factory
        if generator is None:
            generator = RyoGenerator(**config)
        
        # Use parent class method to load all providers
        return super().create(
            locale=locale,
            providers=providers,
            generator=generator,
            includes=includes,
            use_weighting=use_weighting,
            **config,
        )
