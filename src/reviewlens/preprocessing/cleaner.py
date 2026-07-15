from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import pandas as pd

from reviewlens.config import PreprocessingConfig
from reviewlens.exceptions import InputError
from reviewlens.models import Diagnostic

_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")
_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def _is_emoji(character: str) -> bool:
    value = ord(character)
    return (
        0x1F000 <= value <= 0x1FAFF
        or 0x2600 <= value <= 0x27BF
        or 0xFE00 <= value <= 0xFE0F
    )


def clean_text_basic(value: object) -> str:
    if value is None or pd.isna(value):  # type: ignore[call-overload]
        return ""
    text = unicodedata.normalize("NFKC", str(value)).lower()
    text = _URL.sub(" ", text)
    text = "".join(
        " "
        if _is_emoji(character) or unicodedata.category(character).startswith("P")
        else character
        for character in text
    )
    return _WHITESPACE.sub(" ", text).strip()


@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    frame: pd.DataFrame
    modeling_frame: pd.DataFrame
    diagnostics: tuple[Diagnostic, ...]


def preprocess_reviews(
    frame: pd.DataFrame,
    config: PreprocessingConfig,
) -> PreprocessingResult:
    from reviewlens.preprocessing.indonesian import model_tokens

    result = frame.copy()
    result["text_clean"] = result["review_text"].map(clean_text_basic)
    result["text_model"] = result["text_clean"].map(
        lambda text: " ".join(model_tokens(text, config))
    )
    result["included"] = result["text_model"].str.strip().ne("")
    result["drop_reason"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result.loc[~result["included"], "drop_reason"] = "blank_review"
    excluded = int((~result["included"]).sum())
    diagnostics: tuple[Diagnostic, ...] = ()
    if excluded:
        diagnostics = (
            Diagnostic(
                severity="warning",
                code="blank_review_excluded",
                message="Reviews empty after preprocessing were excluded.",
                count=excluded,
            ),
        )
    modeling = result.loc[result["included"]].copy().reset_index(drop=True)
    if modeling.empty:
        raise InputError("No usable reviews remain after preprocessing.")
    return PreprocessingResult(result, modeling, diagnostics)
