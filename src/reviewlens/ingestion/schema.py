from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from reviewlens.exceptions import InputError
from reviewlens.ingestion.normalization import normalize_column_name, normalize_columns
from reviewlens.models import Diagnostic

TEXT_ALIASES = ("review_text", "text", "review", "content", "review_body")
RATING_ALIASES = ("rating", "stars", "score", "star_rating")
OPTIONAL_ALIASES = {
    "timestamp": ("timestamp", "created_at", "date", "review_date"),
    "location": ("location", "place", "venue", "address"),
    "metadata": ("metadata", "meta"),
}
RESERVED = {
    "source_row",
    "included",
    "drop_reason",
    "text_clean",
    "text_model",
    "cluster_id",
}


@dataclass(frozen=True, slots=True)
class LoadedDataset:
    frame: pd.DataFrame
    source_path: Path
    source_sha256: str
    source_stem: str
    diagnostics: tuple[Diagnostic, ...]


def _select_column(
    columns: pd.Index,
    canonical: str,
    aliases: tuple[str, ...],
    explicit: str | None,
    assignments: dict[str, str],
) -> str | None:
    if explicit is not None:
        selected = normalize_column_name(explicit)
        if selected not in columns:
            raise InputError(f"Column {explicit!r} was not found after normalization.")
        return selected
    present = [
        alias for alias in aliases if alias in columns and alias not in assignments
    ]
    if len(present) > 1:
        raise InputError(f"Found multiple aliases for {canonical}: {present}.")
    return present[0] if present else None


def _assign_column(assignments: dict[str, str], source: str, canonical: str) -> None:
    existing = assignments.get(source)
    if existing is not None and existing != canonical:
        raise InputError(
            f"Column {source!r} cannot be used for both {existing!r} and {canonical!r}."
        )
    assignments[source] = canonical


def _validate_unique_destinations(
    columns: pd.Index, assignments: dict[str, str]
) -> None:
    destinations: dict[str, str] = {}
    for source in columns:
        target = assignments.get(source, source)
        if target in destinations:
            raise InputError(
                f"Columns {destinations[target]!r} and {source!r} "
                f"would both produce {target!r}."
            )
        destinations[target] = source


def canonicalize_schema(
    frame: pd.DataFrame,
    *,
    text_column: str | None,
    rating_column: str | None,
) -> tuple[pd.DataFrame, tuple[Diagnostic, ...]]:
    result = normalize_columns(frame)
    reserved = RESERVED.intersection(result.columns)
    if reserved:
        raise InputError(f"Input uses reserved ReviewLens columns: {sorted(reserved)}.")
    assignments: dict[str, str] = {}
    text = _select_column(
        result.columns, "review_text", TEXT_ALIASES, text_column, assignments
    )
    if text is None:
        raise InputError("A review-text column is required.")
    _assign_column(assignments, text, "review_text")
    rating = _select_column(
        result.columns, "rating", RATING_ALIASES, rating_column, assignments
    )
    if rating is not None:
        _assign_column(assignments, rating, "rating")
    for canonical, aliases in OPTIONAL_ALIASES.items():
        selected = _select_column(result.columns, canonical, aliases, None, assignments)
        if selected is not None:
            _assign_column(assignments, selected, canonical)
    _validate_unique_destinations(result.columns, assignments)
    result = result.rename(columns=assignments)
    result.insert(0, "source_row", range(1, len(result) + 1))
    diagnostics: list[Diagnostic] = []
    if "rating" not in result:
        result["rating"] = pd.Series(pd.NA, index=result.index, dtype="Float64")
    else:
        raw = result["rating"]
        numeric = pd.to_numeric(raw, errors="coerce")
        invalid = raw.notna() & (numeric.isna() | ~numeric.between(1, 5))
        result["rating"] = numeric.mask(invalid).astype("Float64")
        if int(invalid.sum()):
            diagnostics.append(
                Diagnostic(
                    severity="warning",
                    code="invalid_rating",
                    message="Ratings outside numeric range 1-5 were ignored.",
                    count=int(invalid.sum()),
                )
            )
    for canonical in OPTIONAL_ALIASES:
        if canonical not in result:
            result[canonical] = pd.NA
    return result, tuple(diagnostics)
