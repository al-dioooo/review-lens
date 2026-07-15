from __future__ import annotations

import pandas as pd

from reviewlens.analysis.clustering import cluster_features
from reviewlens.analysis.interpretation import interpret_clusters
from reviewlens.analysis.vectorizer import vectorize_reviews
from reviewlens.config import (
    ClusteringConfig,
    InterpretationConfig,
    VectorizerConfig,
)


def _modeling_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_row": [1, 2, 3, 4, 5, 6],
            "review_text": [
                "pelayanan lambat antre lama",
                "antre lama pelayanan lambat",
                "petugas lambat dan antre",
                "tempat bersih nyaman",
                "bersih rapi nyaman",
                "lokasi nyaman dan bersih",
            ],
            "text_clean": [
                "pelayanan lambat antre lama",
                "antre lama pelayanan lambat",
                "petugas lambat dan antre",
                "tempat bersih nyaman",
                "bersih rapi nyaman",
                "lokasi nyaman dan bersih",
            ],
            "text_model": [
                "pelayanan lambat antre lama",
                "antre lama pelayanan lambat",
                "petugas lambat antre",
                "tempat bersih nyaman",
                "bersih rapi nyaman",
                "lokasi nyaman bersih",
            ],
            "rating": pd.Series([2, 2, 1, 5, 4, 5], dtype="Float64"),
        }
    )


def test_interpretation_is_tidy_and_deterministic() -> None:
    frame = _modeling_frame()
    vectorization = vectorize_reviews(frame, VectorizerConfig())
    clustering = cluster_features(
        vectorization.matrix,
        ClusteringConfig(clusters=2),
    )
    result = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(),
    )
    assert result.clusters["cluster_id"].tolist() == [0, 1]
    assert set(result.clusters["rating_signal"]) == {"complaint", "positive"}
    assert result.keywords.groupby("cluster_id").size().between(1, 10).all()
    assert result.keywords.columns.tolist() == [
        "cluster_id",
        "rank",
        "term",
        "score",
    ]
    assert result.reviews["cluster_id"].notna().all()
    assert all(result.clusters["theme"].str.len() > 0)


def test_representatives_are_nearest_and_source_order_breaks_ties() -> None:
    frame = _modeling_frame()
    vectorization = vectorize_reviews(frame, VectorizerConfig())
    clustering = cluster_features(
        vectorization.matrix,
        ClusteringConfig(clusters=2),
    )
    first = interpret_clusters(frame, vectorization, clustering, InterpretationConfig())
    second = interpret_clusters(
        frame, vectorization, clustering, InterpretationConfig()
    )
    assert first.clusters["representative_source_rows"].tolist() == (
        second.clusters["representative_source_rows"].tolist()
    )


def test_rating_free_clusters_use_unknown_signal() -> None:
    frame = _modeling_frame()
    frame["rating"] = pd.Series(pd.NA, index=frame.index, dtype="Float64")
    vectorization = vectorize_reviews(frame, VectorizerConfig())
    clustering = cluster_features(
        vectorization.matrix,
        ClusteringConfig(clusters=2),
    )
    result = interpret_clusters(
        frame, vectorization, clustering, InterpretationConfig()
    )
    assert set(result.clusters["rating_signal"]) == {"unknown"}
    assert "rating_unavailable" in set(result.summary["name"])
