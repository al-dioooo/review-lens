from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from reviewlens.models import AnalysisResult

_FIGURE_SIZE = (8.0, 5.0)
_PNG_METADATA = {"Software": "ReviewLens"}


@dataclass(frozen=True, slots=True)
class ChartArtifact:
    name: str
    path: Path
    title: str


@contextmanager
def _figure() -> Iterator[tuple[Figure, Axes]]:
    figure, axis = plt.subplots(figsize=_FIGURE_SIZE)
    try:
        yield figure, axis
    finally:
        plt.close(figure)


def _save(
    figure: Figure,
    output_dir: Path,
    name: str,
    title: str,
) -> ChartArtifact:
    path = output_dir / f"{name}.png"
    try:
        figure.savefig(
            path,
            dpi=160,
            bbox_inches="tight",
            metadata=_PNG_METADATA,
        )
    finally:
        plt.close(figure)
    return ChartArtifact(name=name, path=path, title=title)


def _cluster_distribution(
    result: AnalysisResult,
    output_dir: Path,
) -> ChartArtifact:
    distribution = result.visual_data["cluster_distribution"].sort_values("cluster_id")
    selected_k = result.metadata.get("selected_k", len(distribution))
    title = f"Cluster Distribution (k={selected_k})"
    cluster_ids = distribution["cluster_id"].astype(int).tolist()
    with _figure() as (figure, axis):
        axis.bar(
            cluster_ids,
            distribution["review_count"].astype(int).tolist(),
            color="#4C78A8",
        )
        axis.set_title(title)
        axis.set_xlabel("Cluster")
        axis.set_ylabel("Review Count")
        axis.set_xticks(cluster_ids)
        return _save(figure, output_dir, "cluster_distribution", title)


def _rating_distribution(
    ratings: pd.DataFrame,
    output_dir: Path,
) -> ChartArtifact:
    title = "Rating Distribution"
    with _figure() as (figure, axis):
        axis.hist(
            ratings["rating"].astype(float).tolist(),
            bins=(0.5, 1.5, 2.5, 3.5, 4.5, 5.5),
            color="#F58518",
            edgecolor="white",
        )
        axis.set_title(title)
        axis.set_xlabel("Rating")
        axis.set_ylabel("Review Count")
        axis.set_xticks(range(1, 6))
        return _save(figure, output_dir, "rating_distribution", title)


def _cluster_keywords(
    result: AnalysisResult,
    output_dir: Path,
    cluster_id: int,
) -> ChartArtifact:
    keywords = result.visual_data["keywords"]
    ranked = keywords.loc[keywords["cluster_id"] == cluster_id].sort_values(
        ["rank", "term"],
        ascending=[False, True],
    )
    cluster = result.clusters.loc[result.clusters["cluster_id"] == cluster_id].iloc[0]
    title = f"Top Keywords for Cluster {cluster_id}: {cluster['theme']}"
    name = f"cluster_keywords_{cluster_id}"
    palette = matplotlib.colormaps["tab10"]
    with _figure() as (figure, axis):
        axis.barh(
            ranked["term"].astype(str).tolist(),
            ranked["score"].astype(float).tolist(),
            color=palette(cluster_id % 10),
        )
        axis.set_title(title)
        axis.set_xlabel("Mean TF-IDF Score")
        axis.set_ylabel("Keyword")
        return _save(figure, output_dir, name, title)


def _cluster_projection(
    result: AnalysisResult,
    output_dir: Path,
) -> ChartArtifact:
    projection = result.visual_data["projection"]
    selected_k = result.metadata.get(
        "selected_k",
        projection["cluster_id"].nunique(),
    )
    title = f"Cluster Projection (k={selected_k})"
    palette = matplotlib.colormaps["tab10"]
    cluster_ids = sorted(int(value) for value in projection["cluster_id"].unique())
    with _figure() as (figure, axis):
        for cluster_id in cluster_ids:
            points = projection.loc[projection["cluster_id"] == cluster_id].sort_values(
                "source_row"
            )
            axis.scatter(
                points["x"].astype(float).tolist(),
                points["y"].astype(float).tolist(),
                color=palette(cluster_id % 10),
                label=f"Cluster {cluster_id}",
                s=36,
                alpha=0.85,
            )
        axis.set_title(title)
        axis.set_xlabel("Projection Dimension 1")
        axis.set_ylabel("Projection Dimension 2")
        axis.legend(title="Cluster")
        return _save(figure, output_dir, "cluster_projection", title)


def _evaluation_chart(
    evaluation: pd.DataFrame,
    output_dir: Path,
    *,
    metric: str,
    name: str,
    title: str,
    ylabel: str,
) -> ChartArtifact:
    with _figure() as (figure, axis):
        axis.plot(
            evaluation["k"].astype(int).tolist(),
            evaluation[metric].astype(float).tolist(),
            marker="o",
            color="#4C78A8",
        )
        axis.set_title(title)
        axis.set_xlabel("Number of Clusters (k)")
        axis.set_ylabel(ylabel)
        axis.set_xticks(evaluation["k"].astype(int).tolist())
        return _save(figure, output_dir, name, title)


def generate_charts(
    result: AnalysisResult,
    output_dir: Path,
) -> tuple[ChartArtifact, ...]:
    """Generate an ordered set of deterministic PNGs in ``output_dir``."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = [_cluster_distribution(result, output_dir)]

    ratings = result.visual_data["rating_distribution"]
    if not ratings.empty:
        artifacts.append(_rating_distribution(ratings, output_dir))

    cluster_ids = sorted(int(value) for value in result.clusters["cluster_id"])
    artifacts.extend(
        _cluster_keywords(result, output_dir, cluster_id) for cluster_id in cluster_ids
    )
    artifacts.append(_cluster_projection(result, output_dir))

    evaluation = result.visual_data["evaluation"]
    valid_evaluation = evaluation.loc[evaluation["valid"].eq(True)].sort_values("k")
    if not valid_evaluation.empty:
        artifacts.append(
            _evaluation_chart(
                valid_evaluation,
                output_dir,
                metric="inertia",
                name="inertia_by_k",
                title="Inertia by Number of Clusters",
                ylabel="Inertia",
            )
        )
        artifacts.append(
            _evaluation_chart(
                valid_evaluation,
                output_dir,
                metric="silhouette",
                name="silhouette_by_k",
                title="Silhouette Score by Number of Clusters",
                ylabel="Silhouette Score",
            )
        )
    return tuple(artifacts)


__all__ = ["ChartArtifact", "generate_charts"]
