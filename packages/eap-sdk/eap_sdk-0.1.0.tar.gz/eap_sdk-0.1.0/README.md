# EAP SDK

A lightweight, domain-neutral orchestration SDK for authoring async flows and steps with a small runtime and CLI. The EAP SDK provides decorator-based flow and step definitions with dependency injection support.

## Features

- **Flow Decorators**: `@flow` decorator for async business logic orchestration
- **Step/Task Decorators**: `@step` and `@task` decorators with retry, timeout, and backoff support
- **RunContext**: Dependency injection container for services and configuration
- **Local & Remote Execution**: Run flows locally or via HTTP transport
- **Remote Execution**: `.serve()` method for fire-and-forget remote execution
- **Entrypoints**: Module:function format for robot execution
- **Flow Specs**: Structured flow specifications for orchestration
- **Plugin System**: Register services via `register_service()` for dependency injection
- **CLI Tool**: Command-line interface for running flows
- **Telemetry**: Optional Prometheus metrics integration

## Installation

The EAP SDK is part of the Enterprise Assistant Platform workspace. Install dependencies:

```bash
uv sync --all-packages
```

Or install as a standalone package:

```bash
pip install eap-sdk
```

## Quick Start

### Defining a Flow

```python
from eap_sdk import RunContext, flow, step, task

@step(retries=3, timeout_s=30.0)
async def fetch_data(ctx: RunContext, source: str) -> dict:
    """Fetch data from a source."""
    api = ctx.get("api")  # Access injected service
    result = await api.fetch(source)
    return {"data": result}

# @task is an alias for @step
@task(retries=2, timeout_s=20.0)
async def process_data(ctx: RunContext, data: dict) -> dict:
    """Process data."""
    return {"processed": data}

@flow("my_flow")
async def my_flow(ctx: RunContext, name: str, count: int = 1) -> dict:
    """Example flow that orchestrates steps."""
    data = await fetch_data(ctx, f"source/{name}")
    processed = await process_data(ctx, data)
    return {
        "success": True,
        "processed": count,
        "result": processed
    }
```

### Running a Flow

**Using Python:**

```python
from eap_sdk import RunContext
from eap_sdk.decorators import get_flow

# Get registered flow
flow_fn = get_flow("my_flow")

# Create context and inject services
ctx = RunContext(run_id="run_123", tenant="acme")
ctx.set("api", my_api_client)

# Execute flow locally
result = await flow_fn(ctx, name="test", count=5)

# Or use remote execution via .serve() method
import os
os.environ["MAESTRO_HTTP"] = "http://maestro:8000"

# Submit for remote execution (returns run_id immediately)
run_id = my_flow.serve(pool="prod", params={"name": "test", "count": 5})
print(f"Started run: {run_id}")

# With scheduling
run_id = my_flow.serve(
    pool="prod",
    schedule="0 9 * * *",  # Daily at 9 AM
    params={"name": "test", "count": 5}
)
```

**Using CLI:**

```bash
# Run flow locally
uv run eap-sdk run my_flow --runner local \
  --param name=test --param count=5

# Run flow remotely (requires MAESTRO_ADDR or ROBOT_ADDR)
uv run eap-sdk run my_flow --runner remote \
  --param-json '{"name": "test", "count": 5}'
```

## Core Concepts

### RunContext

`RunContext` provides dependency injection and metadata:

```python
from eap_sdk import RunContext

ctx = RunContext(
    run_id="unique_run_id",
    tenant="acme",
    labels={"env": "production"}
)

# Set services
ctx.set("api", api_client)
ctx.set("db", database_connection)

# Get services
api = ctx.get("api")
db = ctx.get("db")
```

### Flow Decorator

Flows are async functions decorated with `@flow(name)`:

```python
@flow("process_data")
async def process_data(ctx: RunContext, input_data: dict) -> dict:
    # Flow logic here
    return {"success": True, "output": processed}
```

**Requirements:**
- Must be async
- First parameter must be `RunContext`
- Return type should be `dict`
- Registered automatically on import

### Step/Task Decorator

Steps are functions (sync or async) decorated with `@step(...)` or `@task(...)`:

```python
@step(retries=3, timeout_s=30.0, backoff=1.5, base_delay=0.5)
async def api_call(ctx: RunContext, endpoint: str) -> dict:
    # Step logic with automatic retry
    return await http_client.get(endpoint)

# @task is an alias for @step
@task(retries=2, timeout_s=20.0)
async def process_data(ctx: RunContext, data: dict) -> dict:
    return {"processed": data}
```

**Parameters:**
- `retries`: Number of retry attempts (default: 0)
- `timeout_s`: Timeout in seconds (default: None)
- `backoff`: Exponential backoff multiplier (default: 1.5)
- `base_delay`: Base delay in seconds (default: 0.5)
- `jitter`: Random jitter factor (default: 0.2)

