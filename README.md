# Cloud Agent OS

A cloud-native orchestration framework for autonomous task planning, scheduling, and execution with built-in policy enforcement and audit logging.

## Overview

Cloud Agent OS is a Python-based orchestration system designed to manage complex cloud workloads through an intelligent agent architecture. It combines task planning, policy enforcement, execution scheduling, and comprehensive auditing to enable secure and controlled automation of cloud operations.

## Features

- **Intelligent Task Planning**: Automatically generate execution plans from high-level goals
- **Policy Engine**: Enforce security and operational policies on all tasks before execution
- **Smart Scheduling**: Optimize task scheduling with dependency resolution and parallel execution
- **Flexible Execution**: Execute tasks across multiple executor implementations
- **Comprehensive Audit Trail**: Track all operations and decisions for compliance and debugging
- **Context Management**: Maintain execution context throughout the operation lifecycle

## Project Structure

```
cloud-agent-os/
├── src/
│   ├── agent.py              # Main agent entry point
│   ├── orchestrator.py        # Central orchestration logic
│   ├── planner.py            # Task planning engine
│   ├── policy.py             # Policy enforcement engine
│   ├── scheduler.py          # Task scheduling logic
│   ├── executor.py           # Task execution engine
│   ├── audit.py              # Audit and logging system
│   ├── context.py            # Execution context management
│   ├── models.py             # Data models and schemas
│   ├── control_plane.py      # Control plane management
│   │
│   ├── audits/               # Audit implementations
│   ├── control-planes/       # Control plane implementations
│   ├── executors/            # Executor implementations
│   ├── planners/             # Planner implementations
│   ├── policys/              # Policy implementations
│   └── schedulers/           # Scheduler implementations
│
├── tests/                    # Test suite
├── pyproject.toml           # Project configuration (PDM)
└── README.md               # This file
```

## Core Components

### Agent (`agent.py`)
The main agent entry point that orchestrates the entire system.

### Orchestrator (`orchestrator.py`)
Coordinates the workflow between planning, policy enforcement, scheduling, execution, and auditing.

### Planner (`planner.py`)
Converts high-level goals into executable task plans with dependency tracking.

### Policy Engine (`policy.py`)
Validates tasks against organizational policies before execution.

### Scheduler (`scheduler.py`)
Manages task scheduling with intelligent dependency resolution and parallel execution batching.

### Executor (`executor.py`)
Executes tasks and manages their lifecycle (pending → running → success/failed).

### Audit System (`audit.py`)
Maintains a comprehensive audit trail of all operations and decisions.

### Context Management (`context.py`)
Manages execution context, environment variables, and state across operations.

## Data Models

### Task
Represents a single executable unit with:
- **id**: Unique identifier
- **name**: Human-readable name
- **action**: The action to execute
- **params**: Parameters for the action
- **depends**: List of task IDs this task depends on
- **status**: Current task status (pending, running, success, failed, rolled_back)
- **result**: Execution result
- **error**: Error message if failed

### Plan
Represents an execution plan containing:
- **goal**: The high-level goal to achieve
- **tasks**: List of tasks to execute
- **status**: Plan status

### TaskStatus
Enum representing possible task states:
- `PENDING`: Task waiting to be executed
- `RUNNING`: Task currently executing
- `SUCCESS`: Task completed successfully
- `FAILED`: Task failed
- `ROLLED_BACK`: Task was rolled back

## Installation

### Requirements
- Python 3.13+

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cloud-agent-os
```

2. Install dependencies using PDM:
```bash
pdm install
```

## Usage

```python
from src.orchestrator import Orchestrator
from src.planner import Planner
from src.policy import PolicyEngine
from src.scheduler import Scheduler
from src.executor import Executor
from src.audit import Auditor
from src.context import ExecutionContext

# Initialize components
planner = Planner()
policy_engine = PolicyEngine()
scheduler = Scheduler()
executor = Executor()
auditor = Auditor()

# Create orchestrator
orchestrator = Orchestrator(
    planner=planner,
    policy=policy_engine,
    scheduler=scheduler,
    executor=executor,
    auditor=auditor
)

# Execute a goal
context = ExecutionContext()
result = orchestrator.run("Deploy application", context)
```

## Workflow

1. **Planning**: User provides a goal to the orchestrator
2. **Audit Recording**: Plan creation is recorded in the audit log
3. **Scheduling**: Tasks are scheduled in dependency-aware batches
4. **Policy Enforcement**: Each task is validated against policies
5. **Execution**: Tasks are executed by the executor
6. **Result Processing**: Results are recorded and propagated
7. **Completion**: Final results are returned to the user

## Configuration

Configuration is managed through `pyproject.toml`. Key settings:
- Project name: `cloud-agent-os`
- Python version: 3.13.*
- Package manager: PDM

## Testing

Run tests using:
```bash
pdm run test
pdm run test-cov    # With coverage report
```

## Code Quality

This project uses pre-commit hooks to ensure code quality. Pre-commit hooks automatically run checks before each commit.

### Pre-commit Hooks

The project includes the following pre-commit hooks:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **General checks**: Trailing whitespace, file endings, YAML validation, large files, merge conflicts

### Setting up Pre-commit

1. Install pre-commit hooks:
```bash
pdm run pre-commit-install
```

2. Run pre-commit checks manually:
```bash
pdm run pre-commit-run
```

3. Available code quality commands:
```bash
pdm run format      # Format code with Black
pdm run isort       # Sort imports with isort
pdm run lint        # Lint with flake8
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:
1. Code follows Python best practices
2. All tests pass
3. New features include appropriate tests
4. Audit trail is maintained for all operations

## Support

For issues, questions, or contributions, please open an issue in the repository.

## Authors

- khachi (hechl@chinatelecom.cn)
