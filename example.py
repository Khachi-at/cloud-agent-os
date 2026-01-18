"""
Complete example demonstrating Cloud Agent OS for cloud resource orchestration.

This example shows a practical cloud infrastructure scenario where:
1. A planner creates a deployment plan based on a goal
2. A scheduler determines execution order with dependencies
3. A policy engine evaluates security/compliance
4. An executor manages resources via control plane
5. An auditor tracks all events

Scenario: Deploy a production web service with networking and database
"""

from typing import Any, Dict

from core.agent.planners.langchain import LangChainPlanner
from core.audit import Auditor
from core.context import ExecutionContext
from core.control.control_plane import DefaultControlPlane
from core.control.providers.ctyun import CtyunProvider
from core.control.registry import ProviderRegistry
from core.executors.executor import SimpleExecutor
from core.orchestrator import Orchestrator
from core.policy import PolicyDecision, PolicyEngine
from core.schedulers.dag import DAGScheduler


class SimplePolicyEngine(PolicyEngine):
    """Simple policy engine that checks for dangerous operations"""

    def evaluate(
        self,
        subject: str,
        action: str,
        resource: Dict[str, Any],
        ctx: ExecutionContext,
    ) -> Dict[str, Any]:
        """
        Evaluate if an action should be allowed based on environment and action type.

        Args:
            subject: Who is performing the action
            action: What action is being performed (create, delete, scale, etc.)
            resource: Resource details
            ctx: Execution context

        Returns:
            Decision dict with decision, reason, and risk_score
        """
        # Production environment requires approval for dangerous operations
        if ctx.env == "prod" and action in ["delete", "scale_down"]:
            return {
                "decision": PolicyDecision.ALLOW,
                "reason": f"Production {action} requires manual approval",
                "risk_score": 100,
            }

        # Deny delete operations in staging
        if ctx.env == "staging" and action == "delete":
            return {
                "decision": PolicyDecision.DENY,
                "reason": "Delete operations not allowed in staging",
                "risk_score": 80,
            }

        # Allow safe operations
        safe_actions = ["create", "scale_up", "describe", "list"]
        if action in safe_actions:
            return {
                "decision": PolicyDecision.ALLOW,
                "reason": f"Safe operation: {action}",
                "risk_score": 10,
            }

        # Default to deny unknown operations
        return {
            "decision": PolicyDecision.DENY,
            "reason": f"Unknown or restricted operation: {action}",
            "risk_score": 90,
        }


class SimpleAuditor(Auditor):
    """Simple auditor that logs events to in-memory storage"""

    def __init__(self) -> None:
        """Initialize auditor with empty event log"""
        self.events: list[Dict[str, Any]] = []

    def record(self, event: Dict[str, Any]) -> None:
        """
        Record an event in the audit log.

        Args:
            event: Event details to record
        """
        self.events.append(event)
        # In production, this would write to persistent storage, logs, etc.
        print(f"[AUDIT] {event}")

    def get_events(self) -> list[Dict[str, Any]]:
        """Get all recorded events"""
        return self.events.copy()


