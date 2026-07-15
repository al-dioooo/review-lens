from __future__ import annotations

import pandas as pd
import pytest

from reviewlens.config import PreprocessingConfig
from reviewlens.exceptions import InputError
from reviewlens.preprocessing import preprocess_reviews
from reviewlens.preprocessing.cleaner import clean_text_basic


def _frame(texts: list[object]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_row": range(1, len(texts) + 1),
            "review_text": texts,
            "rating": pd.Series([pd.NA] * len(texts), dtype="Float64"),
        }
    )


def test_basic_cleaning_handles_unicode_url_emoji_and_punctuation() -> None:
    assert clean_text_basic("  LAYANAN!!! https://x.test 😊  ") == "layanan"
    assert clean_text_basic("Kafe—rapi") == "kafe rapi"


def test_slang_and_stopwords_preserve_negation() -> None:
    result = preprocess_reviews(
        _frame(["Pelayanan gk cepat dan tidak ramah"]),
        PreprocessingConfig(),
    )
    text_model = result.modeling_frame.loc[0, "text_model"]
    assert isinstance(text_model, str)
    assert result.modeling_frame.loc[0, "text_model"] == (
        "pelayanan gak cepat tidak ramah"
    )
    assert "tidak" in text_model.split()
    assert "dan" not in text_model.split()


def test_stemming_is_explicit() -> None:
    without_stem = preprocess_reviews(
        _frame(["pelayanan membantu"]),
        PreprocessingConfig(remove_stopwords=False),
    )
    with_stem = preprocess_reviews(
        _frame(["pelayanan membantu"]),
        PreprocessingConfig(remove_stopwords=False, stem=True),
    )
    assert without_stem.modeling_frame.loc[0, "text_model"] == "pelayanan membantu"
    assert with_stem.modeling_frame.loc[0, "text_model"] == "layan bantu"


def test_blank_rows_remain_visible_but_are_excluded() -> None:
    result = preprocess_reviews(_frame(["Bagus", None, "!!!"]), PreprocessingConfig())
    assert result.frame["included"].tolist() == [True, False, False]
    assert pd.isna(result.frame.loc[0, "drop_reason"])
    assert result.frame["drop_reason"].iloc[1:].tolist() == [
        "blank_review",
        "blank_review",
    ]
    assert result.modeling_frame["source_row"].tolist() == [1]
    assert result.diagnostics[0].code == "blank_review_excluded"
    assert result.diagnostics[0].count == 2


def test_all_blank_rows_are_fatal() -> None:
    with pytest.raises(InputError, match="No usable reviews"):
        preprocess_reviews(_frame([None, "!!!"]), PreprocessingConfig())
