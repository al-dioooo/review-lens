from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from reviewlens.exceptions import ConfigurationError

ClusterCount: TypeAlias = int | Literal["auto"]
_MAX_RANDOM_STATE = 2**32 - 1


@dataclass(frozen=True, slots=True)
class IngestionConfig:
    records_key: str | None = None
    csv_delimiter: str | None = None


@dataclass(frozen=True, slots=True)
class PreprocessingConfig:
    normalize_slang: bool = True
    remove_stopwords: bool = True
    stem: bool = False
    protected_negations: tuple[str, ...] = (
        "tidak",
        "tak",
        "bukan",
        "belum",
        "jangan",
        "gak",
        "nggak",
        "enggak",
    )
    extra_slang: tuple[tuple[str, str], ...] = ()
    extra_stopwords: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VectorizerConfig:
    ngram_range: tuple[int, int] = (1, 2)
    min_df: int = 1
    max_df: float = 1.0
    max_features: int = 50_000
    sublinear_tf: bool = True


@dataclass(frozen=True, slots=True)
class ClusteringConfig:
    clusters: ClusterCount = "auto"
    random_state: int = 42
    n_init: int = 20
    max_iter: int = 300
    k_max: int = 10
    silhouette_sample_size: int = 5_000
    evaluate_manual: bool = False


@dataclass(frozen=True, slots=True)
class InterpretationConfig:
    keyword_count: int = 10
    representative_count: int = 3


@dataclass(frozen=True, slots=True)
class ProjectionConfig:
    components: int = 2
    sample_size: int = 10_000
    random_state: int = 42


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    language: Literal["id"] = "id"
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    vectorizer: VectorizerConfig = field(default_factory=VectorizerConfig)
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)
    interpretation: InterpretationConfig = field(default_factory=InterpretationConfig)
    projection: ProjectionConfig = field(default_factory=ProjectionConfig)


def _require_bool(value: object, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ConfigurationError(f"{field_name} must be a boolean.")


def _require_int(
    value: object,
    field_name: str,
    *,
    minimum: int,
    maximum: int | None = None,
) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigurationError(f"{field_name} must be an integer.")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            raise ConfigurationError(f"{field_name} must be at least {minimum}.")
        raise ConfigurationError(
            f"{field_name} must be between {minimum} and {maximum}."
        )


def _is_token(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.isalnum()


def _require_token_tuple(value: object, field_name: str) -> None:
    if not isinstance(value, tuple) or not all(_is_token(item) for item in value):
        raise ConfigurationError(
            f"{field_name} must be a tuple of non-empty single tokens."
        )


def _validate_ingestion(config: IngestionConfig) -> None:
    records_key = config.records_key
    if records_key is not None and (
        not isinstance(records_key, str) or not records_key.strip()
    ):
        raise ConfigurationError("records_key must be a non-empty string or None.")
    delimiter = config.csv_delimiter
    if delimiter is not None and (
        not isinstance(delimiter, str)
        or len(delimiter) != 1
        or delimiter in {"\0", "\r", "\n"}
    ):
        raise ConfigurationError(
            "csv_delimiter must be exactly one non-newline character or None."
        )


def _validate_preprocessing(config: PreprocessingConfig) -> None:
    _require_bool(config.normalize_slang, "normalize_slang")
    _require_bool(config.remove_stopwords, "remove_stopwords")
    _require_bool(config.stem, "stem")
    _require_token_tuple(config.protected_negations, "protected_negations")
    _require_token_tuple(config.extra_stopwords, "extra_stopwords")
    if not isinstance(config.extra_slang, tuple):
        raise ConfigurationError(
            "extra_slang must be a tuple of two-token string pairs."
        )
    for pair in config.extra_slang:
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or not _is_token(pair[0])
            or not _is_token(pair[1])
        ):
            raise ConfigurationError(
                "extra_slang must be a tuple of two-token string pairs."
            )


def _validate_vectorizer(config: VectorizerConfig) -> None:
    ngram_range = config.ngram_range
    if (
        not isinstance(ngram_range, tuple)
        or len(ngram_range) != 2
        or any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in ngram_range
        )
    ):
        raise ConfigurationError("ngram_range must be a two-item tuple of integers.")
    if ngram_range[0] < 1:
        raise ConfigurationError("ngram_range minimum must be at least 1.")
    if ngram_range[0] > ngram_range[1]:
        raise ConfigurationError("ngram_range minimum cannot exceed maximum.")
    _require_int(config.min_df, "min_df", minimum=1)
    if not isinstance(config.max_df, float) or not 0.0 < config.max_df <= 1.0:
        raise ConfigurationError("max_df must be a float in the range (0.0, 1.0].")
    if (
        not isinstance(config.max_features, int)
        or isinstance(config.max_features, bool)
        or config.max_features < 1
    ):
        raise ConfigurationError("max_features must be positive.")
    _require_bool(config.sublinear_tf, "sublinear_tf")


def _validate_clustering(config: ClusteringConfig) -> None:
    clusters = config.clusters
    valid_auto = isinstance(clusters, str) and clusters == "auto"
    valid_manual = (
        isinstance(clusters, int) and not isinstance(clusters, bool) and clusters >= 2
    )
    if not valid_auto and not valid_manual:
        raise ConfigurationError("clusters must be 'auto' or an integer at least 2.")
    _require_int(
        config.random_state,
        "clustering.random_state",
        minimum=0,
        maximum=_MAX_RANDOM_STATE,
    )
    _require_int(config.n_init, "n_init", minimum=1)
    _require_int(config.max_iter, "max_iter", minimum=1)
    _require_int(config.k_max, "k_max", minimum=2)
    _require_int(
        config.silhouette_sample_size,
        "silhouette_sample_size",
        minimum=2,
    )
    _require_bool(config.evaluate_manual, "evaluate_manual")


def _validate_interpretation(config: InterpretationConfig) -> None:
    _require_int(config.keyword_count, "keyword_count", minimum=1)
    _require_int(config.representative_count, "representative_count", minimum=1)


def _validate_projection(config: ProjectionConfig) -> None:
    _require_int(config.components, "components", minimum=1)
    _require_int(config.sample_size, "sample_size", minimum=1)
    _require_int(
        config.random_state,
        "projection.random_state",
        minimum=0,
        maximum=_MAX_RANDOM_STATE,
    )


def validate_analysis_config(config: object) -> None:
    """Validate every public configuration field before analysis starts."""
    if not isinstance(config, AnalysisConfig):
        raise ConfigurationError("config must be an AnalysisConfig instance.")
    if not isinstance(config.language, str) or config.language != "id":
        raise ConfigurationError("v0.1.0 supports language='id' only.")
    sections = (
        ("ingestion", config.ingestion, IngestionConfig),
        ("preprocessing", config.preprocessing, PreprocessingConfig),
        ("vectorizer", config.vectorizer, VectorizerConfig),
        ("clustering", config.clustering, ClusteringConfig),
        ("interpretation", config.interpretation, InterpretationConfig),
        ("projection", config.projection, ProjectionConfig),
    )
    for name, section, expected_type in sections:
        if not isinstance(section, expected_type):
            raise ConfigurationError(
                f"{name} must be a {expected_type.__name__} instance."
            )
    _validate_ingestion(config.ingestion)
    _validate_preprocessing(config.preprocessing)
    _validate_vectorizer(config.vectorizer)
    _validate_clustering(config.clustering)
    _validate_interpretation(config.interpretation)
    _validate_projection(config.projection)
