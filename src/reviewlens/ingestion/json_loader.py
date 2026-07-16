from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from reviewlens.exceptions import InputError

RECORD_KEYS = ("reviews", "data", "items", "results")


def load_json_frame(path: Path, records_key: str | None) -> pd.DataFrame:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=str,
        )
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise InputError(f"Cannot read JSON dataset {path.name}: {error}") from error
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
