from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
from importlib.metadata import version as distribution_version
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import ConvergenceWarning  # type: ignore[import-untyped]

import reviewlens
from reviewlens import (
    AnalysisConfig,
    AnalysisResult,
    ExportManifest,
    analyze_reviews,
)
from reviewlens.config import (
    ClusteringConfig,
    IngestionConfig,
    InterpretationConfig,
    PreprocessingConfig,
    ProjectionConfig,
    VectorizerConfig,
)
from reviewlens.exceptions import ConfigurationError, InputError


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


def test_convenience_arguments_can_repair_overridden_config_fields(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    supplied = AnalysisConfig(
        language=cast(Any, "en"),
        clustering=ClusteringConfig(clusters=1),
    )

    result = analyze_reviews(
        source,
        language="id",
        clusters=2,
        config=supplied,
    )

    effective = result.metadata["config"]
    assert isinstance(effective, dict)
    assert effective["language"] == "id"
    assert effective["clustering"]["clusters"] == 2


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


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (AnalysisConfig(language=cast(Any, 1)), "language"),
        (
            AnalysisConfig(ingestion=IngestionConfig(records_key="")),
            "records_key",
        ),
        (
            AnalysisConfig(ingestion=IngestionConfig(records_key=cast(Any, 1))),
            "records_key",
        ),
        (
            AnalysisConfig(ingestion=IngestionConfig(csv_delimiter="")),
            "csv_delimiter",
        ),
        (
            AnalysisConfig(ingestion=IngestionConfig(csv_delimiter="::")),
            "csv_delimiter",
        ),
        (
            AnalysisConfig(ingestion=IngestionConfig(csv_delimiter=cast(Any, 1))),
            "csv_delimiter",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(normalize_slang=cast(Any, 1))
            ),
            "normalize_slang",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(remove_stopwords=cast(Any, 1))
            ),
            "remove_stopwords",
        ),
        (
            AnalysisConfig(preprocessing=PreprocessingConfig(stem=cast(Any, 1))),
            "stem",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(
                    protected_negations=cast(Any, ["tidak"])
                )
            ),
            "protected_negations",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(protected_negations=("",))
            ),
            "protected_negations",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(protected_negations=("dua kata",))
            ),
            "protected_negations",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(
                    extra_slang=cast(Any, [("gk", "gak")])
                )
            ),
            "extra_slang",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(extra_slang=cast(Any, (("gk",),)))
            ),
            "extra_slang",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(extra_slang=(("gk", ""),))
            ),
            "extra_slang",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(extra_stopwords=cast(Any, ["dan"]))
            ),
            "extra_stopwords",
        ),
        (
            AnalysisConfig(
                preprocessing=PreprocessingConfig(extra_stopwords=("dua kata",))
            ),
            "extra_stopwords",
        ),
        (
            AnalysisConfig(vectorizer=VectorizerConfig(ngram_range=cast(Any, [1, 2]))),
            "ngram_range",
        ),
        (
            AnalysisConfig(vectorizer=VectorizerConfig(ngram_range=cast(Any, (1,)))),
            "ngram_range",
        ),
        (
            AnalysisConfig(
                vectorizer=VectorizerConfig(ngram_range=(cast(Any, True), 2))
            ),
            "ngram_range",
        ),
        (
            AnalysisConfig(vectorizer=VectorizerConfig(min_df=cast(Any, True))),
            "min_df",
        ),
        (AnalysisConfig(vectorizer=VectorizerConfig(min_df=0)), "min_df"),
        (
            AnalysisConfig(vectorizer=VectorizerConfig(max_df=cast(Any, "1.0"))),
            "max_df",
        ),
        (AnalysisConfig(vectorizer=VectorizerConfig(max_df=0.0)), "max_df"),
        (AnalysisConfig(vectorizer=VectorizerConfig(max_df=1.1)), "max_df"),
        (
            AnalysisConfig(vectorizer=VectorizerConfig(max_features=cast(Any, True))),
            "max_features",
        ),
        (
            AnalysisConfig(vectorizer=VectorizerConfig(sublinear_tf=cast(Any, 1))),
            "sublinear_tf",
        ),
        (
            AnalysisConfig(clustering=ClusteringConfig(clusters=cast(Any, "manual"))),
            "clusters",
        ),
        (
            AnalysisConfig(clustering=ClusteringConfig(clusters=cast(Any, True))),
            "clusters",
        ),
        (AnalysisConfig(clustering=ClusteringConfig(clusters=1)), "clusters"),
        (
            AnalysisConfig(clustering=ClusteringConfig(random_state=cast(Any, True))),
            "random_state",
        ),
        (
            AnalysisConfig(clustering=ClusteringConfig(random_state=-1)),
            "random_state",
        ),
        (
            AnalysisConfig(clustering=ClusteringConfig(random_state=2**32)),
            "random_state",
        ),
        (
            AnalysisConfig(clustering=ClusteringConfig(n_init=cast(Any, True))),
            "n_init",
        ),
        (AnalysisConfig(clustering=ClusteringConfig(n_init=0)), "n_init"),
        (
            AnalysisConfig(clustering=ClusteringConfig(max_iter=cast(Any, True))),
            "max_iter",
        ),
        (AnalysisConfig(clustering=ClusteringConfig(max_iter=0)), "max_iter"),
        (
            AnalysisConfig(clustering=ClusteringConfig(k_max=cast(Any, True))),
            "k_max",
        ),
        (AnalysisConfig(clustering=ClusteringConfig(k_max=1)), "k_max"),
        (
            AnalysisConfig(
                clustering=ClusteringConfig(silhouette_sample_size=cast(Any, True))
            ),
            "silhouette_sample_size",
        ),
        (
            AnalysisConfig(clustering=ClusteringConfig(silhouette_sample_size=1)),
            "silhouette_sample_size",
        ),
        (
            AnalysisConfig(clustering=ClusteringConfig(evaluate_manual=cast(Any, 1))),
            "evaluate_manual",
        ),
        (
            AnalysisConfig(
                interpretation=InterpretationConfig(keyword_count=cast(Any, True))
            ),
            "keyword_count",
        ),
        (
            AnalysisConfig(interpretation=InterpretationConfig(keyword_count=0)),
            "keyword_count",
        ),
        (
            AnalysisConfig(
                interpretation=InterpretationConfig(
                    representative_count=cast(Any, True)
                )
            ),
            "representative_count",
        ),
        (
            AnalysisConfig(interpretation=InterpretationConfig(representative_count=0)),
            "representative_count",
        ),
        (
            AnalysisConfig(projection=ProjectionConfig(components=cast(Any, True))),
            "components",
        ),
        (AnalysisConfig(projection=ProjectionConfig(components=0)), "components"),
        (
            AnalysisConfig(projection=ProjectionConfig(sample_size=cast(Any, True))),
            "sample_size",
        ),
        (AnalysisConfig(projection=ProjectionConfig(sample_size=0)), "sample_size"),
        (
            AnalysisConfig(projection=ProjectionConfig(random_state=cast(Any, True))),
            "random_state",
        ),
        (
            AnalysisConfig(projection=ProjectionConfig(random_state=-1)),
            "random_state",
        ),
        (
            AnalysisConfig(projection=ProjectionConfig(random_state=2**32)),
            "random_state",
        ),
    ],
)
def test_every_invalid_config_field_is_rejected_before_loading(
    tmp_path: Path,
    config: AnalysisConfig,
    message: str,
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        analyze_reviews(tmp_path / "missing.csv", config=config)


@pytest.mark.parametrize(
    ("config", "section"),
    [
        (AnalysisConfig(ingestion=cast(Any, "invalid")), "ingestion"),
        (AnalysisConfig(preprocessing=cast(Any, "invalid")), "preprocessing"),
        (AnalysisConfig(vectorizer=cast(Any, "invalid")), "vectorizer"),
        (AnalysisConfig(clustering=cast(Any, "invalid")), "clustering"),
        (AnalysisConfig(interpretation=cast(Any, "invalid")), "interpretation"),
        (AnalysisConfig(projection=cast(Any, "invalid")), "projection"),
    ],
)
def test_invalid_config_section_type_is_a_configuration_error(
    tmp_path: Path,
    config: AnalysisConfig,
    section: str,
) -> None:
    with pytest.raises(ConfigurationError, match=section):
        analyze_reviews(tmp_path / "missing.csv", config=config)


def test_invalid_root_config_type_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="AnalysisConfig"):
        analyze_reviews(tmp_path / "missing.csv", config=cast(Any, "invalid"))


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (AnalysisConfig(language=cast(Any, np.array(["id", "en"]))), "language"),
        (
            AnalysisConfig(clustering=ClusteringConfig(clusters=cast(Any, pd.NA))),
            "clusters",
        ),
    ],
)
def test_array_like_config_values_are_configuration_errors_before_loading(
    tmp_path: Path,
    config: AnalysisConfig,
    message: str,
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        analyze_reviews(tmp_path / "missing.csv", config=config)


def test_structured_review_text_is_an_api_input_error(tmp_path: Path) -> None:
    source = tmp_path / "structured.json"
    source.write_text(
        json.dumps(
            [
                {"text": ["nested", "review"], "rating": 5},
                {"text": "pelayanan cepat", "rating": 5},
                {"text": "pelayanan lambat", "rating": 1},
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(InputError, match=r"(?i)review text.*scalar"):
        analyze_reviews(source, clusters=2)


def test_duplicate_heavy_api_analysis_emits_no_convergence_warning(
    tmp_path: Path,
) -> None:
    source = tmp_path / "duplicates.csv"
    source.write_text(
        "text,rating\n"
        "pelayanan lambat,1\n"
        "pelayanan lambat,1\n"
        "tempat bersih,5\n"
        "tempat bersih,5\n"
        "lokasi nyaman,4\n"
        "lokasi nyaman,4\n",
        encoding="utf-8",
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = analyze_reviews(source)

    selected_k = cast(int, result.metadata["selected_k"])
    assert 2 <= selected_k <= 3
    assert not any(item.category is ConvergenceWarning for item in caught)


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


def test_metadata_uses_distribution_identity_without_renaming_public_contract(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    expected_version = distribution_version("review-lens")

    result = reviewlens.analyze_reviews(source, clusters=2)

    assert reviewlens.__version__ == expected_version
    assert result.metadata["reviewlens_version"] == expected_version
    assert "review-lens_version" not in result.metadata


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
        "warning",
    ]
    assert result.visual_data["rating_distribution"].empty
    assert result.metadata["diagnostic_counts"] == {
        "total": 4,
        "info": 0,
        "warning": 4,
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
