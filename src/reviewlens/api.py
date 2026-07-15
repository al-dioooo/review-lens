from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime
from importlib.metadata import version as distribution_version
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from reviewlens.analysis.clustering import cluster_features
from reviewlens.analysis.interpretation import interpret_clusters
from reviewlens.analysis.projection import project_features
from reviewlens.analysis.vectorizer import vectorize_reviews
from reviewlens.config import AnalysisConfig
from reviewlens.exceptions import ConfigurationError
from reviewlens.ingestion import load_dataset
from reviewlens.models import AnalysisResult, Diagnostic
from reviewlens.preprocessing import preprocess_reviews

_DEPENDENCY_DISTRIBUTIONS = {
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "openpyxl": "openpyxl",
    "pandas": "pandas",
    "pillow": "Pillow",
    "sastrawi": "Sastrawi",
    "scikit-learn": "scikit-learn",
    "scipy": "scipy",
}


def _effective_config(
    config: AnalysisConfig | None,
    language: Literal["id"] | None,
    clusters: int | Literal["auto"] | None,
) -> AnalysisConfig:
    effective = config or AnalysisConfig()
    if language is not None:
        if language != "id":
            raise ConfigurationError("v0.1.0 supports language='id' only.")
        effective = replace(effective, language=language)
    if clusters is not None:
        effective = replace(
            effective,
            clustering=replace(effective.clustering, clusters=clusters),
        )
    if effective.language != "id":
        raise ConfigurationError("v0.1.0 supports language='id' only.")
    if effective.vectorizer.ngram_range[0] < 1:
        raise ConfigurationError("ngram_range minimum must be at least 1.")
    if effective.vectorizer.ngram_range[0] > effective.vectorizer.ngram_range[1]:
        raise ConfigurationError("ngram_range minimum cannot exceed maximum.")
    if effective.vectorizer.max_features < 1:
        raise ConfigurationError("max_features must be positive.")
    return effective


def _dependency_versions() -> dict[str, str]:
    return {
        name: distribution_version(distribution)
        for name, distribution in _DEPENDENCY_DISTRIBUTIONS.items()
    }


def _merge_reviews(
    all_reviews: pd.DataFrame,
    included_reviews: pd.DataFrame,
) -> pd.DataFrame:
    assignments = included_reviews.loc[:, ["source_row", "cluster_id"]]
    reviews = all_reviews.merge(
        assignments,
        how="left",
        on="source_row",
        sort=False,
        validate="one_to_one",
    )
    reviews["cluster_id"] = reviews["cluster_id"].astype("Int64")
    return reviews


def _diagnostic_counts(diagnostics: tuple[Diagnostic, ...]) -> dict[str, int]:
    return {
        "total": len(diagnostics),
        "info": sum(item.severity == "info" for item in diagnostics),
        "warning": sum(item.severity == "warning" for item in diagnostics),
    }


def analyze_reviews(
    file: str | Path,
    *,
    language: Literal["id"] | None = None,
    clusters: int | Literal["auto"] | None = None,
    text_column: str | None = None,
    rating_column: str | None = None,
    config: AnalysisConfig | None = None,
) -> AnalysisResult:
    """Analyze one supported review dataset without writing output files."""
    effective = _effective_config(config, language, clusters)
    loaded = load_dataset(
        file,
        config=effective.ingestion,
        text_column=text_column,
        rating_column=rating_column,
    )
    preprocessing = preprocess_reviews(loaded.frame, effective.preprocessing)
    vectorization = vectorize_reviews(
        preprocessing.modeling_frame,
        effective.vectorizer,
    )
    clustering = cluster_features(vectorization.matrix, effective.clustering)
    interpretation = interpret_clusters(
        preprocessing.modeling_frame,
        vectorization,
        clustering,
        effective.interpretation,
    )
    projection = project_features(
        vectorization.matrix,
        interpretation.presentation_labels,
        interpretation.reviews["source_row"].to_numpy(dtype=np.int_),
        effective.projection,
    )

    reviews = _merge_reviews(preprocessing.frame, interpretation.reviews)
    cluster_distribution = (
        interpretation.reviews["cluster_id"]
        .value_counts()
        .sort_index()
        .rename_axis("cluster_id")
        .reset_index(name="review_count")
    )
    valid_ratings = reviews.loc[reviews["rating"].notna(), ["source_row", "rating"]]
    visual_data = {
        "cluster_distribution": cluster_distribution,
        "rating_distribution": valid_ratings.reset_index(drop=True),
        "keywords": interpretation.keywords.copy(),
        "projection": projection.data.copy(),
        "evaluation": clustering.evaluation.copy(),
    }

    diagnostics = (
        loaded.diagnostics + preprocessing.diagnostics + projection.diagnostics
    )
    if valid_ratings.empty:
        diagnostics += (
            Diagnostic(
                severity="info",
                code="rating_unavailable",
                message=(
                    "No valid ratings were available; rating-dependent insights "
                    "were omitted."
                ),
            ),
        )

    metadata: dict[str, object] = {
        "reviewlens_version": distribution_version("reviewlens"),
        "dependency_versions": _dependency_versions(),
        "config": asdict(effective),
        "source_name": loaded.source_path.name,
        "source_sha256": loaded.source_sha256,
        "generated_at": datetime.now(UTC).isoformat(),
        "input_count": len(preprocessing.frame),
        "retained_count": len(preprocessing.modeling_frame),
        "excluded_count": len(preprocessing.frame) - len(preprocessing.modeling_frame),
        "selected_k": clustering.selected_k,
        "diagnostic_counts": _diagnostic_counts(diagnostics),
    }
    return AnalysisResult(
        reviews=reviews,
        clusters=interpretation.clusters,
        summary=interpretation.summary,
        keywords=interpretation.keywords,
        evaluation=clustering.evaluation,
        visual_data=visual_data,
        metadata=metadata,
        diagnostics=diagnostics,
        source_stem=loaded.source_stem,
    )
