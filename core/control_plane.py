"""
Control Plane module for cloud resource management.

The control plane is the interface between the orchestration system and actual
cloud infrastructure. It provides a unified abstraction for resource operations
across different cloud providers, enabling the orchestrator to manage resources
in a provider-agnostic way.

The control plane follows a declarative model where resources are defined by
their kind and specification, similar to Kubernetes' approach.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ControlPlane(ABC):
    """
    Abstract base class for cloud resource control planes.

    A control plane manages the lifecycle of cloud resources. It provides
    a unified interface for create, read, update, and delete (CRUD) operations
    on cloud infrastructure resources.

    The control plane uses a declarative model where resources are identified
    by their kind (type) and managed via specifications that describe the
    desired state.

    Examples:
        - Kubernetes clusters and workloads
        - VM instances and storage volumes
        - Networking configurations
        - Database instances
    """

    @abstractmethod
    def apply(self, kind: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a resource with the provided specification.

        This is a declarative operation that idempotently applies the desired
        state. If the resource exists, it will be updated to match the spec.
        If it doesn't exist, it will be created.

        Args:
            kind: The resource kind/type (e.g., 'Instance', 'VolumeSnapshot',
                'SecurityGroup'). The specific kinds supported depend on the
                control plane implementation.
            spec: A dictionary describing the desired resource state. Should
                include metadata like name/id and configuration parameters.
                Common fields might include:
                - metadata: name, labels, tags
                - spec: configuration details (size, image, network, etc.)

        Returns:
            A dictionary containing the applied resource with:
                - kind: The resource kind
                - metadata: Resource identifiers and metadata
                - status: Current status of the resource
                - result: Operation result or resource data

        Raises:
            Exception: If the resource cannot be created/updated. Reasons might
                include invalid spec, quota exceeded, or provider errors.
        """
        pass

    @abstractmethod
    def get(self, kind: str, resource_id: str) -> Dict[str, Any]:
        """
        Query the current state and status of a resource.

        Retrieves detailed information about an existing resource, including
        its current state, metadata, and any provider-specific status information.

        Args:
            kind: The resource kind/type (e.g., 'Instance', 'VolumeSnapshot').
            resource_id: The unique identifier of the resource to query.
                Format depends on the provider (e.g., AWS ARN, K8s name).

        Returns:
            A dictionary containing the resource's current state:
                - kind: The resource kind
                - metadata: Resource identifiers and metadata
                - status: Current status (running, pending, failed, etc.)
                - spec: The resource's current specification
                - result: Any operation output or data

        Raises:
            Exception: If the resource cannot be found or if the query fails.
                A common pattern is to raise a specific exception when the
                resource doesn't exist (e.g., ResourceNotFound).
        """
        pass

    @abstractmethod
    def delete(self, resource_id: str) -> bool:
        """
        Delete a resource and its associated state.

        Removes a resource from the control plane. This is typically used during
        rollback operations to clean up resources created by failed tasks.

        Args:
            kind: The resource kind/type to delete.
            resource_id: The unique identifier of the resource to delete.

        Returns:
            True if deletion successful, False if resource not found

        Raises:
            Exception: If the resource cannot be deleted (e.g., doesn't exist,
                is in use, insufficient permissions).
        """
        pass
