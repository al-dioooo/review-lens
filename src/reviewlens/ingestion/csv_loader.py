from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from reviewlens.exceptions import InputError


def load_csv_frame(path: Path, delimiter: str | None) -> pd.DataFrame:
    try:
        sample = path.read_text(encoding="utf-8-sig")[:16_384]
        selected = delimiter
        if selected is None:
            try:
                selected = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                selected = ","
        return pd.read_csv(path, sep=selected, encoding="utf-8-sig")
    except (OSError, UnicodeError, pd.errors.ParserError) as error:
        raise InputError(f"Cannot read CSV dataset {path.name}: {error}") from error
