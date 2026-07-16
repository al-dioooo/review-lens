from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd
from pandas.api.types import is_scalar

_EXCEL_CELL_LIMIT = 32_767
_FORMULA_PREFIXES = frozenset("=+-@")


def _is_missing(value: object) -> bool:
    if value is None or value is pd.NA:
        return True
    if not is_scalar(value):
        return False
    try:
        return bool(value != value)
    except (TypeError, ValueError):
        return False


def safe_excel_value(value: object) -> tuple[object, bool]:
    """Return an Excel-safe scalar and whether its text was truncated."""
    if _is_missing(value):
        return None, False
    if isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    elif isinstance(value, (list, tuple)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    elif isinstance(value, Path):
        value = str(value)
    elif isinstance(value, int):
        try:
            float(value)
        except OverflowError:
            value = str(value)

    if not isinstance(value, str):
        return value, False

    stripped = value.lstrip()
    if stripped and stripped[0] in _FORMULA_PREFIXES:
        value = "'" + value
    truncated = len(value) > _EXCEL_CELL_LIMIT
    return value[:_EXCEL_CELL_LIMIT], truncated


def sanitize_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Copy and sanitize a frame without mutating its source values."""
    sanitized = frame.astype(object).copy(deep=True)
    truncated_count = 0
    for row_index in range(len(sanitized.index)):
        for column_index in range(len(sanitized.columns)):
            value, truncated = safe_excel_value(sanitized.iat[row_index, column_index])
            sanitized.iat[row_index, column_index] = cast(Any, value)
            truncated_count += int(truncated)
    return sanitized, truncated_count


__all__ = ["safe_excel_value", "sanitize_frame"]
