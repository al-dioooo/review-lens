from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]
from sklearn.cluster import KMeans  # type: ignore[import-untyped]
from sklearn.feature_extraction.text import (  # type: ignore[import-untyped]
    TfidfVectorizer,
)

from reviewlens.analysis.clustering import ClusteringResult, cluster_features
from reviewlens.analysis.interpretation import interpret_clusters, rating_signal
from reviewlens.analysis.vectorizer import VectorizationResult, vectorize_reviews
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


def _controlled_results(
    matrix_rows: list[list[float]],
    labels: list[int],
    centers: list[list[float]],
    terms: tuple[str, ...],
) -> tuple[VectorizationResult, ClusteringResult]:
    vectorizer = TfidfVectorizer(
        vocabulary={term: index for index, term in enumerate(terms)}
    )
    vectorizer.fit([" ".join(terms)])
    model = KMeans(n_clusters=len(centers), random_state=0, n_init=1)
    model.cluster_centers_ = np.asarray(centers, dtype=float)
    vectorization = VectorizationResult(
        matrix=csr_matrix(np.asarray(matrix_rows, dtype=float)),
        vectorizer=vectorizer,
    )
    clustering = ClusteringResult(
        model=model,
        labels=np.asarray(labels, dtype=np.int_),
        selected_k=len(centers),
        evaluation=pd.DataFrame(
            columns=["k", "inertia", "silhouette", "valid", "reason"]
        ),
    )
    return vectorization, clustering


def _controlled_two_cluster_case(
    *,
    rating_free: bool = False,
) -> tuple[pd.DataFrame, VectorizationResult, ClusteringResult]:
    ratings: list[float | None] = (
        [None] * 6 if rating_free else [2.0, None, 4.0, 3.0, 3.0, None]
    )
    review_text = [
        "alpha exact",
        "alpha tie high",
        "alpha tie low",
        "zeta sixty",
        "zeta fifty",
        "zeta forty",
    ]
    frame = pd.DataFrame(
        {
            "source_row": [30, 20, 10, 60, 50, 40],
            "review_text": review_text,
            "text_clean": review_text,
            "text_model": review_text,
            "rating": pd.Series(ratings, dtype="Float64"),
        }
    )
    vectorization, clustering = _controlled_results(
        matrix_rows=[
            [1.0, 0.0, 0.0, 0.0],
            [0.8, 0.2, 0.0, 0.0],
            [0.8, 0.2, 0.0, 0.0],
            [0.0, 0.4, 0.4, 0.8],
            [0.0, 0.4, 0.4, 0.8],
            [0.0, 0.4, 0.4, 0.8],
        ],
        labels=[1, 1, 1, 0, 0, 0],
        centers=[
            [0.0, 0.4, 0.4, 0.8],
            [1.0, 0.0, 0.0, 0.0],
        ],
        terms=("alpha", "beta", "gamma", "zeta"),
    )
    return frame, vectorization, clustering


def _controlled_four_cluster_case() -> tuple[
    pd.DataFrame, VectorizationResult, ClusteringResult
]:
    labels = [0, 1, 2, 3, 2, 0, 1, 2, 3]
    center_by_label = [
        [0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
    ]
    review_text = [f"review {index}" for index in range(1, 10)]
    frame = pd.DataFrame(
        {
            "source_row": list(range(1, 10)),
            "review_text": review_text,
            "text_clean": review_text,
            "text_model": review_text,
            "rating": pd.Series([None] * 9, dtype="Float64"),
        }
    )
    vectorization, clustering = _controlled_results(
        matrix_rows=[center_by_label[label] for label in labels],
        labels=labels,
        centers=center_by_label,
        terms=("alpha", "beta", "gamma"),
    )
    return frame, vectorization, clustering


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


def test_keywords_sort_by_descending_score_then_ascending_term() -> None:
    frame, vectorization, clustering = _controlled_two_cluster_case()
    result = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(keyword_count=4),
    )
    tied_cluster = result.keywords.loc[result.keywords["cluster_id"] == 1]
    assert tied_cluster["term"].tolist() == ["zeta", "beta", "gamma"]
    assert tied_cluster["score"].tolist() == pytest.approx([0.8, 0.4, 0.4])


@pytest.mark.parametrize(
    ("average", "expected"),
    [
        (None, "unknown"),
        (float("nan"), "unknown"),
        (2.9999, "complaint"),
        (3.0, "mixed"),
        (3.9999, "mixed"),
        (4.0, "positive"),
    ],
)
def test_rating_signal_uses_exact_boundaries(
    average: float | None,
    expected: str,
) -> None:
    assert rating_signal(average) == expected


def test_partial_missing_ratings_are_ignored_in_cluster_and_overall_means() -> None:
    frame, vectorization, clustering = _controlled_two_cluster_case()
    result = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(),
    )
    assert result.clusters["average_rating"].tolist() == pytest.approx([3.0, 3.0])
    overall = result.summary.loc[
        result.summary["name"] == "overall_average_rating"
    ].iloc[0]
    assert float(overall["value"]) == pytest.approx(3.0)
    assert overall["details"] == "Rata-rata dari 4 rating yang tersedia."


def test_representatives_use_cosine_distance_then_source_row_for_a_tie() -> None:
    frame, vectorization, clustering = _controlled_two_cluster_case()
    result = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(representative_count=3),
    )
    first_cluster = result.clusters.iloc[0]
    assert first_cluster["representative_source_rows"] == (30, 10, 20)
    assert first_cluster["representative_reviews"] == (
        "alpha exact",
        "alpha tie low",
        "alpha tie high",
    )


