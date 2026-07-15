from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Diagnostic:
    severity: Literal["info", "warning"]
    code: str
    message: str
    count: int | None = None
