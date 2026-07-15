from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd


@dataclass(frozen=True, slots=True)
class Diagnostic:
    severity: Literal["info", "warning"]
    code: str
    message: str
    count: int | None = None


@dataclass(frozen=True, slots=True)
class ExportManifest:
    workbook_path: Path
    chart_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    reviews: pd.DataFrame
    clusters: pd.DataFrame
    summary: pd.DataFrame
    keywords: pd.DataFrame
    evaluation: pd.DataFrame
    visual_data: dict[str, pd.DataFrame]
    metadata: dict[str, object]
    diagnostics: tuple[Diagnostic, ...]
    source_stem: str
