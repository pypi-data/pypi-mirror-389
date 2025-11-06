import json

from eap_sdk.cli import main


def test_cli_run_success_and_param_coercion(monkeypatch, capsys):
    def fake_run(flow, runner="local", **params):
        return {"success": True, "message": "OK", "data": params}

    import eap_sdk.cli as cli

    monkeypatch.setattr(cli, "run_sync", fake_run)

    code = main(
        [
            "run",
            "flow",
            "--runner",
            "local",
            "--param",
            "a=1",
            "--param",
            "b=true",
            "--param-json",
            '{"c":2}',
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["success"] is True
    assert doc["data"] == {"a": 1, "b": True, "c": 2}


def test_cli_run_failure_exit_code(monkeypatch, capsys):
    def fake_run(flow, runner="local", **params):
        return {"success": False, "message": "bad"}

    import eap_sdk.cli as cli

    monkeypatch.setattr(cli, "run_sync", fake_run)
    code = main(["run", "x"])  # minimal
    assert code == 1


def test_cli_param_json_non_dict(monkeypatch, capsys):
    def fake_run(flow, runner="local", **params):
        return {"success": True, "data": params}

    import eap_sdk.cli as cli

    monkeypatch.setattr(cli, "run_sync", fake_run)

    code = main(["run", "flow", "--param-json", "[1,2,3]"])
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["data"] == {}


def test_cli_param_json_malformed(monkeypatch, capsys):
    def fake_run(flow, runner="local", **params):
        return {"success": True, "data": params}

    import eap_sdk.cli as cli

    monkeypatch.setattr(cli, "run_sync", fake_run)

    code = main(["run", "flow", "--param-json", "{invalid json"])
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["data"] == {}


def test_cli_param_without_equals(monkeypatch, capsys):
    def fake_run(flow, runner="local", **params):
        return {"success": True, "data": params}

    import eap_sdk.cli as cli

    monkeypatch.setattr(cli, "run_sync", fake_run)

    code = main(["run", "flow", "--param", "noequals"])
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["data"] == {}


def test_cli_param_coercion_numeric(monkeypatch, capsys):
    def fake_run(flow, runner="local", **params):
        return {"success": True, "data": params}

    import eap_sdk.cli as cli

    monkeypatch.setattr(cli, "run_sync", fake_run)

    code = main(["run", "flow", "--param", "x=42", "--param", "y=3.14"])
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["data"] == {"x": 42, "y": 3.14}


def test_cli_param_coercion_string_fallback(monkeypatch, capsys):
    def fake_run(flow, runner="local", **params):
        return {"success": True, "data": params}

    import eap_sdk.cli as cli

    monkeypatch.setattr(cli, "run_sync", fake_run)

    # Test string that can't be parsed as JSON or number
    code = main(["run", "flow", "--param", "x=hello"])
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["data"] == {"x": "hello"}