def test_presentation_ids_follow_count_theme_and_original_label_without_leaks() -> None:
    frame, vectorization, clustering = _controlled_four_cluster_case()
    result = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(keyword_count=1, representative_count=1),
    )
    assert clustering.labels.tolist() == [0, 1, 2, 3, 2, 0, 1, 2, 3]
    expected_labels = [2, 3, 0, 1, 0, 2, 3, 0, 1]
    assert result.presentation_labels.tolist() == expected_labels
    assert result.reviews["cluster_id"].tolist() == expected_labels
    assert result.reviews["cluster_id"].tolist() != clustering.labels.tolist()
    assert result.clusters["cluster_id"].tolist() == [0, 1, 2, 3]
    assert result.clusters["review_count"].tolist() == [3, 2, 2, 2]
    assert result.clusters["theme"].tolist() == ["gamma", "alpha", "beta", "beta"]
    assert result.keywords["cluster_id"].tolist() == [0, 1, 2, 3]
    largest = result.summary.loc[result.summary["name"] == "largest_cluster"].iloc[0]
    assert largest["value"] == 0
    assert largest["details"] == "Cluster 0: gamma (3 ulasan, 33.3%)."
    for output in (result.reviews, result.clusters, result.summary, result.keywords):
        assert not any(
            "raw" in str(column) or "original" in str(column)
            for column in output.columns
        )


def test_cluster_schema_templates_tuple_fields_and_keyword_ranks_are_exact() -> None:
    frame, vectorization, clustering = _controlled_two_cluster_case()
    rated = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(keyword_count=4, representative_count=3),
    )
    assert rated.clusters.columns.tolist() == [
        "cluster_id",
        "review_count",
        "share",
        "average_rating",
        "rating_signal",
        "theme",
        "summary",
        "keywords",
        "representative_reviews",
        "representative_source_rows",
    ]
    assert rated.clusters["summary"].tolist() == [
        "Cluster 0 mencakup 3 ulasan (50.0%) dengan rata-rata rating "
        "3.00/5. Tema utama: alpha, beta.",
        "Cluster 1 mencakup 3 ulasan (50.0%) dengan rata-rata rating "
        "3.00/5. Tema utama: zeta, beta, gamma.",
    ]
    assert rated.clusters["keywords"].tolist() == [
        ("alpha", "beta"),
        ("zeta", "beta", "gamma"),
    ]
    assert all(
        isinstance(value, tuple)
        for column in (
            "keywords",
            "representative_reviews",
            "representative_source_rows",
        )
        for value in rated.clusters[column]
    )
    assert rated.keywords.groupby("cluster_id")["rank"].apply(list).tolist() == [
        [1, 2],
        [1, 2, 3],
    ]

    rating_free_frame, _, _ = _controlled_two_cluster_case(rating_free=True)
    rating_free = interpret_clusters(
        rating_free_frame,
        vectorization,
        clustering,
        InterpretationConfig(keyword_count=4, representative_count=3),
    )
    assert rating_free.clusters["summary"].tolist() == [
        "Cluster 0 mencakup 3 ulasan (50.0%). Tema utama: alpha, beta.",
        "Cluster 1 mencakup 3 ulasan (50.0%). Tema utama: zeta, beta, gamma.",
    ]


def test_dataset_summary_rows_are_exact_and_rating_ties_choose_cluster_zero() -> None:
    frame, vectorization, clustering = _controlled_two_cluster_case()
    rated = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(),
    ).summary
    assert rated.columns.tolist() == ["category", "name", "value", "details"]
    assert rated["category"].tolist() == [
        "analysis",
        "analysis",
        "rating",
        "highlight",
        "highlight",
        "highlight",
    ]
    assert rated["name"].tolist() == [
        "input-ready",
        "selected_k",
        "overall_average_rating",
        "largest_cluster",
        "lowest_rated_cluster",
        "highest_rated_cluster",
    ]
    assert rated["value"].tolist() == [6, 2, 3.0, 0, 0, 0]
    assert rated["details"].tolist() == [
        "Ulasan yang dipertahankan untuk analisis.",
        "Jumlah cluster yang digunakan.",
        "Rata-rata dari 4 rating yang tersedia.",
        "Cluster 0: alpha · beta (3 ulasan, 50.0%).",
        "Cluster 0: alpha · beta (rata-rata rating 3.00/5).",
        "Cluster 0: alpha · beta (rata-rata rating 3.00/5).",
    ]

    rating_free_frame, _, _ = _controlled_two_cluster_case(rating_free=True)
    rating_free = interpret_clusters(
        rating_free_frame,
        vectorization,
        clustering,
        InterpretationConfig(),
    ).summary
    assert rating_free["category"].tolist() == [
        "analysis",
        "analysis",
        "highlight",
        "rating",
    ]
    assert rating_free["name"].tolist() == [
        "input-ready",
        "selected_k",
        "largest_cluster",
        "rating_unavailable",
    ]
    assert rating_free["value"].tolist() == [6, 2, 0, "unknown"]
    assert rating_free["details"].tolist() == [
        "Ulasan yang dipertahankan untuk analisis.",
        "Jumlah cluster yang digunakan.",
        "Cluster 0: alpha · beta (3 ulasan, 50.0%).",
        "Insight berbasis rating tidak tersedia.",
    ]


def test_all_interpretation_outputs_are_repeatable() -> None:
    frame, vectorization, clustering = _controlled_two_cluster_case()
    first = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(),
    )
    second = interpret_clusters(
        frame,
        vectorization,
        clustering,
        InterpretationConfig(),
    )
    pd.testing.assert_frame_equal(first.reviews, second.reviews)
    pd.testing.assert_frame_equal(first.clusters, second.clusters)
    pd.testing.assert_frame_equal(first.summary, second.summary)
    pd.testing.assert_frame_equal(first.keywords, second.keywords)
    np.testing.assert_array_equal(
        first.presentation_labels,
        second.presentation_labels,
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
