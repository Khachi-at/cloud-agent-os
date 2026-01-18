"""
Base Provider Interface for Cloud Resource Management.

This module defines the abstract interface that all cloud providers
must implement to be used with the Cloud Agent OS.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Provider(ABC):
    """
    Abstract base class for cloud providers.

    All cloud provider implementations (Ctyun, AWS, GCP, etc.) must
    inherit from this class and implement the required methods for
    resource lifecycle management.
    """

    @abstractmethod
    def apply(self, kind: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply (create or update) a cloud resource.

        This method should handle the creation or update of a cloud
        resource based on the provided specification. It should return
        the current state of the resource.

        Args:
            kind: The type of resource (e.g., 'VPC', 'Instance', 'Database')
            spec: Resource specification containing provider, metadata, and details

        Returns:
            Dictionary containing the resource state after application,
            including identifiers and configuration

        Raises:
            ValueError: If resource kind is not supported
            Exception: If resource creation/update fails
        """
        pass

    @abstractmethod
    def get(self, kind: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the current state of a cloud resource.

        This method should query the cloud provider for the current
        state of an existing resource and return updated information.

        Args:
            kind: The type of resource (e.g., 'VPC', 'Instance', 'Database')
            state: Current known state of the resource with identifiers

        Returns:
            Dictionary containing the updated resource state from the cloud

        Raises:
            ValueError: If resource kind is not supported
            Exception: If resource lookup fails
        """
        pass
