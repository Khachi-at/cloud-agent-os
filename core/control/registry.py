"""
Provider Registry for managing cloud provider implementations.

This registry maintains a registry of available cloud providers
and provides methods to register and retrieve them.
"""

from typing import Any, Dict


class ProviderRegistry:
    """
    Registry for cloud provider implementations.

    Manages registration and retrieval of provider instances for
    different cloud platforms (Ctyun, AWS, GCP, etc.).
    """

    def __init__(self) -> None:
        """Initialize the provider registry."""
        self._providers: Dict[str, Any] = {}

    def register(self, name: str, provider: Any) -> None:
        """
        Register a cloud provider.

        Args:
            name: Provider name (e.g., 'ctyun', 'aws', 'gcp')
            provider: Provider instance implementing the Provider interface

        Raises:
            ValueError: If provider with same name already registered
        """
        if name in self._providers:
            raise ValueError(f"Provider {name} is already registered")

        self._providers[name] = provider

    def get(self, name: str) -> Any:
        """
        Get a registered cloud provider.

        Args:
            name: Provider name to retrieve

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found
        """
        if name not in self._providers:
            raise ValueError(
                f"Provider {name} not found. Available: {list(self._providers.keys())}"
            )

        return self._providers[name]

    def list_providers(self) -> list[str]:
        """
        List all registered provider names.

        Returns:
            List of registered provider names
        """
        return list(self._providers.keys())

    def unregister(self, name: str) -> None:
        """
        Unregister a cloud provider.

        Args:
            name: Provider name to unregister

        Raises:
            ValueError: If provider not found
        """
        if name not in self._providers:
            raise ValueError(f"Provider {name} not found")

        del self._providers[name]
