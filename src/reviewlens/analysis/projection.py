from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]
from sklearn.decomposition import TruncatedSVD  # type: ignore[import-untyped]

from reviewlens.config import ProjectionConfig
from reviewlens.exceptions import AnalysisError
from reviewlens.models import Diagnostic


@dataclass(frozen=True, slots=True)
class ProjectionResult:
    data: pd.DataFrame
    diagnostics: tuple[Diagnostic, ...]


def _one_dimensional_diagnostics() -> tuple[Diagnostic, ...]:
    return (
        Diagnostic(
            severity="warning",
            code="one_dimensional_projection",
            message="Projection used one feature dimension and a zero y-axis.",
        ),
    )


def project_features(
    matrix: csr_matrix,
    presentation_labels: NDArray[np.int_],
    source_rows: NDArray[np.int_],
    config: ProjectionConfig,
) -> ProjectionResult:
    row_count = matrix.shape[0]
    if len(presentation_labels) != row_count or len(source_rows) != row_count:
        raise AnalysisError(
            "Projection labels and source rows must align with features."
        )
    indices = np.arange(row_count)
    if row_count > config.sample_size:
        rng = np.random.default_rng(config.random_state)
        indices = np.sort(rng.choice(indices, size=config.sample_size, replace=False))
    selected = matrix[indices]
    diagnostics: tuple[Diagnostic, ...] = ()
    if selected.shape[1] == 1:
        x = selected.toarray()[:, 0].astype(float)
        y = np.zeros(len(indices), dtype=float)
        diagnostics = _one_dimensional_diagnostics()
    else:
        component_count = min(
            config.components,
            selected.shape[0],
            selected.shape[1],
        )
        reducer = TruncatedSVD(
            n_components=component_count,
            random_state=config.random_state,
        )
        with np.errstate(divide="ignore", invalid="ignore"):
            coordinates = reducer.fit_transform(selected)
        x = coordinates[:, 0].astype(float)
        if coordinates.shape[1] < 2:
            y = np.zeros(len(indices), dtype=float)
            diagnostics = _one_dimensional_diagnostics()
        else:
            y = coordinates[:, 1].astype(float)
    data = pd.DataFrame(
        {
            "source_row": source_rows[indices],
            "x": x,
            "y": y,
            "cluster_id": presentation_labels[indices],
        }
    ).sort_values("source_row", ignore_index=True)
    return ProjectionResult(data=data, diagnostics=diagnostics)
