import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pandas as pd
import pytest

from reviewlens import analyze_reviews
from reviewlens.export.charts import ChartArtifact, generate_charts


def _source(tmp_path: Path, with_rating: bool = True) -> Path:
    path = tmp_path / "reviews.csv"
    header = "text,rating\n" if with_rating else "text\n"
    rows = [
        "pelayanan lambat antre,2\n" if with_rating else "pelayanan lambat antre\n",
        "antre lama pelayanan,1\n" if with_rating else "antre lama pelayanan\n",
        "petugas lambat antre,2\n" if with_rating else "petugas lambat antre\n",
        "tempat bersih nyaman,5\n" if with_rating else "tempat bersih nyaman\n",
        "bersih rapi nyaman,4\n" if with_rating else "bersih rapi nyaman\n",
        "lokasi nyaman bersih,5\n" if with_rating else "lokasi nyaman bersih\n",
    ]
    path.write_text(header + "".join(rows), encoding="utf-8")
    return path


def test_chart_set_is_ordered_and_complete(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    artifacts = generate_charts(result, tmp_path / "charts")
    names = [artifact.name for artifact in artifacts]
    assert names[0:2] == ["cluster_distribution", "rating_distribution"]
    assert "cluster_projection" in names
    assert names.count("cluster_keywords_0") == 1
    assert names.count("cluster_keywords_1") == 1
    assert all(artifact.path.is_file() for artifact in artifacts)
    assert all(artifact.path.stat().st_size > 0 for artifact in artifacts)
    assert all(
        artifact.path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        for artifact in artifacts
    )
    assert all(re.fullmatch(r"[A-Za-z0-9_]+", artifact.name) for artifact in artifacts)
    assert all(artifact.title for artifact in artifacts)


def test_rating_chart_is_omitted_without_ratings(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path, with_rating=False), clusters=2)
    artifacts = generate_charts(result, tmp_path / "charts")
    assert "rating_distribution" not in [artifact.name for artifact in artifacts]


def test_valid_evaluation_charts_follow_projection(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    result.visual_data["evaluation"] = pd.DataFrame(
        {
            "k": [2, 3, 4],
            "inertia": [12.0, 8.0, 999.0],
            "silhouette": [0.3, 0.6, 999.0],
            "valid": [True, True, False],
            "reason": [None, None, "invalid"],
        }
    )
    artifacts = generate_charts(result, tmp_path / "charts")
    assert [artifact.name for artifact in artifacts][-3:] == [
        "cluster_projection",
        "inertia_by_k",
        "silhouette_by_k",
    ]


def test_evaluation_charts_are_omitted_without_valid_rows(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    result.visual_data["evaluation"] = pd.DataFrame(
        {
            "k": [2],
            "inertia": [12.0],
            "silhouette": [0.3],
            "valid": [False],
            "reason": ["invalid"],
        }
    )
    names = [artifact.name for artifact in generate_charts(result, tmp_path / "charts")]
    assert "inertia_by_k" not in names
    assert "silhouette_by_k" not in names


def test_pngs_are_deterministic_and_figures_are_closed(tmp_path: Path) -> None:
    from matplotlib import pyplot as plt

    result = analyze_reviews(_source(tmp_path), clusters=2)
    figures_before = tuple(plt.get_fignums())
    first = generate_charts(result, tmp_path / "first")
    second = generate_charts(result, tmp_path / "second")
    assert [artifact.name for artifact in first] == [
        artifact.name for artifact in second
    ]
    assert [artifact.path.read_bytes() for artifact in first] == [
        artifact.path.read_bytes() for artifact in second
    ]
    assert tuple(plt.get_fignums()) == figures_before


def test_chart_artifact_is_immutable(tmp_path: Path) -> None:
    artifact = ChartArtifact("chart", tmp_path / "chart.png", "Chart")
    with pytest.raises(FrozenInstanceError):
        artifact.title = "Changed"  # type: ignore[misc]
