import pytest

from eap_sdk import decorators
from eap_sdk.plugins import _SERVICE_FACTORIES
from eap_sdk.runtime import _run_local


@pytest.fixture(autouse=True)
def clear_registry():
    decorators._FLOWS.clear()
    _SERVICE_FACTORIES.clear()
    yield
    decorators._FLOWS.clear()
    _SERVICE_FACTORIES.clear()


@pytest.mark.asyncio
async def test_run_local_happy_path_normalization(monkeypatch):
    @decorators.flow("as_dict")
    async def f1(ctx):
        return {"a": 1}

    r1 = await _run_local("as_dict")
    assert r1["success"] is True
    assert r1["data"] == {"a": 1}

    @decorators.flow("non_dict")
    async def f2(ctx):
        return 42

    r2 = await _run_local("non_dict")
    assert r2["success"] is True
    assert r2["data"] == {"result": 42}


@pytest.mark.asyncio
async def test_run_local_unknown_flow():
    r = await _run_local("missing")
    assert r["success"] is False
    assert "Unknown flow" in r["message"] or "Unknown" in r["error"]


@pytest.mark.asyncio
async def test_run_local_exception_branches(monkeypatch):
    @decorators.flow("boom")
    async def f(ctx):
        raise RuntimeError("bad")

    # no debug: error is str(e)
    monkeypatch.delenv("EAP_DEBUG", raising=False)
    r = await _run_local("boom")
    assert r["success"] is False
    assert r["error"] == "bad"

    # debug branch includes traceback
    monkeypatch.setenv("EAP_DEBUG", "1")
    r2 = await _run_local("boom")
    assert r2["success"] is False
    assert "Traceback" in r2["error"]
