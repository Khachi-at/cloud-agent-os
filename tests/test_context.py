"""Tests for ExecutionContext"""
from src.context import ExecutionContext


class TestExecutionContext:
    """Test ExecutionContext"""

    def test_context_creation(self):
        """Test basic context creation"""
        ctx = ExecutionContext(
            tenant="test-tenant", region="us-east-1", env="test", trace_id="trace-123", metadata={}
        )
        assert ctx is not None

    def test_context_can_store_attributes(self):
        """Test that context can store attributes"""
        ctx = ExecutionContext(
            tenant="test-tenant", region="us-east-1", env="test", trace_id="trace-123", metadata={}
        )
        assert ctx.tenant == "test-tenant"
        assert ctx.region == "us-east-1"
        assert ctx.env == "test"

    def test_context_isolation(self):
        """Test that different contexts are isolated"""
        ctx1 = ExecutionContext(
            tenant="tenant-1",
            region="us-east-1",
            env="prod",
            trace_id="trace-1",
            metadata={"key": "value1"},
        )
        ctx2 = ExecutionContext(
            tenant="tenant-2",
            region="us-west-2",
            env="staging",
            trace_id="trace-2",
            metadata={"key": "value2"},
        )

        assert ctx1.tenant == "tenant-1"
        assert ctx2.tenant == "tenant-2"
        assert ctx1.metadata["key"] == "value1"
        assert ctx2.metadata["key"] == "value2"
