from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from reviewlens.exceptions import InputError
from reviewlens.ingestion.normalization import normalize_columns


def _read_header(path: Path, delimiter: str) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration as error:
            raise InputError(
                f"Cannot read CSV dataset {path.name}: file is empty."
            ) from error
        normalize_columns(pd.DataFrame(columns=header))
        for record_number, record in enumerate(reader, start=2):
            if len(record) > len(header):
                raise InputError(
                    f"CSV record {record_number} has {len(record)} fields but "
                    f"the header has {len(header)} columns."
                )
    return header


def load_csv_frame(path: Path, delimiter: str | None) -> pd.DataFrame:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(16_384)
        if not sample:
            raise InputError(f"Cannot read CSV dataset {path.name}: file is empty.")
        selected = delimiter
        if selected is None:
            try:
                selected = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                selected = ","
        header = _read_header(path, selected)
        frame = pd.read_csv(
            path,
            sep=selected,
            encoding="utf-8-sig",
            dtype=str,
            header=0,
            index_col=False,
            names=header,
            keep_default_na=False,
            skip_blank_lines=False,
        )
        frame.columns = header
        return frame.replace("", pd.NA)
    except InputError:
        raise
    except (
        OSError,
        UnicodeError,
        csv.Error,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        TypeError,
        ValueError,
    ) as error:
        raise InputError(f"Cannot read CSV dataset {path.name}: {error}") from error
