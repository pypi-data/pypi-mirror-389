from __future__ import annotations

import argparse
import json
import sys

from .runtime import run as run_sync


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser("eap-sdk", description="SDK runner")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="Run a registered flow")
    r.add_argument("flow", help="Flow name")
    r.add_argument("--runner", default="local", choices=["local", "remote"], help="Execution mode")
    r.add_argument("--param", action="append", default=[], help="k=v pairs (repeatable)")
    r.add_argument("--param-json", default=None, help="JSON object with parameters")
    args = p.parse_args(argv)

    if args.cmd == "run":
        params = {}
        # Optional JSON blob
        if args.param_json:
            try:
                obj = json.loads(args.param_json)
                if isinstance(obj, dict):
                    params.update(obj)  # type: ignore[arg-type]
            except Exception:  # nosec B110 - intentional fallback for malformed JSON
                pass

        def _coerce(value: str):
            # Try JSON first (handles bool, null, numbers, arrays)
            try:
                return json.loads(value)
            except Exception:  # nosec B110 - intentional fallback for non-JSON values
                pass
            # Fallback basic numeric coercion
            try:
                return int(value)
            except Exception:  # nosec B110 - intentional fallback for non-numeric values
                pass
            try:
                return float(value)
            except Exception:  # nosec B110 - intentional fallback for non-numeric values
                pass
            # Keep string as-is
            return value

        for kv in args.param:
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            params[k] = _coerce(v)
        resp = run_sync(args.flow, runner=args.runner, **params)
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        return 0 if resp.get("success") else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
