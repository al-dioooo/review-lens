from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from reviewlens.config import IngestionConfig
from reviewlens.exceptions import InputError
from reviewlens.ingestion import load_dataset
from reviewlens.ingestion.normalization import normalize_column_name, normalize_columns


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


def test_csv_preserves_literal_sentinels_and_leading_zero_text(
    tmp_path: Path,
) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text(
        "text,rating,reference\nNA,NA,NA\nN/A,N/A,N/A\nnull,null,null\n001,,\n",
        encoding="utf-8",
    )

    loaded = load_dataset(path, config=IngestionConfig())

    assert loaded.frame["review_text"].tolist() == ["NA", "N/A", "null", "001"]
    assert loaded.frame["reference"].iloc[:3].tolist() == ["NA", "N/A", "null"]
    assert pd.isna(loaded.frame.loc[3, "reference"])
    assert loaded.frame["rating"].isna().all()
    assert len(loaded.diagnostics) == 1
    assert loaded.diagnostics[0].code == "invalid_rating"
    assert loaded.diagnostics[0].count == 3


def test_csv_retains_fully_blank_records_with_stable_source_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text(
        "text,rating\nBagus,5\n\nBuruk,1\n",
        encoding="utf-8",
    )

    loaded = load_dataset(path, config=IngestionConfig())

    assert loaded.frame["source_row"].tolist() == [1, 2, 3]
    assert loaded.frame["review_text"].iloc[0] == "Bagus"
    assert loaded.frame["review_text"].iloc[2] == "Buruk"
    assert pd.isna(loaded.frame.loc[1, "review_text"])
    assert pd.isna(loaded.frame.loc[1, "rating"])


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("text,text\nfirst,second\n", "normalize to 'text'"),
        ("text,,rating\nfirst,second,5\n", "empty name"),
    ],
)
def test_csv_rejects_invalid_raw_headers_before_pandas_mangling(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(InputError, match=message):
        load_dataset(path, config=IngestionConfig())


def test_csv_rejects_records_wider_than_the_raw_header(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text(
        "text,rating\nA,5,unexpected\nB,4,unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(InputError, match=r"record 2.*3 fields.*2 columns"):
        load_dataset(path, config=IngestionConfig())


def test_empty_csv_is_a_public_input_error(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")

    with pytest.raises(InputError, match=r"CSV|review records"):
        load_dataset(path, config=IngestionConfig())


@pytest.mark.parametrize(
    ("content", "location"),
    [
        (b"te\x00xt,rating\nA,5\n", "header"),
        (b"text,rating\nA\x00B,5\n", "record 2"),
    ],
)
def test_csv_rejects_nul_characters_before_pandas_can_truncate(
    tmp_path: Path,
    content: bytes,
    location: str,
) -> None:
    path = tmp_path / "nul.csv"
    path.write_bytes(content)

    with pytest.raises(InputError, match=rf"(?i){location}.*NUL"):
        load_dataset(path, config=IngestionConfig())


@pytest.mark.parametrize("review_text", [["nested", "review"], {"nested": "review"}])
def test_json_rejects_non_scalar_review_text(
    tmp_path: Path,
    review_text: object,
) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps([{"text": review_text}]), encoding="utf-8")

    with pytest.raises(InputError, match=r"(?i)review text.*scalar"):
        load_dataset(path, config=IngestionConfig())


def test_json_boolean_and_structured_ratings_are_invalid(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(
        json.dumps(
            [
                {"text": "A", "rating": True},
                {"text": "B", "rating": False},
                {"text": "C", "rating": {"value": 5}},
                {"text": "D", "rating": [5]},
                {"text": "E", "rating": 5},
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_dataset(path, config=IngestionConfig())

    assert loaded.frame["rating"].iloc[:4].isna().all()
    assert loaded.frame.loc[4, "rating"] == 5.0
    assert loaded.diagnostics[0].code == "invalid_rating"
    assert loaded.diagnostics[0].count == 4


def test_json_huge_rating_is_invalid_without_overflow(tmp_path: Path) -> None:
    path = tmp_path / "huge-rating.json"
    huge_rating = "9" * 1_001
    path.write_text(
        '[{"text":"A","rating":'
        + huge_rating
        + '},{"text":"B","rating":null},{"text":"C","rating":5}]',
        encoding="utf-8",
    )

    loaded = load_dataset(path, config=IngestionConfig())

    assert loaded.frame["rating"].iloc[:2].isna().all()
    assert loaded.frame.loc[2, "rating"] == 5.0
    assert loaded.frame["rating"].dtype == pd.Float64Dtype()
    assert len(loaded.diagnostics) == 1
    assert loaded.diagnostics[0].severity == "warning"
    assert loaded.diagnostics[0].code == "invalid_rating"
    assert loaded.diagnostics[0].count == 1
    assert "finite numeric values from 1 to 5" in loaded.diagnostics[0].message


def test_json_nonfinite_constants_are_invalid_but_missing_is_not(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nonfinite-ratings.json"
    path.write_text(
        "["
        '{"text":"A","rating":NaN},'
        '{"text":"B","rating":Infinity},'
        '{"text":"C","rating":-Infinity},'
        '{"text":"D"},'
        '{"text":"E","rating":null},'
        '{"text":"F","rating":5}'
        "]",
        encoding="utf-8",
    )

    loaded = load_dataset(path, config=IngestionConfig())

    assert loaded.frame["rating"].iloc[:5].isna().all()
    assert loaded.frame.loc[5, "rating"] == 5.0
    assert loaded.frame["rating"].dtype == pd.Float64Dtype()
    assert len(loaded.diagnostics) == 1
    assert loaded.diagnostics[0].severity == "warning"
    assert loaded.diagnostics[0].code == "invalid_rating"
    assert loaded.diagnostics[0].count == 3


def test_rating_coercion_keeps_missing_unflagged_and_rejects_nonfinite(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ratings.csv"
    path.write_text(
        "text,rating\nA,\nB,NaN\nC,inf\nD,-inf\nE,5\n",
        encoding="utf-8",
    )

    loaded = load_dataset(path, config=IngestionConfig())

    assert loaded.frame["rating"].iloc[:4].isna().all()
    assert loaded.frame.loc[4, "rating"] == 5.0
    assert len(loaded.diagnostics) == 1
    assert loaded.diagnostics[0].code == "invalid_rating"
    assert loaded.diagnostics[0].count == 3


def test_json_integer_digit_limit_is_a_public_input_error(tmp_path: Path) -> None:
    path = tmp_path / "digit-limit.json"
    path.write_text(
        '[{"text":"A","rating":' + "9" * 5_000 + "}]",
        encoding="utf-8",
    )

    with pytest.raises(InputError, match=r"Cannot read JSON"):
        load_dataset(path, config=IngestionConfig())


def test_json_recursion_limit_is_a_public_input_error(tmp_path: Path) -> None:
    path = tmp_path / "recursion-limit.json"
    nested_value = "[" * 1_100 + "0" + "]" * 1_100
    path.write_text(
        '[{"text":"A","metadata":' + nested_value + "}]",
        encoding="utf-8",
    )

    with pytest.raises(InputError, match=r"Cannot read JSON"):
        load_dataset(path, config=IngestionConfig())


def test_normalization_collision_is_fatal() -> None:
    frame = pd.DataFrame([["A", "B"]], columns=["reviewText", "review_text"])
    with pytest.raises(InputError, match="normalize to 'review_text'"):
        normalize_columns(frame)


def test_column_normalization_is_nfkc_and_unicode_alphanumeric_aware() -> None:
    assert normalize_column_name("Téks Ulasan") == "téks_ulasan"
    assert (
        normalize_column_name("\uff32\uff45\uff56\uff49\uff45\uff57 Text")
        == "review_text"
    )
    assert normalize_column_name("reviewText") == "review_text"
    assert normalize_column_name("URLValue") == "urlvalue"
    assert normalize_column_name("HTTP2XX") == "http2_xx"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("İ", "i\u0307"),
        ("नमस्ते", "नमस्ते"),
        ("مُراجعة", "مُراجعة"),
    ],
)
def test_unicode_column_normalization_preserves_marks_and_is_idempotent(
    source: str,
    expected: str,
) -> None:
    normalized = normalize_column_name(source)

    assert normalized == expected
    assert normalize_column_name(normalized) == normalized


def test_unattached_unicode_marks_are_not_column_name_content() -> None:
    assert normalize_column_name("\u0301") == ""
    assert normalize_column_name("\u0301Review") == "review"


def test_unicode_normalization_collision_is_fatal() -> None:
    frame = pd.DataFrame([["A", "B"]], columns=["İ", "i\u0307"])

    with pytest.raises(InputError, match="normalize to 'i̇'"):
        normalize_columns(frame)


def test_explicit_normalized_unicode_text_column_resolves(tmp_path: Path) -> None:
    path = tmp_path / "unicode-header.csv"
    path.write_text("İ\nBagus\n", encoding="utf-8")
    normalized_override = normalize_column_name("İ")

    loaded = load_dataset(
        path,
        config=IngestionConfig(),
        text_column=normalized_override,
    )

    assert loaded.frame.loc[0, "review_text"] == "Bagus"


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
