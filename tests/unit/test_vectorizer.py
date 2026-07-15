import pandas as pd
import pytest

from reviewlens.analysis.vectorizer import vectorize_reviews
from reviewlens.config import VectorizerConfig
from reviewlens.exceptions import AnalysisError


def test_vectorizer_uses_sparse_unigrams_and_bigrams() -> None:
    frame = pd.DataFrame(
        {"text_model": ["pelayanan cepat ramah", "pelayanan lambat antre"]}
    )
    result = vectorize_reviews(frame, VectorizerConfig())
    features = set(result.vectorizer.get_feature_names_out())
    assert result.matrix.shape[0] == 2
    assert "pelayanan" in features
    assert "pelayanan cepat" in features


def test_identical_feature_rows_are_rejected() -> None:
    frame = pd.DataFrame({"text_model": ["sama persis", "sama persis", "sama persis"]})
    with pytest.raises(AnalysisError, match="distinguishable"):
        vectorize_reviews(frame, VectorizerConfig())


def test_empty_vocabulary_has_actionable_error() -> None:
    frame = pd.DataFrame({"text_model": ["a", "b"]})
    with pytest.raises(AnalysisError, match="vocabulary"):
        vectorize_reviews(frame, VectorizerConfig())
