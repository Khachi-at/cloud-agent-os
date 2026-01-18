"""Pytest configuration and fixtures"""
import sys
from pathlib import Path

import pytest

from core.context import ExecutionContext

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture
def execution_context():
    """Create a test ExecutionContext"""
    return ExecutionContext(
        tenant="test-tenant",
        region="us-east-1",
        env="test",
        trace_id="trace-test-123",
        metadata={"test": "true"},
    )
