from dataclasses import FrozenInstanceError

import pytest

from reviewlens.config import AnalysisConfig


def test_analysis_defaults_are_reproducible() -> None:
    config = AnalysisConfig()
    assert config.language == "id"
    assert config.preprocessing.stem is False
    assert config.preprocessing.protected_negations == (
        "tidak",
        "tak",
        "bukan",
        "belum",
        "jangan",
        "gak",
        "nggak",
        "enggak",
    )
    assert config.vectorizer.ngram_range == (1, 2)
    assert config.vectorizer.max_features == 50_000
    assert config.clustering.clusters == "auto"
    assert config.clustering.random_state == 42
    assert config.clustering.silhouette_sample_size == 5_000
    assert config.projection.sample_size == 10_000


def test_analysis_config_is_immutable() -> None:
    config = AnalysisConfig()
    with pytest.raises(FrozenInstanceError):
        config.language = "id"  # type: ignore[misc]
