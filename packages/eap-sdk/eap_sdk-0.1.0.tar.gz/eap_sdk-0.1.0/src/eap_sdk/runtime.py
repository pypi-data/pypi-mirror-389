from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Protocol

import httpx

from .context import RunContext
from .contracts import RunRequest, RunResponse
from .decorators import get_flow
from .plugins import build_services, import_plugins_from_env
from .telemetry import record_job


def build_flow_spec(flow_fn: Any, flow_name: str) -> dict[str, Any]:
    """
    Build flow specification dictionary for remote execution.
    For now, creates a minimal spec with a single task representing the flow.
    """
    from .decorators import _infer_entrypoint  # type: ignore[import-private] # noqa: PLC0415

    entrypoint = getattr(flow_fn, "_eap_flow_entry", None)
    if entrypoint is None:
        entrypoint = _infer_entrypoint(flow_fn)

    return {
        "flow_id": f"py.{flow_name}",
        "version": 1,
        "tasks": [
            {
                "id": "task-1",
                "name": flow_name,
                "entrypoint": entrypoint,
            }
        ],
    }


# Transport SPI
class Transport(Protocol):
    async def run(self, flow: str, params: dict[str, Any]) -> dict[str, Any]: ...


class LocalTransport:
    async def run(self, flow: str, params: dict[str, Any]) -> dict[str, Any]:
        return await _run_local(flow, **params)


class HTTPTransport:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def run(self, flow: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=float(os.getenv("EAP_HTTP_TIMEOUT", "60"))) as client:
            try:
                body = RunRequest(flow=flow, params=params).model_dump()
                r = await client.post(f"{self.base_url}/run", json=body)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as e:
                return RunResponse(success=False, message="HTTP error", error=str(e)).model_dump()


def submit_remote_http(
    base: str,
    flow_spec: dict[str, Any],
    deployment: dict[str, Any],
    params: dict[str, Any],
) -> str:
    """
    Submit flow execution request to remote Maestro HTTP endpoint.
    Uses new flow spec format with spec/deployment/params.
    Returns run_id string.
    """
    url = f"{base.rstrip('/')}/run"
    payload = {
        "spec": flow_spec,
        "deployment": deployment,
        "params": params,
    }

    response = httpx.post(url, json=payload, timeout=10.0)
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        raise RuntimeError(f"Remote run failed: {data}")

    run_id = data.get("run_id")
    if not run_id:
        raise RuntimeError(f"Response missing run_id: {data}")

    return str(run_id)


# Public API
def serve(*_args: Any, **_kwargs: Any) -> None:
    """
    Placeholder for future registration with Maestro. No-op in B1/B2.
    Kept to maintain API continuity.
    """
    return None


def run(flow: str, runner: str = "local", **params: Any) -> dict[str, Any]:
    """
    Synchronous helper for scripts/CLI.
    """
    return asyncio.run(arun(flow, runner=runner, **params))


async def arun(flow: str, runner: str = "local", **params: Any) -> dict[str, Any]:
    """
    Async variant. Selects transport by 'runner' or environment.
    """
    import_plugins_from_env()  # EAP_PLUGINS="pkg.module,another.module"

    if runner == "remote" or os.getenv("MAESTRO_ADDR") or os.getenv("ROBOT_ADDR"):
        base = os.getenv("MAESTRO_ADDR") or os.getenv("ROBOT_ADDR")
        if not base:
            return RunResponse(
                success=False,
                message="Remote runner requires MAESTRO_ADDR or ROBOT_ADDR",
                error="ConfigError",
            ).model_dump()
        transport: Transport = HTTPTransport(base)
        resp = await transport.run(flow, params)
        ok = bool(resp.get("success"))
        record_job(flow, "remote", ok, resp.get("error"))
        return resp

    # default local
    resp = await _run_local(flow, **params)
    ok = bool(resp.get("success"))
    record_job(flow, "local", ok, resp.get("error"))
    return resp


# Internal local execution
async def _run_local(flow_name: str, **params: Any) -> dict[str, Any]:
    try:
        fn = get_flow(flow_name)
    except KeyError as e:
        return RunResponse(success=False, message=str(e), error="UnknownFlow").model_dump()

    ctx = RunContext(run_id=str(uuid.uuid4()), tenant=os.getenv("EAP_TENANT"))
    ctx.services.update(build_services(ctx))

    try:
        data = await fn(ctx, **params)
        if not isinstance(data, dict):  # type: ignore[redundant-expr]
            # normalize
            data = {"result": data}
        return RunResponse(success=True, message="OK", data=data).model_dump()
    except Exception as e:
        # Include traceback if EAP_DEBUG=1
        import traceback

        if os.getenv("EAP_DEBUG") == "1":
            tb = traceback.format_exc()
            return RunResponse(success=False, message="Flow failed", error=tb).model_dump()
        return RunResponse(success=False, message="Flow failed", error=str(e)).model_dump()


def run_entrypoint(entry: str, kwargs: dict[str, Any]) -> Any:
    """
    Execute a flow entrypoint string in 'module:func' format.
    Used by robots for remote execution.
    """
    import importlib

    module_name, func_name = entry.split(":", 1)
    mod = importlib.import_module(module_name)
    func_obj = getattr(mod, func_name)
    return func_obj(**kwargs)
