from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]

from reviewlens.analysis.clustering import cluster_features
from reviewlens.config import ClusteringConfig
from reviewlens.exceptions import AnalysisError, ConfigurationError


def _separated_matrix() -> csr_matrix:
    return csr_matrix(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.0, 1.0, 0.0],
                [0.1, 0.9, 0.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.1, 0.9],
            ]
        )
    )


def test_auto_k_returns_valid_evaluation_and_seeded_labels() -> None:
    first = cluster_features(_separated_matrix(), ClusteringConfig())
    second = cluster_features(_separated_matrix(), ClusteringConfig())
    assert 2 <= first.selected_k <= 5
    assert set(first.evaluation.columns) == {
        "k",
        "inertia",
        "silhouette",
        "valid",
        "reason",
    }
    assert first.labels.tolist() == second.labels.tolist()


def test_auto_k_requires_three_rows() -> None:
    with pytest.raises(AnalysisError, match="at least three"):
        cluster_features(csr_matrix([[1.0, 0.0], [0.0, 1.0]]), ClusteringConfig())


def test_manual_k_is_validated() -> None:
    with pytest.raises(ConfigurationError, match="2 <= k"):
        cluster_features(_separated_matrix(), ClusteringConfig(clusters=6))


def test_manual_k_skips_range_unless_requested() -> None:
    result = cluster_features(_separated_matrix(), ClusteringConfig(clusters=3))
    assert result.selected_k == 3
    assert result.evaluation.empty


def test_empty_manual_evaluation_preserves_schema_dtypes() -> None:
    auto = cluster_features(_separated_matrix(), ClusteringConfig())
    manual = cluster_features(_separated_matrix(), ClusteringConfig(clusters=3))
    assert manual.evaluation.dtypes.to_dict() == auto.evaluation.dtypes.to_dict()


def test_equal_silhouette_scores_choose_smaller_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "reviewlens.analysis.evaluation.silhouette_score",
        lambda *args, **kwargs: 0.5,
    )
    result = cluster_features(_separated_matrix(), ClusteringConfig())
    assert result.selected_k == 2
