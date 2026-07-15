from __future__ import annotations

import re

import pandas as pd

from reviewlens.exceptions import InputError

_CASE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SEPARATORS = re.compile(r"[^0-9A-Za-z]+")


def normalize_column_name(name: str) -> str:
    split = _CASE_BOUNDARY.sub("_", str(name))
    return _SEPARATORS.sub("_", split).strip("_").lower()


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = [normalize_column_name(str(column)) for column in frame.columns]
    seen: dict[str, str] = {}
    for original, target in zip(frame.columns, normalized, strict=True):
        if not target:
            raise InputError(f"Column {original!r} normalizes to an empty name.")
        if target in seen:
            raise InputError(
                f"Columns {seen[target]!r} and {original!r} normalize to {target!r}."
            )
        seen[target] = str(original)
    result = frame.copy()
    result.columns = normalized
    return result
