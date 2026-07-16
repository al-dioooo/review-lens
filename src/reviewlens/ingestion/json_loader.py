from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from reviewlens.exceptions import InputError

RECORD_KEYS = ("reviews", "data", "items", "results")
_MAX_JSON_NESTING = 64


def _validate_json_nesting(value: object, path: Path) -> None:
    stack: list[tuple[object, int]] = [(value, 0)]
    while stack:
        current, parent_depth = stack.pop()
        if not isinstance(current, (dict, list)):
            continue
        depth = parent_depth + 1
        if depth > _MAX_JSON_NESTING:
            raise InputError(
                f"Cannot read JSON dataset {path.name}: nesting exceeds "
                f"{_MAX_JSON_NESTING} container levels."
            )
        children: Iterable[object]
        if isinstance(current, dict):
            children = current.values()
        else:
            children = current
        stack.extend(
            (child, depth) for child in children if isinstance(child, (dict, list))
        )


def load_json_frame(path: Path, records_key: str | None) -> pd.DataFrame:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=str,
        )
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise InputError(f"Cannot read JSON dataset {path.name}: {error}") from error
    _validate_json_nesting(value, path)
    if isinstance(value, list):
        records = value
    elif isinstance(value, dict):
        if records_key is not None:
            if not isinstance(value.get(records_key), list):
                raise InputError(f"JSON key {records_key!r} is not an array.")
            records = value[records_key]
        else:
            matches = [key for key in RECORD_KEYS if isinstance(value.get(key), list)]
            if len(matches) != 1:
                raise InputError(
                    "JSON object must contain exactly one review array; "
                    f"found multiple review arrays or none: {matches}."
                )
            records = value[matches[0]]
    else:
        raise InputError("JSON root must be an array or object.")
    if not all(isinstance(record, dict) for record in records):
        raise InputError("Every JSON review record must be an object.")
    return pd.DataFrame(records, dtype=object)
