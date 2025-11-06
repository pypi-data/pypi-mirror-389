from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunContext:
    run_id: str
    tenant: str | None = None
    labels: dict[str, str] = field(default_factory=dict)  # type: ignore[assignment]
    services: dict[str, Any] = field(default_factory=dict)  # type: ignore[assignment]

    def get(self, key: str) -> Any:
        return self.services[key]

    def set(self, key: str, value: Any) -> None:
        self.services[key] = value
