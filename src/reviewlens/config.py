from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

ClusterCount: TypeAlias = int | Literal["auto"]


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
