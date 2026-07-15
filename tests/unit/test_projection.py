import numpy as np
import pytest
from scipy.sparse import csr_matrix, issparse  # type: ignore[import-untyped]
from sklearn.decomposition import TruncatedSVD  # type: ignore[import-untyped]

from reviewlens.analysis.projection import project_features
from reviewlens.config import ProjectionConfig
from reviewlens.exceptions import AnalysisError
from reviewlens.models import Diagnostic


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


def test_projection_sampling_is_seeded_fixed_and_unique() -> None:
    matrix = csr_matrix(np.eye(10))
    labels = np.arange(10) % 2
    rows = np.arange(101, 111)
    config = ProjectionConfig(sample_size=4, random_state=7)
    first = project_features(matrix, labels, rows, config)
    second = project_features(matrix, labels, rows, config)
    assert first.data.equals(second.data)
    assert first.data["source_row"].tolist() == [106, 107, 109, 110]
    assert first.data["source_row"].is_unique


def test_source_label_alignment_survives_sampling_and_sort() -> None:
    matrix = csr_matrix(np.eye(8))
    labels = np.arange(100, 108)
    rows = np.array([80, 10, 70, 20, 60, 30, 50, 40])
    result = project_features(
        matrix,
        labels,
        rows,
        ProjectionConfig(sample_size=4),
    )
    label_by_source_row = dict(zip(rows.tolist(), labels.tolist(), strict=True))
    assert result.data["source_row"].tolist() == [20, 50, 60, 80]
    assert result.data["cluster_id"].tolist() == [
        label_by_source_row[source_row]
        for source_row in result.data["source_row"].tolist()
    ]


def test_mismatched_presentation_labels_are_rejected() -> None:
    with pytest.raises(AnalysisError, match="must align"):
        project_features(
            csr_matrix(np.eye(3)),
            np.array([0, 1]),
            np.array([10, 11, 12]),
            ProjectionConfig(),
        )


def test_mismatched_source_rows_are_rejected() -> None:
    with pytest.raises(AnalysisError, match="must align"):
        project_features(
            csr_matrix(np.eye(3)),
            np.array([0, 1, 2]),
            np.array([10, 11]),
            ProjectionConfig(),
        )


def test_truncated_svd_receives_sparse_matrix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_fit_transform = TruncatedSVD.fit_transform
    received: list[object] = []

    def record_fit_transform(
        reducer: TruncatedSVD,
        matrix: csr_matrix,
        *args: object,
        **kwargs: object,
    ) -> object:
        received.append(matrix)
        transformed: object = original_fit_transform(
            reducer,
            matrix,
            *args,
            **kwargs,
        )
        return transformed

    monkeypatch.setattr(TruncatedSVD, "fit_transform", record_fit_transform)
    project_features(
        csr_matrix(np.eye(3)),
        np.array([0, 1, 2]),
        np.array([10, 11, 12]),
        ProjectionConfig(),
    )
    assert len(received) == 1
    assert issparse(received[0])


def test_one_feature_uses_zero_y_and_warning() -> None:
    matrix = csr_matrix([[1.0], [2.0], [3.0]])
    result = project_features(
        matrix,
        np.array([0, 0, 1]),
        np.array([1, 2, 3]),
        ProjectionConfig(),
    )
    assert result.data["x"].tolist() == [1.0, 2.0, 3.0]
    assert result.data["y"].tolist() == [0.0, 0.0, 0.0]
    assert result.diagnostics == (
        Diagnostic(
            severity="warning",
            code="one_dimensional_projection",
            message="Projection used one feature dimension and a zero y-axis.",
            count=None,
        ),
    )


def test_single_sample_multi_feature_projection_pads_y_and_warns() -> None:
    matrix = csr_matrix(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.5, 0.25, 0.75],
            ]
        )
    )
    labels = np.array([10, 11, 12])
    rows = np.array([101, 102, 103])
    config = ProjectionConfig(sample_size=1, random_state=0)
    first = project_features(matrix, labels, rows, config)
    second = project_features(matrix, labels, rows, config)
    assert first.data.equals(second.data)
    assert first.data["source_row"].tolist() == [103]
    assert first.data["cluster_id"].tolist() == [12]
    assert np.isfinite(first.data["x"].iloc[0])
    assert first.data["y"].tolist() == [0.0]
    assert first.diagnostics[0].code == "one_dimensional_projection"
