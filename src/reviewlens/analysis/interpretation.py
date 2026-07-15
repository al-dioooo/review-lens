from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_distances  # type: ignore[import-untyped]

from reviewlens.analysis.clustering import ClusteringResult
from reviewlens.analysis.vectorizer import VectorizationResult
from reviewlens.config import InterpretationConfig


@dataclass(frozen=True, slots=True)
class InterpretationResult:
    reviews: pd.DataFrame
    clusters: pd.DataFrame
    summary: pd.DataFrame
    keywords: pd.DataFrame
    presentation_labels: NDArray[np.int_]


@dataclass(frozen=True, slots=True)
class _ClusterDraft:
    original_label: int
    review_count: int
    average_rating: float | None
    terms: tuple[str, ...]
    scores: tuple[float, ...]
    theme: str
    representative_reviews: tuple[str, ...]
    representative_source_rows: tuple[int, ...]


def rating_signal(average: float | None) -> str:
    if average is None or math.isnan(average):
        return "unknown"
    if average < 3.0:
        return "complaint"
    if average < 4.0:
        return "mixed"
    return "positive"


def cluster_summary_text(
    cluster_id: int,
    count: int,
    share: float,
    average: float | None,
    terms: list[str],
) -> str:
    term_text = ", ".join(terms[:3])
    if average is None or math.isnan(average):
        return (
            f"Cluster {cluster_id} mencakup {count} ulasan ({share:.1%}). "
            f"Tema utama: {term_text}."
        )
    return (
        f"Cluster {cluster_id} mencakup {count} ulasan ({share:.1%}) "
        f"dengan rata-rata rating {average:.2f}/5. "
        f"Tema utama: {term_text}."
    )


def _average_rating(ratings: pd.Series) -> float | None:
    available = ratings.dropna()
    if available.empty:
        return None
    return float(available.astype(float).mean())


