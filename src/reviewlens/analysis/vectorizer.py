from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy.sparse import csr_matrix  # type: ignore[import-untyped]
from sklearn.feature_extraction.text import (  # type: ignore[import-untyped]
    TfidfVectorizer,
)

from reviewlens.config import VectorizerConfig
from reviewlens.exceptions import AnalysisError


@dataclass(frozen=True, slots=True)
class VectorizationResult:
    matrix: csr_matrix
    vectorizer: TfidfVectorizer


def _has_two_distinct_rows(matrix: csr_matrix) -> bool:
    first = matrix.getrow(0)
    return any(
        (matrix.getrow(index) != first).nnz for index in range(1, matrix.shape[0])
    )


def vectorize_reviews(
    modeling_frame: pd.DataFrame,
    config: VectorizerConfig,
) -> VectorizationResult:
    vectorizer = TfidfVectorizer(
        ngram_range=config.ngram_range,
        min_df=config.min_df,
        max_df=config.max_df,
        max_features=config.max_features,
        sublinear_tf=config.sublinear_tf,
    )
    try:
        fitted = vectorizer.fit_transform(modeling_frame["text_model"])
    except ValueError as error:
        raise AnalysisError(
            "TF-IDF produced an empty vocabulary; retain more words or lower "
            "vectorizer thresholds."
        ) from error
    matrix = csr_matrix(fitted)
    if matrix.shape[0] < 2 or not _has_two_distinct_rows(matrix):
        raise AnalysisError(
            "Review text must produce at least two distinguishable feature vectors."
        )
    return VectorizationResult(matrix=matrix, vectorizer=vectorizer)
