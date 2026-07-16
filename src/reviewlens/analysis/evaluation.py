from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]
from sklearn.cluster import KMeans  # type: ignore[import-untyped]
from sklearn.exceptions import ConvergenceWarning  # type: ignore[import-untyped]
from sklearn.metrics import silhouette_score  # type: ignore[import-untyped]

from reviewlens.config import ClusteringConfig


@dataclass(frozen=True, slots=True)
class EvaluationCandidate:
    k: int
    inertia: float | None
    silhouette: float | None
    valid: bool
    reason: str | None
    model: KMeans | None


def fit_candidate(
    matrix: csr_matrix,
    k: int,
    config: ClusteringConfig,
) -> EvaluationCandidate:
    model = KMeans(
        n_clusters=k,
        random_state=config.random_state,
        n_init=config.n_init,
        max_iter=config.max_iter,
    )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            labels = model.fit_predict(matrix)
        if len(np.unique(labels)) != k:
            return EvaluationCandidate(
                k,
                float(model.inertia_),
                None,
                False,
                "fewer_labels_than_requested",
                None,
            )
        sample_size = (
            config.silhouette_sample_size
            if matrix.shape[0] > config.silhouette_sample_size
            else None
        )
        score = silhouette_score(
            matrix,
            labels,
            metric="cosine",
            sample_size=sample_size,
            random_state=config.random_state,
        )
        return EvaluationCandidate(
            k,
            float(model.inertia_),
            float(score),
            True,
            None,
            model,
        )
    except ValueError as error:
        return EvaluationCandidate(k, None, None, False, str(error), None)


def evaluate_candidates(
    matrix: csr_matrix,
    config: ClusteringConfig,
) -> list[EvaluationCandidate]:
    upper = min(config.k_max, matrix.shape[0] - 1)
    return [fit_candidate(matrix, k, config) for k in range(2, upper + 1)]
