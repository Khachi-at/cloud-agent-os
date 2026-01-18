"""
Default Control Plane Implementation.

This module provides a control plane that coordinates with cloud providers
to manage the complete lifecycle of cloud resources.
"""

import uuid
from typing import Any, Dict, Optional

from core.control.models import Resource
from core.control.registry import ProviderRegistry
from core.control_plane import ControlPlane


class Store:
    """
    In-memory resource store for demonstration.

    In production, this should be replaced with a persistent store
    (database, etcd, etc.).
    """

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._resources: Dict[str, Resource] = {}

    def save(self, resource: Resource) -> None:
        """Save a resource."""
        self._resources[resource.id] = resource

    def get(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by ID."""
        return self._resources.get(resource_id)

    def update(self, resource: Resource) -> None:
        """Update an existing resource."""
        if resource.id in self._resources:
            self._resources[resource.id] = resource

    def delete(self, resource_id: str) -> bool:
        """Delete a resource."""
        if resource_id in self._resources:
            del self._resources[resource_id]
            return True
        return False

    def list_resources(self) -> list[Resource]:
        """List all resources."""
        return list(self._resources.values())


class DefaultControlPlane(ControlPlane):
    """
    Default implementation of a cloud control plane.

    Coordinates with cloud providers to provision, manage, and track
    the lifecycle of cloud resources.
    """

    def __init__(self, registry: ProviderRegistry, store: Optional[Store] = None) -> None:
        """
        Initialize the control plane.

        Args:
            registry: ProviderRegistry with registered cloud providers
            store: Resource store (defaults to in-memory store)
        """
        self.registry = registry
        self.store = store or Store()

    def apply(self, kind: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a resource specification to create or update a cloud resource.

        Workflow:
        1. Get provider from registry
        2. Create resource record with "provisioning" status
        3. Call provider to create actual cloud resource
        4. Update resource record with cloud state
        5. Return result to caller

        Args:
            kind: Resource type (e.g., 'VPC', 'Instance')
            spec: Full resource specification

        Returns:
            Dictionary with resource_id, status, and state

        Raises:
            ValueError: If provider not found or kind not supported
        """
        # Extract provider name
        provider_name = spec.get("provider")
        if not provider_name:
            raise ValueError("Specification must include 'provider' field")

        # Get provider from registry
        provider = self.registry.get(provider_name)

        # Generate resource ID
        resource_id = str(uuid.uuid4())

        # Create resource record in store
        resource = Resource(
            id=resource_id,
            kind=kind,
            provider=provider_name,
            spec=spec,
            status="provisioning",
        )
        self.store.save(resource)

        try:
            # Call provider to provision resource
            state = provider.apply(kind, spec)

            # Update resource with cloud state
            resource.state = state
            resource.status = "ready"
            self.store.update(resource)

            return {
                "resource_id": resource.id,
                "kind": resource.kind,
                "status": resource.status,
                "state": resource.state,
            }
        except Exception as e:
            # Mark resource as failed
            resource.status = "failed"
            resource.state = {"error": str(e)}
            self.store.update(resource)
            raise

    def get(self, kind: str, resource_id: str) -> Dict[str, Any]:
        """
        Get the current state of a resource.

        Queries both the local store and the cloud provider to get
        the most current state of a resource.

        Args:
            kind: Resource type
            resource_id: Resource identifier

        Returns:
            Dictionary with current resource state

        Raises:
            ValueError: If resource not found
        """
        # Get resource from store
        resource = self.store.get(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        # Get provider
        provider = self.registry.get(resource.provider)

        # Query provider for current state
        try:
            actual_state = provider.get(kind, resource.state)
        except Exception as e:
            actual_state = resource.state
            actual_state["error"] = str(e)

        return {
            "resource_id": resource.id,
            "kind": resource.kind,
            "status": resource.status,
            "spec": resource.spec,
            "state": actual_state,
            "created_at": resource.created_at,
        }

    def delete(self, resource_id: str) -> bool:
        """
        Delete a cloud resource.

        Args:
            resource_id: Resource identifier

        Returns:
            True if deletion successful, False if resource not found

        Raises:
            Exception: If deletion fails
        """
        resource = self.store.get(resource_id)
        if not resource:
            return False

        try:
            # Provider cleanup if needed (not implemented in base)
            # In real implementation, provider.delete() would be called
            pass
        finally:
            # Remove from store
            self.store.delete(resource_id)

        return True

    def list_resources(self, kind: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        List all resources, optionally filtered by kind.

        Args:
            kind: Optional resource type to filter by

        Returns:
            List of resource information
        """
        resources = self.store.list_resources()

        if kind:
            resources = [r for r in resources if r.kind == kind]

        return [
            {
                "resource_id": r.id,
                "kind": r.kind,
                "provider": r.provider,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in resources
        ]
