from __future__ import annotations

import unicodedata

import pandas as pd

from reviewlens.exceptions import InputError


def normalize_column_name(name: str) -> str:
    text = unicodedata.normalize("NFKC", str(name))
    normalized: list[str] = []
    previous: str | None = None
    for character in text:
        if character.isalnum():
            if (
                normalized
                and normalized[-1] != "_"
                and character.isupper()
                and previous is not None
                and (previous.islower() or previous.isdigit())
            ):
                normalized.append("_")
            normalized.append(character.lower())
            previous = character
        else:
            if normalized and normalized[-1] != "_":
                normalized.append("_")
            previous = None
    return "".join(normalized).strip("_")


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
