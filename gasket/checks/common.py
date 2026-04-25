from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

@dataclass
class Finding:
    path: Path
    line: int
    severity: Literal["error", "warning"]
    code: str
    message: str
