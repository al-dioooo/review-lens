from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]
from sklearn.cluster import KMeans  # type: ignore[import-untyped]
from sklearn.exceptions import ConvergenceWarning  # type: ignore[import-untyped]

from reviewlens.analysis.clustering import cluster_features
from reviewlens.analysis.evaluation import fit_candidate
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


def _collapsed_matrix() -> csr_matrix:
    return csr_matrix(np.ones((3, 2)))


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


@pytest.mark.parametrize("row_count", [6, 12])
def test_auto_evaluation_covers_exact_bounded_candidate_range(
    row_count: int,
) -> None:
    result = cluster_features(csr_matrix(np.eye(row_count)), ClusteringConfig())
    assert result.evaluation["k"].tolist() == list(range(2, min(10, row_count - 1) + 1))


def test_auto_selects_the_greatest_silhouette(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scores = {2: 0.2, 3: 0.9, 4: 0.4, 5: 0.1}

    def score_by_cluster_count(*args: object, **_kwargs: object) -> float:
        labels = np.asarray(args[1])
        return scores[len(np.unique(labels))]

    monkeypatch.setattr(
        "reviewlens.analysis.evaluation.silhouette_score",
        score_by_cluster_count,
    )
    result = cluster_features(_separated_matrix(), ClusteringConfig())
    assert result.selected_k == 3
    assert result.evaluation.set_index("k").loc[3, "silhouette"] == 0.9


def test_fewer_unique_labels_invalidates_candidate() -> None:
    with pytest.warns(ConvergenceWarning):
        candidate = fit_candidate(_collapsed_matrix(), 2, ClusteringConfig())
    assert not candidate.valid
    assert candidate.reason == "fewer_labels_than_requested"
    assert candidate.model is None


def test_silhouette_value_error_invalidates_candidate_with_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_silhouette(*_args: object, **_kwargs: object) -> float:
        raise ValueError("cosine scoring failed")

    monkeypatch.setattr(
        "reviewlens.analysis.evaluation.silhouette_score",
        fail_silhouette,
    )
    candidate = fit_candidate(_separated_matrix(), 3, ClusteringConfig())
    assert not candidate.valid
    assert candidate.reason == "cosine scoring failed"
    assert candidate.model is None


def test_cosine_silhouette_sampling_is_seeded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    matrix = _separated_matrix()
    received_matrix: list[object] = []
    received_options: dict[str, object] = {}

    def record_silhouette(*args: object, **kwargs: object) -> float:
        received_matrix.append(args[0])
        received_options.update(kwargs)
        return 0.5

    monkeypatch.setattr(
        "reviewlens.analysis.evaluation.silhouette_score",
        record_silhouette,
    )
    candidate = fit_candidate(
        matrix,
        3,
        ClusteringConfig(random_state=17, silhouette_sample_size=3),
    )
    assert candidate.valid
    assert received_matrix[0] is matrix
    assert received_options == {
        "metric": "cosine",
        "sample_size": 3,
        "random_state": 17,
    }


def test_all_invalid_auto_candidates_raise_analysis_error() -> None:
    with pytest.warns(ConvergenceWarning):
        with pytest.raises(AnalysisError, match="No candidate cluster count"):
            cluster_features(_collapsed_matrix(), ClusteringConfig())


def test_invalid_manual_candidate_raises_analysis_error() -> None:
    with pytest.warns(ConvergenceWarning):
        with pytest.raises(AnalysisError, match="Manual cluster count 2 is invalid"):
            cluster_features(
                _collapsed_matrix(),
                ClusteringConfig(clusters=2),
            )


def test_auto_fits_each_candidate_once_and_reuses_winner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_fit = KMeans.fit
    fit_calls: dict[int, int] = {}
    fitted_models: dict[int, KMeans] = {}

    def track_fit(
        model: KMeans,
        matrix: csr_matrix,
        *args: object,
        **kwargs: object,
    ) -> KMeans:
        identity = id(model)
        fit_calls[identity] = fit_calls.get(identity, 0) + 1
        fitted_models[identity] = model
        original_fit(model, matrix, *args, **kwargs)
        return model

    monkeypatch.setattr(KMeans, "fit", track_fit)
    result = cluster_features(_separated_matrix(), ClusteringConfig())
    candidate_models = list(fitted_models.values())
    assert [int(model.n_clusters) for model in candidate_models] == [2, 3, 4, 5]
    assert all(fit_calls[id(model)] == 1 for model in candidate_models)
    winning_models = [
        model
        for model in candidate_models
        if int(model.n_clusters) == result.selected_k
    ]
    assert len(winning_models) == 1
    assert result.model is winning_models[0]
    assert fit_calls[id(result.model)] == 1


def test_manual_evaluation_uses_bounded_candidate_range() -> None:
    result = cluster_features(
        _separated_matrix(),
        ClusteringConfig(clusters=3, evaluate_manual=True, k_max=4),
    )
    assert result.selected_k == 3
    assert result.evaluation["k"].tolist() == [2, 3, 4]
