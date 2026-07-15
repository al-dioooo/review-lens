import numpy as np
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]

from reviewlens.analysis.projection import project_features
from reviewlens.config import ProjectionConfig


def test_projection_is_seeded_and_aligned() -> None:
    matrix = csr_matrix(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.9, 0.1],
            ]
        )
    )
    labels = np.array([0, 0, 1, 1])
    rows = np.array([10, 11, 12, 13])
    first = project_features(matrix, labels, rows, ProjectionConfig())
    second = project_features(matrix, labels, rows, ProjectionConfig())
    assert first.data.columns.tolist() == ["source_row", "x", "y", "cluster_id"]
    assert first.data.equals(second.data)
    assert first.data["source_row"].tolist() == [10, 11, 12, 13]


def test_projection_samples_at_most_configured_rows() -> None:
    matrix = csr_matrix(np.eye(20))
    labels = np.arange(20) % 2
    rows = np.arange(1, 21)
    result = project_features(
        matrix,
        labels,
        rows,
        ProjectionConfig(sample_size=5),
    )
    assert len(result.data) == 5
    assert result.data["source_row"].is_monotonic_increasing


def test_one_feature_uses_zero_y_and_warning() -> None:
    matrix = csr_matrix([[1.0], [2.0], [3.0]])
    result = project_features(
        matrix,
        np.array([0, 0, 1]),
        np.array([1, 2, 3]),
        ProjectionConfig(),
    )
    assert result.data["y"].tolist() == [0.0, 0.0, 0.0]
    assert result.diagnostics[0].code == "one_dimensional_projection"