**Features:**
- Automatic retry on failure
- Timeout enforcement (sync steps run in thread pool)
- Exponential backoff with jitter

**Note:** `@task` and `@step` are interchangeable aliases. Use whichever naming convention fits your project.

### Service Registration

Register services for dependency injection:

```python
from eap_sdk.plugins import register_service

def create_api_client(ctx: RunContext):
    return ApiClient(host=ctx.tenant)

register_service("api", create_api_client)
```

Services are automatically built when creating a `RunContext` via `build_services()`.

## Runtime

### Local Execution

```python
from eap_sdk.runtime import arun

result = await arun("my_flow", runner="local", name="test", count=5)
```

### Remote Execution

```python
import os
os.environ["MAESTRO_ADDR"] = "http://maestro:8000"

result = await arun("my_flow", runner="remote", name="test", count=5)
```

### Transport Protocols

- **LocalTransport**: Executes flows in-process
- **HTTPTransport**: Sends flow execution requests via HTTP

## CLI Usage

```bash
# Basic usage
eap-sdk run <flow_name> [options]

# Options
--runner {local,remote}    Execution mode (default: local)
--param k=v                Parameter key-value pairs (repeatable)
--param-json JSON          JSON object with parameters

# Examples
eap-sdk run my_flow --param name=test --param count=5
eap-sdk run my_flow --param-json '{"name": "test", "count": 5}'
eap-sdk run my_flow --runner remote --param name=test
```

**Parameter Coercion:**
- `--param` values are auto-coerced (JSON, bool, number if possible)
- `--param-json` accepts a JSON object that's merged into parameters

## Error Handling

Flows should return `{"success": bool, ...}` dictionaries:

```python
@flow("safe_flow")
async def safe_flow(ctx: RunContext, data: dict) -> dict:
    try:
        result = await process(data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

The runtime wraps exceptions in `RunResponse` if they escape the flow.

## Telemetry

Optional Prometheus metrics (requires `prometheus-client`):

- `eap_jobs_total`: Total jobs executed
- `eap_jobs_failed_total`: Failed jobs
- `eap_step_duration_seconds`: Step execution duration
- `eap_step_retries_total`: Step retry count

Install with observability extras:

```bash
pip install eap-sdk[observability]
```

## Development

### Running Tests

```bash
pytest tests/eap_sdk/
```

### Linting & Formatting

```bash
ruff format src/eap_sdk/
ruff check src/eap_sdk/
```

### Type Checking

```bash
pyright src/eap_sdk/
```

## Architecture

```
eap_sdk/
├── __init__.py          # Public API exports
├── context.py           # RunContext class
├── decorators.py        # @flow, @step, and @task decorators
├── runtime.py           # Execution runtime (local/remote), flow specs, entrypoints
├── plugins.py           # Service registration system
├── contracts.py         # RunRequest/RunResponse models
├── telemetry.py         # Prometheus metrics
├── blocks.py            # Reusable blocks (HttpAuthBlock)
└── cli.py               # Command-line interface
```

## New Features

### Remote Execution with `.serve()`

The `.serve()` method provides a convenient way to submit flows for remote execution:

```python
@flow("my_flow")
async def my_flow(ctx: RunContext, name: str) -> dict:
    return {"result": name}

# Set Maestro endpoint
import os
os.environ["MAESTRO_HTTP"] = "http://maestro:8000"

# Submit for execution
run_id = my_flow.serve(pool="prod", params={"name": "test"})
```

**Benefits:**
- Fire-and-forget execution (returns `run_id` immediately)
- Supports scheduling via cron expressions
- Automatic flow spec generation
- Better integration with orchestration systems

### Entrypoints

Flows automatically generate entrypoints for robot execution:

```python
@flow("my_flow")
async def my_flow(ctx: RunContext, name: str) -> dict:
    return {"result": name}

# Entrypoint is automatically stored
print(my_flow._eap_flow_entry)  # "my_module:my_flow"

# Robots can execute flows using entrypoints
from eap_sdk.runtime import run_entrypoint
result = run_entrypoint("my_module:my_flow", {"name": "test"})
```

### Task Decorator

The `@task` decorator is an alias for `@step`:

```python
from eap_sdk import task

@task(retries=3, timeout_s=30.0)
async def my_task(ctx: RunContext, data: dict) -> dict:
    return {"processed": data}
```

Use `@task` if you prefer that naming convention, or stick with `@step` - both work identically.

## Requirements

- Python >= 3.10
- httpx >= 0.27, < 1.0
- pydantic >= 2.8, < 3.0

## License

MIT License
```

This README includes:
- Overview and features
- Installation instructions
- Quick start examples
- Core concepts (RunContext, flows, steps)
- Service registration
- Runtime execution modes
- CLI usage
- Error handling
- Telemetry
- Development setup
- Architecture overview
