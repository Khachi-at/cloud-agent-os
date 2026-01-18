"""
Data models for cloud resources managed by the control plane.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Resource:
    """
    Represents a cloud resource managed by the control plane.

    Tracks the complete lifecycle of a cloud resource including
    specification, current state, and status.

    Attributes:
        id: Unique resource identifier (UUID)
        kind: Resource type (VPC, Instance, Database, etc.)
        provider: Cloud provider name (ctyun, aws, gcp, etc.)
        spec: Full resource specification
        state: Current state returned by provider
        status: Resource lifecycle status (pending, provisioning, ready, failed, etc.)
        created_at: Timestamp when resource was created locally
    """

    id: str
    kind: str
    provider: str
    spec: Dict[str, Any]
    state: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def is_ready(self) -> bool:
        """Check if resource is ready for use."""
        return self.status == "ready"

    def is_failed(self) -> bool:
        """Check if resource creation failed."""
        return self.status == "failed"

    def is_provisioning(self) -> bool:
        """Check if resource is being provisioned."""
        return self.status == "provisioning"
