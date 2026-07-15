from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]
from sklearn.cluster import KMeans  # type: ignore[import-untyped]

from reviewlens.analysis.evaluation import (
    EvaluationCandidate,
    evaluate_candidates,
    fit_candidate,
)
from reviewlens.config import ClusteringConfig
from reviewlens.exceptions import AnalysisError, ConfigurationError


@dataclass(frozen=True, slots=True)
class ClusteringResult:
    model: KMeans
    labels: NDArray[np.int_]
    selected_k: int
    evaluation: pd.DataFrame


def _evaluation_frame(candidates: list[EvaluationCandidate]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(
        [
            {
                "k": candidate.k,
                "inertia": candidate.inertia,
                "silhouette": candidate.silhouette,
                "valid": candidate.valid,
                "reason": candidate.reason,
            }
            for candidate in candidates
        ],
        columns=["k", "inertia", "silhouette", "valid", "reason"],
    )
    return frame.astype(
        {
            "k": "int64",
            "inertia": "float64",
            "silhouette": "float64",
            "valid": "bool",
            "reason": "object",
        }
    )


def _candidate_rank(candidate: EvaluationCandidate) -> tuple[float, int]:
    assert candidate.silhouette is not None
    return candidate.silhouette, -candidate.k


def cluster_features(
    matrix: csr_matrix,
    config: ClusteringConfig,
) -> ClusteringResult:
    row_count = matrix.shape[0]
    if config.clusters == "auto":
        if row_count < 3:
            raise AnalysisError("Automatic clustering requires at least three reviews.")
        candidates = evaluate_candidates(matrix, config)
        valid = [
            candidate
            for candidate in candidates
            if candidate.valid and candidate.silhouette is not None
        ]
        if not valid:
            raise AnalysisError(
                "No candidate cluster count produced a valid silhouette score."
            )
        winner = max(valid, key=_candidate_rank)
        assert winner.model is not None
        return ClusteringResult(
            model=winner.model,
            labels=np.asarray(winner.model.labels_, dtype=np.int_),
            selected_k=winner.k,
            evaluation=_evaluation_frame(candidates),
        )
    selected = int(config.clusters)
    if not 2 <= selected < row_count:
        raise ConfigurationError(
            f"Manual clusters must satisfy 2 <= k < {row_count}; received {selected}."
        )
    chosen = fit_candidate(matrix, selected, config)
    if not chosen.valid or chosen.model is None:
        raise AnalysisError(
            f"Manual cluster count {selected} is invalid: {chosen.reason}."
        )
    evaluation = (
        _evaluation_frame(evaluate_candidates(matrix, config))
        if config.evaluate_manual
        else _evaluation_frame([])
    )
    return ClusteringResult(
        model=chosen.model,
        labels=np.asarray(chosen.model.labels_, dtype=np.int_),
        selected_k=selected,
        evaluation=evaluation,
    )