def setup_handlers(executor: SimpleExecutor) -> None:
    """
    Register task handlers that use the control plane to manage resources.

    Args:
        executor: The executor to register handlers with
        control_plane: The control plane for resource management
    """

    # Handler: Create VPC
    def create_vpc(params: Dict[str, Any], ctx: ExecutionContext, cp) -> Dict[str, Any]:
        """Create a VPC in the cloud"""
        return cp.apply(
            "VPC",
            {
                "provider": "ctyun",
                "metadata": {
                    "name": params.get("name", "vpc-prod"),
                    "region": ctx.region,
                    "env": ctx.env,
                },
                "spec": {
                    "cidr": params.get("cidr", "10.0.0.0/16"),
                    "enable_dns": True,
                },
            },
        )

    def delete_vpc(params: Dict[str, Any], ctx: ExecutionContext, cp) -> None:
        """Delete a VPC (rollback)"""
        resource_id = params.get("resource_id")
        if resource_id:
            cp.delete(resource_id)

    # Handler: Create Security Group
    def create_security_group(params: Dict[str, Any], ctx: ExecutionContext, cp) -> Dict[str, Any]:
        """Create a security group"""
        result = cp.apply(
            "SecurityGroup",
            {
                "provider": "ctyun",
                "metadata": {"name": params.get("name", "sg-web")},
                "spec": {
                    "description": "Web traffic security group",
                    "rules": params.get("rules", []),
                },
            },
        )
        return result

    def delete_security_group(params: Dict[str, Any], ctx: ExecutionContext, cp) -> None:
        """Delete a security group (rollback)"""
        resource_id = params.get("resource_id")
        if resource_id:
            cp.delete(resource_id)

    # Handler: Create Database
    def create_database(params: Dict[str, Any], ctx: ExecutionContext, cp) -> Dict[str, Any]:
        """Create a database instance"""
        result = cp.apply(
            "Database",
            {
                "provider": "ctyun",
                "metadata": {
                    "name": params.get("name", "db-prod"),
                    "env": ctx.env,
                },
                "spec": {
                    "engine": params.get("engine", "postgres"),
                    "version": params.get("version", "14"),
                    "instance_type": params.get("instance_type", "db.t3.medium"),
                    "storage": params.get("storage", 100),
                    "backup_retention": params.get("backup_retention", 30),
                },
            },
        )
        return result

    def delete_database(params: Dict[str, Any], ctx: ExecutionContext, cp) -> None:
        """Delete a database (rollback)"""
        resource_id = params.get("resource_id")
        if resource_id:
            cp.delete(resource_id)

    # Handler: Deploy Application
    def deploy_app(params: Dict[str, Any], ctx: ExecutionContext, cp) -> Dict[str, Any]:
        """Deploy application servers"""
        result = cp.apply(
            "Instance",
            {
                "provider": "ctyun",
                "metadata": {
                    "name": params.get("name", "app-server"),
                    "env": ctx.env,
                    "region": ctx.region,
                },
                "spec": {
                    "image": params.get("image", "ubuntu-20.04"),
                    "instance_type": params.get("instance_type", "t3.medium"),
                    "count": params.get("count", 2),
                },
            },
        )
        return result

    def undeploy_app(params: Dict[str, Any], ctx: ExecutionContext, cp) -> None:
        """Undeploy application (rollback)"""
        resource_id = params.get("resource_id")
        if resource_id:
            cp.delete(resource_id)

    # Handler: Configure Monitoring
    def setup_monitoring(params: Dict[str, Any], ctx: ExecutionContext, cp) -> Dict[str, Any]:
        """Setup storage for monitoring and logs"""
        result = cp.apply(
            "Storage",
            {
                "provider": "ctyun",
                "metadata": {"name": params.get("name", "monitoring-storage")},
                "spec": {
                    "type": "block",
                    "size": params.get("size", 100),
                    "iops": params.get("iops", 3000),
                },
            },
        )
        return result

    def delete_monitoring(params: Dict[str, Any], ctx: ExecutionContext, cp) -> None:
        """Delete monitoring storage (rollback)"""
        resource_id = params.get("resource_id")
        if resource_id:
            cp.delete(resource_id)

    # Register all handlers
    executor.register("create_vpc", create_vpc, delete_vpc)
    executor.register("create_security_group", create_security_group, delete_security_group)
    executor.register("create_database", create_database, delete_database)
    executor.register("deploy_app", deploy_app, undeploy_app)
    executor.register("setup_monitoring", setup_monitoring, delete_monitoring)


def main() -> None:
    """
    Main entry point demonstrating the complete Cloud Agent OS workflow.

    This demonstrates:
    1. Setting up execution context
    2. Creating all components (planner, executor, control plane, etc.)
    3. Running the orchestration workflow
    4. Reporting results
    """
    print("=" * 80)
    print("Cloud Agent OS - Production Deployment Example")
    print("=" * 80)

    # Setup execution context
    ctx = ExecutionContext(
        tenant="acme-corp",
        region="us-east-1",
        env="prod",
        trace_id="deployment-001",
        metadata={"project": "web-service", "team": "platform"},
    )
    print(f"\nExecution Context: {ctx}")

    # Initialize components
    planner = LangChainPlanner()
    scheduler = DAGScheduler()
    executor = SimpleExecutor()

    # Setup Ctyun provider with control plane
    registry = ProviderRegistry()
    registry.register("ctyun", CtyunProvider())
    control_plane = DefaultControlPlane(registry)

    policy = SimplePolicyEngine()
    auditor = SimpleAuditor()

    # Setup task handlers
    setup_handlers(executor)

    # Create orchestrator
    orchestrator = Orchestrator(
        planner=planner,
        policy=policy,
        scheduler=scheduler,
        executor=executor,
        control_plane=control_plane,
        auditor=auditor,
    )

    print("\n" + "=" * 80)
    print("Starting Deployment")
    print("=" * 80)

    # Run the orchestration
    try:
        plan = orchestrator.run("Deploy production web service", ctx)

        print("\n" + "=" * 80)
        print("Deployment Completed")
        print("=" * 80)
        print(f"\nPlan Goal: {plan.goal}")
        print(f"Plan Status: {plan.status}")
        print("\nTask Results:")
        for task in plan.tasks:
            status_indicator = "✓" if task.status.value == "success" else "✗"
            print(f"  {status_indicator} {task.name}: {task.status.value}")

        # Print executor statistics
        stats = executor.get_stats()
        print("\nExecution Statistics:")
        print(f"  Total Executions: {stats['total_executions']}")
        print(f"  Successful: {stats['successful_executions']}")
        print(f"  Failed: {stats['failed_executions']}")
        print(f"  Rollbacks: {stats['total_rollbacks']}")

        # Print audit events
        events = auditor.get_events()
        print(f"\nAudit Trail ({len(events)} events):")
        for i, event in enumerate(events[-5:], 1):  # Show last 5 events
            print(f"  {i}. {event}")

        print("\n" + "=" * 80)
        print("Deployment Successful!")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Deployment failed: {e}")
        print(f"Audit trail captured {len(auditor.get_events())} events")
        raise


if __name__ == "__main__":
    main()