def _ranked_terms(
    vectorization: VectorizationResult,
    positions: list[int],
    keyword_count: int,
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    mean_weights = np.asarray(
        vectorization.matrix[positions].mean(axis=0),
        dtype=float,
    ).ravel()
    feature_names = vectorization.vectorizer.get_feature_names_out()
    ranked = sorted(
        (
            (str(feature_names[index]), float(score))
            for index, score in enumerate(mean_weights)
            if score > 0.0
        ),
        key=lambda item: (-item[1], item[0]),
    )[:keyword_count]
    return (
        tuple(term for term, _score in ranked),
        tuple(score for _term, score in ranked),
    )


def _representatives(
    modeling_frame: pd.DataFrame,
    vectorization: VectorizationResult,
    clustering: ClusteringResult,
    original_label: int,
    positions: list[int],
    representative_count: int,
) -> tuple[tuple[str, ...], tuple[int, ...]]:
    center = np.asarray(
        clustering.model.cluster_centers_[original_label],
        dtype=float,
    ).reshape(1, -1)
    distances = cosine_distances(
        vectorization.matrix[positions],
        center,
    ).ravel()
    ranked_positions = sorted(
        zip(positions, distances, strict=True),
        key=lambda item: (
            float(item[1]),
            int(modeling_frame.iloc[item[0]]["source_row"]),
        ),
    )[:representative_count]
    source_positions = [position for position, _distance in ranked_positions]
    return (
        tuple(
            str(modeling_frame.iloc[position]["review_text"])
            for position in source_positions
        ),
        tuple(
            int(modeling_frame.iloc[position]["source_row"])
            for position in source_positions
        ),
    )


def _cluster_drafts(
    modeling_frame: pd.DataFrame,
    vectorization: VectorizationResult,
    clustering: ClusteringResult,
    config: InterpretationConfig,
) -> list[_ClusterDraft]:
    drafts: list[_ClusterDraft] = []
    for original_label in sorted(int(label) for label in np.unique(clustering.labels)):
        positions = np.flatnonzero(clustering.labels == original_label).tolist()
        terms, scores = _ranked_terms(
            vectorization,
            positions,
            config.keyword_count,
        )
        representative_reviews, representative_source_rows = _representatives(
            modeling_frame,
            vectorization,
            clustering,
            original_label,
            positions,
            config.representative_count,
        )
        drafts.append(
            _ClusterDraft(
                original_label=original_label,
                review_count=len(positions),
                average_rating=_average_rating(
                    modeling_frame.iloc[positions]["rating"]
                ),
                terms=terms,
                scores=scores,
                theme=" · ".join(terms[:3]),
                representative_reviews=representative_reviews,
                representative_source_rows=representative_source_rows,
            )
        )
    return sorted(
        drafts,
        key=lambda draft: (
            -draft.review_count,
            draft.theme,
            draft.original_label,
        ),
    )


def _cluster_frames(
    drafts: list[_ClusterDraft],
    row_count: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cluster_rows: list[dict[str, object]] = []
    keyword_rows: list[dict[str, object]] = []
    for cluster_id, draft in enumerate(drafts):
        share = draft.review_count / row_count
        summary = cluster_summary_text(
            cluster_id,
            draft.review_count,
            share,
            draft.average_rating,
            list(draft.terms),
        )
        cluster_rows.append(
            {
                "cluster_id": cluster_id,
                "review_count": draft.review_count,
                "share": share,
                "average_rating": draft.average_rating,
                "rating_signal": rating_signal(draft.average_rating),
                "theme": draft.theme,
                "summary": summary,
                "keywords": draft.terms,
                "representative_reviews": draft.representative_reviews,
                "representative_source_rows": draft.representative_source_rows,
            }
        )
        keyword_rows.extend(
            {
                "cluster_id": cluster_id,
                "rank": rank,
                "term": term,
                "score": score,
            }
            for rank, (term, score) in enumerate(
                zip(draft.terms, draft.scores, strict=True),
                start=1,
            )
        )
    clusters = pd.DataFrame.from_records(
        cluster_rows,
        columns=[
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
        ],
    )
    keywords = pd.DataFrame.from_records(
        keyword_rows,
        columns=["cluster_id", "rank", "term", "score"],
    )
    return clusters, keywords


def _highlight_details(row: pd.Series, metric: str) -> str:
    cluster_id = int(row["cluster_id"])
    theme = str(row["theme"])
    if metric == "size":
        return (
            f"Cluster {cluster_id}: {theme} "
            f"({int(row['review_count'])} ulasan, {float(row['share']):.1%})."
        )
    return (
        f"Cluster {cluster_id}: {theme} "
        f"(rata-rata rating {float(row['average_rating']):.2f}/5)."
    )


def _dataset_summary(
    modeling_frame: pd.DataFrame,
    clustering: ClusteringResult,
    clusters: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = [
        {
            "category": "analysis",
            "name": "input-ready",
            "value": len(modeling_frame),
            "details": "Ulasan yang dipertahankan untuk analisis.",
        },
        {
            "category": "analysis",
            "name": "selected_k",
            "value": clustering.selected_k,
            "details": "Jumlah cluster yang digunakan.",
        },
    ]
    largest = clusters.iloc[0]
    rows.append(
        {
            "category": "highlight",
            "name": "largest_cluster",
            "value": int(largest["cluster_id"]),
            "details": _highlight_details(largest, "size"),
        }
    )
    available_ratings = modeling_frame["rating"].dropna()
    if available_ratings.empty:
        rows.append(
            {
                "category": "rating",
                "name": "rating_unavailable",
                "value": "unknown",
                "details": "Insight berbasis rating tidak tersedia.",
            }
        )
        return pd.DataFrame.from_records(
            rows,
            columns=["category", "name", "value", "details"],
        )

    rows.insert(
        2,
        {
            "category": "rating",
            "name": "overall_average_rating",
            "value": float(available_ratings.astype(float).mean()),
            "details": f"Rata-rata dari {len(available_ratings)} rating yang tersedia.",
        },
    )
    rated_clusters = clusters.loc[clusters["average_rating"].notna()]
    lowest = rated_clusters.sort_values(
        ["average_rating", "cluster_id"],
        ascending=[True, True],
    ).iloc[0]
    highest = rated_clusters.sort_values(
        ["average_rating", "cluster_id"],
        ascending=[False, True],
    ).iloc[0]
    rows.extend(
        [
            {
                "category": "highlight",
                "name": "lowest_rated_cluster",
                "value": int(lowest["cluster_id"]),
                "details": _highlight_details(lowest, "rating"),
            },
            {
                "category": "highlight",
                "name": "highest_rated_cluster",
                "value": int(highest["cluster_id"]),
                "details": _highlight_details(highest, "rating"),
            },
        ]
    )
    return pd.DataFrame.from_records(
        rows,
        columns=["category", "name", "value", "details"],
    )


def interpret_clusters(
    modeling_frame: pd.DataFrame,
    vectorization: VectorizationResult,
    clustering: ClusteringResult,
    config: InterpretationConfig,
) -> InterpretationResult:
    drafts = _cluster_drafts(
        modeling_frame,
        vectorization,
        clustering,
        config,
    )
    presentation_id_by_label = {
        draft.original_label: cluster_id for cluster_id, draft in enumerate(drafts)
    }
    presentation_labels = np.asarray(
        [presentation_id_by_label[int(label)] for label in clustering.labels],
        dtype=np.int_,
    )
    reviews = modeling_frame.copy()
    reviews["cluster_id"] = presentation_labels
    clusters, keywords = _cluster_frames(drafts, len(modeling_frame))
    summary = _dataset_summary(modeling_frame, clustering, clusters)
    return InterpretationResult(
        reviews=reviews,
        clusters=clusters,
        summary=summary,
        keywords=keywords,
        presentation_labels=presentation_labels,
    )
