from __future__ import annotations

import unicodedata

import pandas as pd

from reviewlens.exceptions import InputError


def normalize_column_name(name: str) -> str:
    text = unicodedata.normalize("NFKC", str(name))
    normalized: list[str] = []
    previous_base: str | None = None
    for character in text:
        category = unicodedata.category(character)[0]
        if category in {"L", "N"}:
            if (
                normalized
                and normalized[-1] != "_"
                and character.isupper()
                and previous_base is not None
                and (previous_base.islower() or previous_base.isdigit())
            ):
                normalized.append("_")
            normalized.append(character)
            previous_base = character
        elif category == "M":
            if previous_base is not None and normalized and normalized[-1] != "_":
                normalized.append(character)
        else:
            if normalized and normalized[-1] != "_":
                normalized.append("_")
            previous_base = None
    lowered = "".join(normalized).strip("_").lower()
    return unicodedata.normalize("NFKC", lowered)


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
