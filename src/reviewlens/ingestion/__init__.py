from __future__ import annotations

import hashlib
from pathlib import Path

from reviewlens.config import IngestionConfig
from reviewlens.exceptions import InputError
from reviewlens.ingestion.csv_loader import load_csv_frame
from reviewlens.ingestion.json_loader import load_json_frame
from reviewlens.ingestion.schema import LoadedDataset, canonicalize_schema


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_dataset(
    path: str | Path,
    *,
    config: IngestionConfig,
    text_column: str | None = None,
    rating_column: str | None = None,
) -> LoadedDataset:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise InputError(f"Dataset does not exist or is not a file: {source}.")
    suffix = source.suffix.lower()
    if suffix == ".csv":
        raw = load_csv_frame(source, config.csv_delimiter)
    elif suffix == ".json":
        raw = load_json_frame(source, config.records_key)
    else:
        raise InputError("Supported dataset extensions are .csv and .json.")
    if raw.empty:
        raise InputError("Dataset contains no review records.")
    frame, diagnostics = canonicalize_schema(
        raw, text_column=text_column, rating_column=rating_column
    )
    return LoadedDataset(
        frame=frame,
        source_path=source,
        source_sha256=_sha256(source),
        source_stem=source.stem,
        diagnostics=diagnostics,
    )
