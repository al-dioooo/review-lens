from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from reviewlens.config import IngestionConfig
from reviewlens.exceptions import InputError
from reviewlens.ingestion import load_dataset
from reviewlens.ingestion.normalization import normalize_columns


def test_json_list_normalizes_aliases_and_ratings(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(
        json.dumps(
            [
                {"reviewText": "Bagus", "stars": 5, "customField": "x"},
                {"reviewText": "Buruk", "stars": 7, "customField": "y"},
            ]
        ),
        encoding="utf-8",
    )
    loaded = load_dataset(path, config=IngestionConfig())
    assert loaded.frame["review_text"].tolist() == ["Bagus", "Buruk"]
    assert loaded.frame["source_row"].tolist() == [1, 2]
    assert loaded.frame["rating"].tolist()[0] == 5.0
    assert pd.isna(loaded.frame["rating"].tolist()[1])
    assert loaded.frame["custom_field"].tolist() == ["x", "y"]
    assert loaded.source_sha256
    assert loaded.diagnostics[0].code == "invalid_rating"
    assert loaded.diagnostics[0].count == 1


def test_json_object_uses_supported_records_key(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(
        json.dumps({"metadata": {"source": "synthetic"}, "reviews": [{"text": "A"}]}),
        encoding="utf-8",
    )
    loaded = load_dataset(path, config=IngestionConfig())
    assert loaded.frame.loc[0, "review_text"] == "A"


def test_json_object_rejects_ambiguous_arrays(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(
        json.dumps({"reviews": [{"text": "A"}], "data": [{"text": "B"}]}),
        encoding="utf-8",
    )
    with pytest.raises(InputError, match="multiple review arrays"):
        load_dataset(path, config=IngestionConfig())


def test_semicolon_csv_with_bom_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("reviewText;stars\nCepat;5\nLambat;2\n", encoding="utf-8-sig")
    loaded = load_dataset(path, config=IngestionConfig())
    assert loaded.frame[["review_text", "rating"]].to_dict("records") == [
        {"review_text": "Cepat", "rating": 5.0},
        {"review_text": "Lambat", "rating": 2.0},
    ]


def test_normalization_collision_is_fatal() -> None:
    frame = pd.DataFrame([["A", "B"]], columns=["reviewText", "review_text"])
    with pytest.raises(InputError, match="normalize to 'review_text'"):
        normalize_columns(frame)


def test_explicit_text_column_wins(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("text,body\nwrong,right\n", encoding="utf-8")
    loaded = load_dataset(
        path,
        config=IngestionConfig(),
        text_column="body",
    )
    assert loaded.frame.loc[0, "review_text"] == "right"


def test_multiple_implicit_text_aliases_are_fatal(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("text,content\na,b\n", encoding="utf-8")
    with pytest.raises(InputError, match="multiple aliases"):
        load_dataset(path, config=IngestionConfig())


def test_same_source_cannot_be_text_and_rating(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("body\n5\n", encoding="utf-8")
    with pytest.raises(InputError, match="cannot be used for both"):
        load_dataset(
            path,
            config=IngestionConfig(),
            text_column="body",
            rating_column="body",
        )


def test_explicit_text_cannot_duplicate_canonical_text(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("review_text,body\ncanonical,explicit\n", encoding="utf-8")
    with pytest.raises(InputError, match="would both produce 'review_text'"):
        load_dataset(path, config=IngestionConfig(), text_column="body")


def test_explicit_optional_alias_used_as_text_is_not_overwritten(
    tmp_path: Path,
) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("date\nUse this text\n", encoding="utf-8")
    loaded = load_dataset(path, config=IngestionConfig(), text_column="date")
    assert "review_text" in loaded.frame.columns
    assert loaded.frame.loc[0, "review_text"] == "Use this text"
    assert pd.isna(loaded.frame.loc[0, "timestamp"])
