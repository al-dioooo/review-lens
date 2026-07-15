from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from reviewlens import (
    AnalysisConfig,
    AnalysisResult,
    ExportManifest,
    analyze_reviews,
)
from reviewlens.config import (
    ClusteringConfig,
    ProjectionConfig,
    VectorizerConfig,
)
from reviewlens.exceptions import ConfigurationError


def _write_reviews(path: Path) -> None:
    path.write_text(
        "text,rating\n"
        "pelayanan lambat antre,2\n"
        "antre lama pelayanan,1\n"
        "petugas lambat antre,2\n"
        "tempat bersih nyaman,5\n"
        "bersih rapi nyaman,4\n"
        "lokasi nyaman bersih,5\n",
        encoding="utf-8",
    )


def test_api_returns_analysis_without_writing(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    before = set(tmp_path.iterdir())
    result = analyze_reviews(source, clusters=2)
    after = set(tmp_path.iterdir())
    assert isinstance(result, AnalysisResult)
    assert before == after
    assert result.metadata["selected_k"] == 2
    assert result.metadata["source_name"] == "reviews.csv"
    assert result.reviews["cluster_id"].notna().all()
    assert set(result.visual_data) == {
        "cluster_distribution",
        "rating_distribution",
        "keywords",
        "projection",
        "evaluation",
    }


def test_convenience_arguments_override_config(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    supplied = AnalysisConfig(clustering=ClusteringConfig(clusters=3))
    result = analyze_reviews(source, clusters=2, config=supplied)
    assert result.metadata["selected_k"] == 2
    effective = result.metadata["config"]
    assert isinstance(effective, dict)
    assert effective["clustering"]["clusters"] == 2
    assert supplied.clustering.clusters == 3


def test_config_is_used_when_convenience_argument_is_absent(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    config = AnalysisConfig(clustering=ClusteringConfig(clusters=2))
    result = analyze_reviews(source, config=config)
    assert result.metadata["selected_k"] == 2


def test_non_indonesian_language_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    with pytest.raises(ConfigurationError, match="language"):
        analyze_reviews(source, language="en")  # type: ignore[arg-type]


def test_non_indonesian_language_in_config_is_rejected(tmp_path: Path) -> None:
    config = AnalysisConfig(language="en")  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError, match="language"):
        analyze_reviews(tmp_path / "missing.csv", config=config)


@pytest.mark.parametrize(
    ("vectorizer", "message"),
    [
        (VectorizerConfig(ngram_range=(0, 1)), "minimum must be at least 1"),
        (VectorizerConfig(ngram_range=(2, 1)), "minimum cannot exceed maximum"),
        (VectorizerConfig(max_features=0), "max_features must be positive"),
    ],
)
def test_invalid_vectorizer_configuration_is_rejected_before_loading(
    tmp_path: Path,
    vectorizer: VectorizerConfig,
    message: str,
) -> None:
    config = AnalysisConfig(vectorizer=vectorizer)
    with pytest.raises(ConfigurationError, match=message):
        analyze_reviews(tmp_path / "missing.csv", config=config)


def test_result_and_manifest_are_immutable_at_the_top_level(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    result = analyze_reviews(source, clusters=2)
    manifest = ExportManifest(tmp_path / "report.xlsx", ())
    with pytest.raises(FrozenInstanceError):
        result.source_stem = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        manifest.workbook_path = tmp_path / "changed.xlsx"  # type: ignore[misc]


def test_all_rows_are_preserved_with_nullable_cluster_ids(tmp_path: Path) -> None:
    source = tmp_path / "all-rows.csv"
    source.write_text(
        "text,rating,reference\n"
        "pelayanan lambat antre,2,a\n"
        "antre lama pelayanan,1,b\n"
        "petugas lambat antre,2,c\n"
        "!!!,3,excluded\n"
        "tempat bersih nyaman,5,d\n"
        "bersih rapi nyaman,4,e\n"
        "lokasi nyaman bersih,5,f\n",
        encoding="utf-8",
    )
    result = analyze_reviews(source, clusters=2)
    assert result.reviews["source_row"].tolist() == list(range(1, 8))
    assert result.reviews["reference"].tolist()[3] == "excluded"
    assert result.reviews["included"].tolist() == [
        True,
        True,
        True,
        False,
        True,
        True,
        True,
    ]
    assert result.reviews["cluster_id"].dtype == pd.Int64Dtype()
    assert pd.isna(result.reviews.loc[3, "cluster_id"])
    assert result.reviews.loc[result.reviews["included"], "cluster_id"].notna().all()
    assert result.reviews.loc[3, "drop_reason"] == "blank_review"
    assert result.metadata["input_count"] == 7
    assert result.metadata["retained_count"] == 6
    assert result.metadata["excluded_count"] == 1


def test_metadata_records_reproducibility_inputs_without_source_path(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    result = analyze_reviews(source, clusters=2)
    metadata = result.metadata
    generated_at = datetime.fromisoformat(str(metadata["generated_at"]))
    assert generated_at.utcoffset() == timedelta(0)
    assert metadata["reviewlens_version"] == "0.1.0"
    dependency_versions = metadata["dependency_versions"]
    assert isinstance(dependency_versions, dict)
    assert {
        "matplotlib",
        "numpy",
        "openpyxl",
        "pandas",
        "pillow",
        "sastrawi",
        "scikit-learn",
        "scipy",
    } <= dependency_versions.keys()
    assert all(isinstance(value, str) for value in dependency_versions.values())
    assert metadata["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert metadata["input_count"] == 6
    assert metadata["retained_count"] == 6
    assert metadata["excluded_count"] == 0
    assert metadata["diagnostic_counts"] == {
        "total": 0,
        "info": 0,
        "warning": 0,
    }
    assert "source_path" not in metadata
    assert str(source.resolve()) not in repr(metadata)
    assert result.source_stem == "reviews"


def test_diagnostics_are_aggregated_in_stage_order(tmp_path: Path) -> None:
    source = tmp_path / "diagnostics.csv"
    source.write_text(
        "text,rating\n"
        "pelayanan lambat antre,bad\n"
        "antre lama pelayanan,bad\n"
        "petugas lambat antre,bad\n"
        "!!!,bad\n"
        "tempat bersih nyaman,bad\n"
        "bersih rapi nyaman,bad\n"
        "lokasi nyaman bersih,bad\n",
        encoding="utf-8",
    )
    config = AnalysisConfig(projection=ProjectionConfig(sample_size=1))
    result = analyze_reviews(source, clusters=2, config=config)
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "invalid_rating",
        "blank_review_excluded",
        "one_dimensional_projection",
        "rating_unavailable",
    ]
    assert [diagnostic.severity for diagnostic in result.diagnostics] == [
        "warning",
        "warning",
        "warning",
        "info",
    ]
    assert result.visual_data["rating_distribution"].empty
    assert result.metadata["diagnostic_counts"] == {
        "total": 4,
        "info": 1,
        "warning": 3,
    }


def test_visual_tables_have_stable_schemas_and_are_copied(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    result = analyze_reviews(source, clusters=2)
    distribution = result.visual_data["cluster_distribution"]
    assert distribution.columns.tolist() == ["cluster_id", "review_count"]
    assert distribution["review_count"].sum() == 6
    assert result.visual_data["rating_distribution"].columns.tolist() == [
        "source_row",
        "rating",
    ]
    assert result.visual_data["keywords"].equals(result.keywords)
    assert result.visual_data["keywords"] is not result.keywords
    assert result.visual_data["evaluation"].equals(result.evaluation)
    assert result.visual_data["evaluation"] is not result.evaluation


def test_explicit_text_and_rating_columns_reach_ingestion(tmp_path: Path) -> None:
    source = tmp_path / "custom.csv"
    source.write_text(
        "body,grade\n"
        "pelayanan lambat antre,2\n"
        "antre lama pelayanan,1\n"
        "petugas lambat antre,2\n"
        "tempat bersih nyaman,5\n"
        "bersih rapi nyaman,4\n"
        "lokasi nyaman bersih,5\n",
        encoding="utf-8",
    )
    result = analyze_reviews(
        source,
        clusters=2,
        text_column="body",
        rating_column="grade",
    )
    assert result.reviews["review_text"].iloc[0] == "pelayanan lambat antre"
    assert result.reviews["rating"].astype(float).tolist() == [
        2.0,
        1.0,
        2.0,
        5.0,
        4.0,
        5.0,
    ]
