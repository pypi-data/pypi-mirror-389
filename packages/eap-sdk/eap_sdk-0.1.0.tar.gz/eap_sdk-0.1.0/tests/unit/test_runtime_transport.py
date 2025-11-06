import pytest

from eap_sdk.runtime import HTTPTransport, LocalTransport


@pytest.mark.asyncio
async def test_local_transport_delegates(monkeypatch):
    called = {}

    async def fake_run_local(flow_name: str, **params):
        called["args"] = (flow_name, params)
        return {"success": True, "data": {}}

    import eap_sdk.runtime as rt

    monkeypatch.setattr(rt, "_run_local", fake_run_local)
    lt = LocalTransport()
    resp = await lt.run("f", {"x": 1})
    assert resp["success"] is True
    assert called["args"][0] == "f"
    assert called["args"][1] == {"x": 1}


@pytest.mark.asyncio
async def test_http_transport_success(monkeypatch):
    class FakeResponse:
        def __init__(self, json_obj):
            self._json = json_obj

        def raise_for_status(self):
            return None

        def json(self):
            return self._json

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            return FakeResponse({"success": True, "data": {"ok": 1}})

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: FakeClient())

    t = HTTPTransport("https://host")
    resp = await t.run("flow", {"a": 1})
    assert resp["success"] is True and resp["data"] == {"ok": 1}


@pytest.mark.asyncio
async def test_http_transport_http_error(monkeypatch):
    class FakeHTTPError(Exception):
        pass

    class FakeResponse:
        def raise_for_status(self):
            raise FakeHTTPError("boom")

        def json(self):
            return {}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            return FakeResponse()

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: FakeClient())
    monkeypatch.setattr(httpx, "HTTPError", FakeHTTPError)

    t = HTTPTransport("https://host")
    resp = await t.run("flow", {"a": 1})
    assert resp["success"] is False
    assert resp["message"] == "HTTP error"
    assert "boom" in resp["error"]
