# ReviewLens v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build and verify the complete ReviewLens v0.1.0 Python library, CLI, deterministic Indonesian review-clustering pipeline, Excel/PNG reporting, tests, and open-source repository assets.

**Architecture:** A modular vertical slice under src/reviewlens shares one typed pipeline between the public Python API and argparse CLI. Stages exchange focused immutable configuration/result objects; analysis is side-effect free until AnalysisResult.export_excel explicitly invokes the atomic exporter.

**Tech Stack:** Python 3.11-3.14, uv and uv_build, pandas, NumPy, SciPy, scikit-learn, Sastrawi, matplotlib, openpyxl, Pillow, pytest/pytest-cov, Ruff, mypy, and GitHub Actions.

## Global Constraints

- Work only on branch production; do not configure a remote, push, publish, or mutate GitHub state.
- Implement from PRD.md and docs/superpowers/specs/2026-07-15-reviewlens-v0.1-design.md. Never copy or mechanically translate legacy source, data, output, credentials, names, or venue-specific behavior.
- Distribution, import package, and console command are all reviewlens; version is 0.1.0.
- License is Apache-2.0; copyright holder and maintainer are Aldio Lisafron (GitHub al-dioooo, lisafronaldio123@gmail.com).
- requires-python is >=3.11; CI covers CPython 3.11, 3.12, 3.13, and 3.14 on Linux plus Python 3.14 smoke tests on macOS and Windows.
- No scraping, Apify, dotenv, NLTK downloads, HTML, dashboard, external/local generative AI, plugins, MCP, or network behavior.
- Runtime input is CSV or JSON only; examples must be synthetic Indonesian reviews with no real person, business, URL, or copied review.
- Defaults are Indonesian-only processing, preserved negation, stemming off, sparse TF-IDF, K-Means seed 42, cosine-silhouette auto-k, and TruncatedSVD for visualization only.
- Analysis writes nothing. Only export writes, with formula-injection protection, 32,767-character cell limits, atomic staging, and overwrite refusal unless force is true.
- Workbook sheets are ordered metadata, reviews, clusters, summary, keywords, visual_data, visuals.
- Ruff, mypy, pytest, at least 90% line coverage, wheel/sdist build, isolated wheel install, and CLI smoke tests must all pass.
- Use test-driven development. Every behavior task starts with a focused failing test, observes the expected failure, implements the minimum complete behavior, verifies the focused test, then runs the affected suite.
- Use conventional commits with feat:, fix:, docs:, test:, refactor:, or chore: prefixes.

## Verified Tooling Basis

- uv_build is the official uv-native pure-Python build backend; use uv_build>=0.11.28,<0.12 and a src layout: https://docs.astral.sh/uv/concepts/build-backend/
- Current scientific packages publish Python 3.14 support, while current NumPy and SciPy releases require Python 3.12. Therefore runtime floors stay old enough for Python 3.11 and uv resolves newer wheels on newer interpreters:
  - numpy>=1.26.4
  - pandas>=2.2.3
  - scipy>=1.12.0
  - scikit-learn>=1.5.2
  - matplotlib>=3.9.2
  - openpyxl>=3.1.5
  - pillow>=10.4.0
  - Sastrawi>=1.0.1
- Sastrawi 1.0.1 is an old pure-Python distribution without modern Python metadata. Task 1 includes mandatory import/stemming smoke tests on the local Python and CI covers every supported interpreter: https://pypi.org/project/Sastrawi/
- GitHub Actions uses actions/checkout@v6 and astral-sh/setup-uv@v8; the official setup-uv examples support a Python matrix directly: https://github.com/astral-sh/setup-uv

## File Responsibility Map

| Path | Responsibility |
| --- | --- |
| pyproject.toml | Package metadata, dependencies, console script, build backend, lint/type/test/coverage configuration |
| src/reviewlens/config.py | Immutable user configuration and effective defaults |
| src/reviewlens/exceptions.py | Stable public exception hierarchy |
| src/reviewlens/models.py | Public Diagnostic, AnalysisResult, and ExportManifest models |
| src/reviewlens/ingestion/* | CSV/JSON parsing, hashing, column normalization, aliases, rating coercion |
| src/reviewlens/preprocessing/* | Unicode/basic cleaning, slang, protected stopwords, optional stemming |
| src/reviewlens/resources/slang_id.json | Newly authored Apache-licensed Indonesian slang map |
| src/reviewlens/analysis/vectorizer.py | Sparse TF-IDF feature construction |
| src/reviewlens/analysis/evaluation.py | Candidate-k fitting and silhouette/inertia records |
| src/reviewlens/analysis/clustering.py | Manual/automatic cluster selection and fitted model result |
| src/reviewlens/analysis/interpretation.py | Relabeling, keywords, themes, summaries, ratings, representative reviews |
| src/reviewlens/analysis/projection.py | Deterministically sampled two-dimensional chart coordinates |
| src/reviewlens/api.py | Side-effect-free end-to-end orchestration and metadata |
| src/reviewlens/export/safety.py | Formula escaping, JSON serialization, Excel cell-length enforcement |
| src/reviewlens/export/charts.py | Agg-backed deterministic PNG generation |
| src/reviewlens/export/excel.py | Seven-sheet workbook and atomic artifact installation |
| src/reviewlens/cli.py | argparse command, config translation, progress, exit-code mapping |
| examples/* | Equivalent synthetic CSV and JSON inputs |
| tests/unit/* | Focused stage contracts |
| tests/integration/* | API, CLI, workbook, package, and deterministic repeatability |
| docs/* and root policy files | User/developer documentation, governance, license, security, changelog |
| .github/workflows/ci.yml | Linux version matrix, cross-platform smoke tests, package gates |

## Interface Ledger

These names are fixed across tasks:

~~~python
# reviewlens.config
ClusterCount = int | Literal["auto"]
AnalysisConfig
IngestionConfig
PreprocessingConfig
VectorizerConfig
ClusteringConfig
InterpretationConfig
ProjectionConfig

# reviewlens.models
Diagnostic(severity, code, message, count=None)
AnalysisResult(
    reviews,
    clusters,
    summary,
    keywords,
    evaluation,
    visual_data,
    metadata,
    diagnostics,
    source_stem,
)
ExportManifest(workbook_path, chart_paths)

# stage results
LoadedDataset(frame, source_path, source_sha256, source_stem, diagnostics)
PreprocessingResult(frame, modeling_frame, diagnostics)
VectorizationResult(matrix, vectorizer)
ClusteringResult(model, labels, selected_k, evaluation)
InterpretationResult(reviews, clusters, summary, keywords, presentation_labels)
ProjectionResult(data, diagnostics)

# public calls
load_dataset(path, *, config, text_column=None, rating_column=None) -> LoadedDataset
preprocess_reviews(frame, config) -> PreprocessingResult
vectorize_reviews(modeling_frame, config) -> VectorizationResult
cluster_features(matrix, config) -> ClusteringResult
interpret_clusters(modeling_frame, vectorization, clustering, config) -> InterpretationResult
project_features(matrix, presentation_labels, source_rows, config) -> ProjectionResult
analyze_reviews(file, *, language=None, clusters=None, text_column=None, rating_column=None, config=None) -> AnalysisResult
export_analysis(result, path=None, *, force=False) -> ExportManifest
~~~

---

### Task 1: Package foundation, configuration, and public errors

**Files:**
- Create: pyproject.toml
- Create: .python-version
- Create: .gitignore
- Create: .editorconfig
- Create: README.md
- Create: src/reviewlens/__init__.py
- Create: src/reviewlens/config.py
- Create: src/reviewlens/exceptions.py
- Create: src/reviewlens/models.py
- Create: src/reviewlens/py.typed
- Create: tests/unit/test_config.py
- Create: tests/unit/test_exceptions.py

**Interfaces:**
- Consumes: the Global Constraints above.
- Produces: all immutable configuration dataclasses, Diagnostic, public exceptions, __version__="0.1.0", and a synchronized uv environment used by every later task.

- [ ] **Step 1: Add package/build/tool configuration**

Create pyproject.toml exactly with these sections; uv.lock is generated, never hand-edited:

~~~toml
[build-system]
requires = ["uv_build>=0.11.28,<0.12"]
build-backend = "uv_build"

[project]
name = "reviewlens"
version = "0.1.0"
description = "Deterministic Indonesian-first review clustering and reporting toolkit"
readme = "README.md"
requires-python = ">=3.11"
license = "Apache-2.0"
authors = [
  { name = "Aldio Lisafron", email = "lisafronaldio123@gmail.com" },
]
maintainers = [
  { name = "Aldio Lisafron", email = "lisafronaldio123@gmail.com" },
]
keywords = ["reviews", "nlp", "clustering", "indonesian", "k-means"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Developers",
  "Intended Audience :: Science/Research",
  "License :: OSI Approved :: Apache Software License",
  "Operating System :: OS Independent",
  "Programming Language :: Python :: 3 :: Only",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Programming Language :: Python :: 3.14",
  "Topic :: Scientific/Engineering :: Artificial Intelligence",
  "Typing :: Typed",
]
dependencies = [
  "matplotlib>=3.9.2",
  "numpy>=1.26.4",
  "openpyxl>=3.1.5",
  "pandas>=2.2.3",
  "pillow>=10.4.0",
  "Sastrawi>=1.0.1",
  "scikit-learn>=1.5.2",
  "scipy>=1.12.0",
]

[project.urls]
Homepage = "https://github.com/al-dioooo/review-lens"
Repository = "https://github.com/al-dioooo/review-lens"
Issues = "https://github.com/al-dioooo/review-lens/issues"
Changelog = "https://github.com/al-dioooo/review-lens/blob/production/CHANGELOG.md"

[project.scripts]
reviewlens = "reviewlens.cli:main"

[dependency-groups]
dev = [
  "mypy>=1.15.0",
  "pandas-stubs>=2.2.3",
  "pytest>=8.3.5",
  "pytest-cov>=6.0.0",
  "ruff>=0.11.0",
]

[tool.uv]
required-version = ">=0.11.8,<0.12"
default-groups = ["dev"]

[tool.ruff]
target-version = "py311"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I", "B", "UP", "RUF"]

[tool.mypy]
python_version = "3.11"
strict = true
files = ["src", "tests"]

[[tool.mypy.overrides]]
module = ["Sastrawi.*", "matplotlib.*", "openpyxl.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-ra", "--strict-config", "--strict-markers"]

[tool.coverage.run]
branch = true
source = ["reviewlens"]

[tool.coverage.report]
fail_under = 90
show_missing = true
skip_covered = true
~~~

Create .python-version containing 3.11. Create a real, non-placeholder README.md containing the title, one-sentence product description, Apache-2.0 notice, and a statement that full usage documentation lands with v0.1.0. Create .editorconfig with UTF-8, LF, final newline, four-space Python indentation, and two-space YAML indentation. Create .gitignore with:

~~~gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
build/
dist/
*.egg-info/
.DS_Store
.idea/
.vscode/
.env
.env.*
data/
dataset/
datasets/
output/
examples/output/
*.xlsx
*_charts/
~~~

- [ ] **Step 2: Resolve and synchronize dependencies**

Run:

~~~bash
uv lock
uv sync --all-groups --locked
~~~

Expected: uv.lock is created; ReviewLens installs editable; all runtime/dev dependencies resolve for requires-python >=3.11. If Sastrawi fails to build or import on the active interpreter, stop this task and report the exact compatibility failure because the approved spec requires it.

- [ ] **Step 3: Write failing configuration and exception tests**

Create tests/unit/test_config.py:

~~~python
from dataclasses import FrozenInstanceError

import pytest

from reviewlens.config import AnalysisConfig


def test_analysis_defaults_are_reproducible() -> None:
    config = AnalysisConfig()
    assert config.language == "id"
    assert config.preprocessing.stem is False
    assert config.preprocessing.protected_negations == (
        "tidak",
        "tak",
        "bukan",
        "belum",
        "jangan",
        "gak",
        "nggak",
        "enggak",
    )
    assert config.vectorizer.ngram_range == (1, 2)
    assert config.vectorizer.max_features == 50_000
    assert config.clustering.clusters == "auto"
    assert config.clustering.random_state == 42
    assert config.clustering.silhouette_sample_size == 5_000
    assert config.projection.sample_size == 10_000


def test_analysis_config_is_immutable() -> None:
    config = AnalysisConfig()
    with pytest.raises(FrozenInstanceError):
        config.language = "id"  # type: ignore[misc]
~~~

Create tests/unit/test_exceptions.py:

~~~python
from reviewlens.exceptions import (
    AnalysisError,
    ConfigurationError,
    ExportError,
    InputError,
    ReviewLensError,
)
from reviewlens.models import Diagnostic


def test_public_errors_share_one_base() -> None:
    for error_type in (InputError, ConfigurationError, AnalysisError, ExportError):
        assert issubclass(error_type, ReviewLensError)


def test_diagnostic_is_structured_and_immutable() -> None:
    diagnostic = Diagnostic(
        severity="warning",
        code="invalid_rating",
        message="One rating was ignored.",
        count=1,
    )
    assert diagnostic.code == "invalid_rating"
    assert diagnostic.count == 1
~~~

- [ ] **Step 4: Run the tests and observe the expected failure**

Run:

~~~bash
uv run pytest tests/unit/test_config.py tests/unit/test_exceptions.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.config, reviewlens.exceptions, or reviewlens.models.

- [ ] **Step 5: Implement configuration, errors, version, and Diagnostic**

Create src/reviewlens/config.py with immutable, slotted dataclasses:

~~~python
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
    interpretation: InterpretationConfig = field(
        default_factory=InterpretationConfig
    )
    projection: ProjectionConfig = field(default_factory=ProjectionConfig)
~~~

Create src/reviewlens/exceptions.py:

~~~python
class ReviewLensError(Exception):
    """Base class for expected ReviewLens failures."""


class InputError(ReviewLensError):
    """The supplied file or dataset contract is invalid."""


class ConfigurationError(ReviewLensError):
    """The supplied analysis configuration is invalid."""


class AnalysisError(ReviewLensError):
    """The dataset cannot produce a valid analysis."""


class ExportError(ReviewLensError):
    """The completed analysis cannot be exported safely."""
~~~

Create src/reviewlens/models.py:

~~~python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Diagnostic:
    severity: Literal["info", "warning"]
    code: str
    message: str
    count: int | None = None
~~~

Create src/reviewlens/__init__.py:

~~~python
"""ReviewLens public package."""

__version__ = "0.1.0"
~~~

Create an empty src/reviewlens/py.typed marker.

- [ ] **Step 6: Verify the foundation and Sastrawi compatibility**

Run:

~~~bash
uv run pytest tests/unit/test_config.py tests/unit/test_exceptions.py -q
uv run python -c "from Sastrawi.Stemmer.StemmerFactory import StemmerFactory; assert StemmerFactory().create_stemmer().stem('pelayanan') == 'layan'"
uv run ruff check src tests
uv run ruff format --check src tests
~~~

Expected: all commands pass; the Sastrawi command exits 0 without output.

- [ ] **Step 7: Commit the foundation**

~~~bash
git add pyproject.toml uv.lock .python-version .gitignore .editorconfig README.md src tests
git commit -m "chore: initialize ReviewLens Python package"
~~~

### Task 2: CSV/JSON ingestion and canonical schema

**Files:**
- Create: src/reviewlens/ingestion/__init__.py
- Create: src/reviewlens/ingestion/csv_loader.py
- Create: src/reviewlens/ingestion/json_loader.py
- Create: src/reviewlens/ingestion/normalization.py
- Create: src/reviewlens/ingestion/schema.py
- Create: tests/unit/test_ingestion.py

**Interfaces:**
- Consumes: IngestionConfig, Diagnostic, InputError.
- Produces: LoadedDataset and load_dataset(path, *, config, text_column=None, rating_column=None).

- [ ] **Step 1: Write failing loader/normalization tests**

Create tests/unit/test_ingestion.py with focused tests:

~~~python
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from reviewlens.config import IngestionConfig
from reviewlens.exceptions import InputError
from reviewlens.ingestion import load_dataset
from reviewlens.ingestion.normalization import normalize_columns


def test_json_list_normalizes_aliases_and_ratings(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(
        json.dumps(
            [
                {"reviewText": "Bagus", "stars": 5, "customField": "x"},
                {"reviewText": "Buruk", "stars": 7, "customField": "y"},
            ]
        ),
        encoding="utf-8",
    )
    loaded = load_dataset(path, config=IngestionConfig())
    assert loaded.frame["review_text"].tolist() == ["Bagus", "Buruk"]
    assert loaded.frame["source_row"].tolist() == [1, 2]
    assert loaded.frame["rating"].tolist()[0] == 5.0
    assert pd.isna(loaded.frame["rating"].tolist()[1])
    assert loaded.frame["custom_field"].tolist() == ["x", "y"]
    assert loaded.source_sha256
    assert loaded.diagnostics[0].code == "invalid_rating"
    assert loaded.diagnostics[0].count == 1


def test_json_object_uses_supported_records_key(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(
        json.dumps({"metadata": {"source": "synthetic"}, "reviews": [{"text": "A"}]}),
        encoding="utf-8",
    )
    loaded = load_dataset(path, config=IngestionConfig())
    assert loaded.frame.loc[0, "review_text"] == "A"


def test_json_object_rejects_ambiguous_arrays(tmp_path: Path) -> None:
    path = tmp_path / "reviews.json"
    path.write_text(
        json.dumps({"reviews": [{"text": "A"}], "data": [{"text": "B"}]}),
        encoding="utf-8",
    )
    with pytest.raises(InputError, match="multiple review arrays"):
        load_dataset(path, config=IngestionConfig())


def test_semicolon_csv_with_bom_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("reviewText;stars\\nCepat;5\\nLambat;2\\n", encoding="utf-8-sig")
    loaded = load_dataset(path, config=IngestionConfig())
    assert loaded.frame[["review_text", "rating"]].to_dict("records") == [
        {"review_text": "Cepat", "rating": 5.0},
        {"review_text": "Lambat", "rating": 2.0},
    ]


def test_normalization_collision_is_fatal() -> None:
    frame = pd.DataFrame([["A", "B"]], columns=["reviewText", "review_text"])
    with pytest.raises(InputError, match="normalize to 'review_text'"):
        normalize_columns(frame)


def test_explicit_text_column_wins(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("text,body\\nwrong,right\\n", encoding="utf-8")
    loaded = load_dataset(
        path,
        config=IngestionConfig(),
        text_column="body",
    )
    assert loaded.frame.loc[0, "review_text"] == "right"


def test_multiple_implicit_text_aliases_are_fatal(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    path.write_text("text,content\\na,b\\n", encoding="utf-8")
    with pytest.raises(InputError, match="multiple aliases"):
        load_dataset(path, config=IngestionConfig())
~~~

- [ ] **Step 2: Run the tests and observe missing ingestion modules**

Run:

~~~bash
uv run pytest tests/unit/test_ingestion.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.ingestion.

- [ ] **Step 3: Implement normalization and raw loaders**

Implement normalize_column_name(name: str) -> str by splitting case transitions, replacing every run of non-alphanumeric Unicode characters with one underscore, lowercasing, and trimming underscores. Implement normalize_columns(frame) -> DataFrame without silently dropping collisions.

Implement load_json_frame(path, records_key) so a list contains only mappings; an object uses an explicit records_key or exactly one list under reviews/data/items/results. Implement load_csv_frame(path, delimiter) with UTF-8-SIG and csv.Sniffer limited to comma, semicolon, tab, and pipe.

Use these exact core shapes:

~~~python
# normalization.py
_CASE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SEPARATORS = re.compile(r"[^0-9A-Za-z]+")


def normalize_column_name(name: str) -> str:
    split = _CASE_BOUNDARY.sub("_", str(name))
    return _SEPARATORS.sub("_", split).strip("_").lower()


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = [normalize_column_name(str(column)) for column in frame.columns]
    seen: dict[str, str] = {}
    for original, target in zip(frame.columns, normalized, strict=True):
        if not target:
            raise InputError(f"Column {original!r} normalizes to an empty name.")
        if target in seen:
            raise InputError(
                f"Columns {seen[target]!r} and {original!r} normalize to {target!r}."
            )
        seen[target] = str(original)
    result = frame.copy()
    result.columns = normalized
    return result
~~~

~~~python
# json_loader.py
RECORD_KEYS = ("reviews", "data", "items", "results")


def load_json_frame(path: Path, records_key: str | None) -> pd.DataFrame:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InputError(f"Cannot read JSON dataset {path.name}: {error}") from error
    if isinstance(value, list):
        records = value
    elif isinstance(value, dict):
        if records_key is not None:
            if not isinstance(value.get(records_key), list):
                raise InputError(f"JSON key {records_key!r} is not an array.")
            records = value[records_key]
        else:
            matches = [key for key in RECORD_KEYS if isinstance(value.get(key), list)]
            if len(matches) != 1:
                raise InputError(
                    "JSON object must contain exactly one review array; "
                    f"found multiple review arrays or none: {matches}."
                )
            records = value[matches[0]]
    else:
        raise InputError("JSON root must be an array or object.")
    if not all(isinstance(record, dict) for record in records):
        raise InputError("Every JSON review record must be an object.")
    return pd.DataFrame.from_records(records)
~~~

~~~python
# csv_loader.py
def load_csv_frame(path: Path, delimiter: str | None) -> pd.DataFrame:
    try:
        sample = path.read_text(encoding="utf-8-sig")[:16_384]
        selected = delimiter
        if selected is None:
            try:
                selected = csv.Sniffer().sniff(sample, delimiters=",;\\t|").delimiter
            except csv.Error:
                selected = ","
        return pd.read_csv(path, sep=selected, encoding="utf-8-sig")
    except (OSError, UnicodeError, pd.errors.ParserError) as error:
        raise InputError(f"Cannot read CSV dataset {path.name}: {error}") from error
~~~

- [ ] **Step 4: Implement schema resolution, rating coercion, hashing, and dispatch**

Create LoadedDataset as an immutable dataclass in schema.py. Reserve source_row, included, drop_reason, text_clean, text_model, and cluster_id for internal output. Use the alias table from the approved spec. Explicit text/rating arguments are normalized before lookup and bypass alias ambiguity.

The core schema logic must follow this implementation:

~~~python
TEXT_ALIASES = ("review_text", "text", "review", "content", "review_body")
RATING_ALIASES = ("rating", "stars", "score", "star_rating")
OPTIONAL_ALIASES = {
    "timestamp": ("timestamp", "created_at", "date", "review_date"),
    "location": ("location", "place", "venue", "address"),
    "metadata": ("metadata", "meta"),
}
RESERVED = {
    "source_row",
    "included",
    "drop_reason",
    "text_clean",
    "text_model",
    "cluster_id",
}


@dataclass(frozen=True, slots=True)
class LoadedDataset:
    frame: pd.DataFrame
    source_path: Path
    source_sha256: str
    source_stem: str
    diagnostics: tuple[Diagnostic, ...]


def _select_column(
    columns: pd.Index,
    canonical: str,
    aliases: tuple[str, ...],
    explicit: str | None,
) -> str | None:
    if explicit is not None:
        selected = normalize_column_name(explicit)
        if selected not in columns:
            raise InputError(f"Column {explicit!r} was not found after normalization.")
        return selected
    present = [alias for alias in aliases if alias in columns]
    if len(present) > 1:
        raise InputError(f"Found multiple aliases for {canonical}: {present}.")
    return present[0] if present else None


def canonicalize_schema(
    frame: pd.DataFrame,
    *,
    text_column: str | None,
    rating_column: str | None,
) -> tuple[pd.DataFrame, tuple[Diagnostic, ...]]:
    result = normalize_columns(frame)
    reserved = RESERVED.intersection(result.columns)
    if reserved:
        raise InputError(f"Input uses reserved ReviewLens columns: {sorted(reserved)}.")
    text = _select_column(
        result.columns, "review_text", TEXT_ALIASES, text_column
    )
    if text is None:
        raise InputError("A review-text column is required.")
    rating = _select_column(
        result.columns, "rating", RATING_ALIASES, rating_column
    )
    rename = {text: "review_text"}
    if rating is not None:
        rename[rating] = "rating"
    for canonical, aliases in OPTIONAL_ALIASES.items():
        selected = _select_column(result.columns, canonical, aliases, None)
        if selected is not None:
            rename[selected] = canonical
    result = result.rename(columns=rename)
    result.insert(0, "source_row", range(1, len(result) + 1))
    diagnostics: list[Diagnostic] = []
    if "rating" not in result:
        result["rating"] = pd.Series(pd.NA, index=result.index, dtype="Float64")
    else:
        raw = result["rating"]
        numeric = pd.to_numeric(raw, errors="coerce")
        invalid = raw.notna() & (numeric.isna() | ~numeric.between(1, 5))
        result["rating"] = numeric.mask(invalid).astype("Float64")
        if int(invalid.sum()):
            diagnostics.append(
                Diagnostic(
                    severity="warning",
                    code="invalid_rating",
                    message="Ratings outside numeric range 1-5 were ignored.",
                    count=int(invalid.sum()),
                )
            )
    for canonical in OPTIONAL_ALIASES:
        if canonical not in result:
            result[canonical] = pd.NA
    return result, tuple(diagnostics)
~~~

In ingestion/__init__.py, implement _sha256 with 1 MiB chunks and load_dataset:

~~~python
def load_dataset(
    path: str | Path,
    *,
    config: IngestionConfig,
    text_column: str | None = None,
    rating_column: str | None = None,
) -> LoadedDataset:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise InputError(f"Dataset does not exist or is not a file: {source}.")
    suffix = source.suffix.lower()
    if suffix == ".csv":
        raw = load_csv_frame(source, config.csv_delimiter)
    elif suffix == ".json":
        raw = load_json_frame(source, config.records_key)
    else:
        raise InputError("Supported dataset extensions are .csv and .json.")
    if raw.empty:
        raise InputError("Dataset contains no review records.")
    frame, diagnostics = canonicalize_schema(
        raw, text_column=text_column, rating_column=rating_column
    )
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return LoadedDataset(
        frame=frame,
        source_path=source,
        source_sha256=digest.hexdigest(),
        source_stem=source.stem,
        diagnostics=diagnostics,
    )
~~~

- [ ] **Step 5: Verify ingestion**

Run:

~~~bash
uv run pytest tests/unit/test_ingestion.py -q
uv run ruff check src/reviewlens/ingestion tests/unit/test_ingestion.py
uv run mypy src/reviewlens/config.py src/reviewlens/models.py src/reviewlens/ingestion tests/unit/test_ingestion.py
~~~

Expected: all commands pass.

- [ ] **Step 6: Commit ingestion**

~~~bash
git add src/reviewlens/ingestion tests/unit/test_ingestion.py
git commit -m "feat: add review dataset ingestion"
~~~

### Task 3: Indonesian preprocessing

**Files:**
- Create: src/reviewlens/preprocessing/__init__.py
- Create: src/reviewlens/preprocessing/cleaner.py
- Create: src/reviewlens/preprocessing/indonesian.py
- Create: src/reviewlens/preprocessing/slang.py
- Create: src/reviewlens/resources/slang_id.json
- Create: tests/unit/test_preprocessing.py

**Interfaces:**
- Consumes: canonical ingestion frame, PreprocessingConfig, Diagnostic, InputError.
- Produces: PreprocessingResult(frame, modeling_frame, diagnostics) and preprocess_reviews(frame, config).

- [ ] **Step 1: Write failing preprocessing tests**

Create tests/unit/test_preprocessing.py:

~~~python
from __future__ import annotations

import pandas as pd
import pytest

from reviewlens.config import PreprocessingConfig
from reviewlens.exceptions import InputError
from reviewlens.preprocessing import preprocess_reviews
from reviewlens.preprocessing.cleaner import clean_text_basic


def _frame(texts: list[object]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_row": range(1, len(texts) + 1),
            "review_text": texts,
            "rating": pd.Series([pd.NA] * len(texts), dtype="Float64"),
        }
    )


def test_basic_cleaning_handles_unicode_url_emoji_and_punctuation() -> None:
    assert clean_text_basic("  LAYANAN!!! https://x.test 😊  ") == "layanan"
    assert clean_text_basic("Kafe—rapi") == "kafe rapi"


def test_slang_and_stopwords_preserve_negation() -> None:
    result = preprocess_reviews(
        _frame(["Pelayanan gk cepat dan tidak ramah"]),
        PreprocessingConfig(),
    )
    assert result.modeling_frame.loc[0, "text_model"] == (
        "pelayanan gak cepat tidak ramah"
    )
    assert "tidak" in result.modeling_frame.loc[0, "text_model"].split()
    assert "dan" not in result.modeling_frame.loc[0, "text_model"].split()


def test_stemming_is_explicit() -> None:
    without_stem = preprocess_reviews(
        _frame(["pelayanan membantu"]),
        PreprocessingConfig(remove_stopwords=False),
    )
    with_stem = preprocess_reviews(
        _frame(["pelayanan membantu"]),
        PreprocessingConfig(remove_stopwords=False, stem=True),
    )
    assert without_stem.modeling_frame.loc[0, "text_model"] == "pelayanan membantu"
    assert with_stem.modeling_frame.loc[0, "text_model"] == "layan bantu"


def test_blank_rows_remain_visible_but_are_excluded() -> None:
    result = preprocess_reviews(_frame(["Bagus", None, "!!!"]), PreprocessingConfig())
    assert result.frame["included"].tolist() == [True, False, False]
    assert pd.isna(result.frame.loc[0, "drop_reason"])
    assert result.frame["drop_reason"].iloc[1:].tolist() == [
        "blank_review",
        "blank_review",
    ]
    assert result.modeling_frame["source_row"].tolist() == [1]
    assert result.diagnostics[0].code == "blank_review_excluded"
    assert result.diagnostics[0].count == 2


def test_all_blank_rows_are_fatal() -> None:
    with pytest.raises(InputError, match="No usable reviews"):
        preprocess_reviews(_frame([None, "!!!"]), PreprocessingConfig())
~~~

- [ ] **Step 2: Run the tests and observe the expected failure**

Run:

~~~bash
uv run pytest tests/unit/test_preprocessing.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.preprocessing.

- [ ] **Step 3: Add the newly authored slang resource**

Create src/reviewlens/resources/slang_id.json with exactly:

~~~json
{
  "aja": "saja",
  "bgt": "banget",
  "dgn": "dengan",
  "dr": "dari",
  "ga": "gak",
  "gk": "gak",
  "jd": "jadi",
  "krn": "karena",
  "ngga": "gak",
  "nggak": "gak",
  "org": "orang",
  "pdhl": "padahal",
  "sm": "sama",
  "tdk": "tidak",
  "tp": "tapi",
  "utk": "untuk",
  "yg": "yang"
}
~~~

Implement slang.py with importlib.resources.files("reviewlens.resources"), canonical JSON loading, and deterministic merge of config.extra_slang. Reject empty keys/values with ConfigurationError.

- [ ] **Step 4: Implement cleaning, protected stopwords, and optional stemming**

Use these exact behaviors:

~~~python
# cleaner.py
_URL = re.compile(r"https?://\\S+|www\\.\\S+", re.IGNORECASE)
_WHITESPACE = re.compile(r"\\s+")
_TOKEN = re.compile(r"[^\\W_]+", re.UNICODE)


def _is_emoji(character: str) -> bool:
    value = ord(character)
    return (
        0x1F000 <= value <= 0x1FAFF
        or 0x2600 <= value <= 0x27BF
        or 0xFE00 <= value <= 0xFE0F
    )


def clean_text_basic(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).lower()
    text = _URL.sub(" ", text)
    text = "".join(
        " "
        if _is_emoji(character)
        or unicodedata.category(character).startswith("P")
        else character
        for character in text
    )
    return _WHITESPACE.sub(" ", text).strip()
~~~

~~~python
# indonesian.py
@lru_cache(maxsize=1)
def default_stopwords() -> frozenset[str]:
    factory = StopWordRemoverFactory()
    return frozenset(word.lower() for word in factory.get_stop_words())


@lru_cache(maxsize=1)
def default_stemmer() -> Stemmer:
    return StemmerFactory().create_stemmer()


def model_tokens(text: str, config: PreprocessingConfig) -> list[str]:
    slang = load_slang_map(config.extra_slang) if config.normalize_slang else {}
    tokens = [slang.get(token, token) for token in _TOKEN.findall(text)]
    if config.remove_stopwords:
        protected = set(config.protected_negations)
        stopwords = (set(default_stopwords()) | set(config.extra_stopwords)) - protected
        tokens = [token for token in tokens if token not in stopwords]
    if config.stem:
        stemmer = default_stemmer()
        tokens = [stemmer.stem(token) for token in tokens]
    return [token for token in tokens if token]
~~~

~~~python
# cleaner.py
@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    frame: pd.DataFrame
    modeling_frame: pd.DataFrame
    diagnostics: tuple[Diagnostic, ...]


def preprocess_reviews(
    frame: pd.DataFrame,
    config: PreprocessingConfig,
) -> PreprocessingResult:
    result = frame.copy()
    result["text_clean"] = result["review_text"].map(clean_text_basic)
    result["text_model"] = result["text_clean"].map(
        lambda text: " ".join(model_tokens(text, config))
    )
    result["included"] = result["text_model"].str.strip().ne("")
    result["drop_reason"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result.loc[~result["included"], "drop_reason"] = "blank_review"
    excluded = int((~result["included"]).sum())
    diagnostics: tuple[Diagnostic, ...] = ()
    if excluded:
        diagnostics = (
            Diagnostic(
                severity="warning",
                code="blank_review_excluded",
                message="Reviews empty after preprocessing were excluded.",
                count=excluded,
            ),
        )
    modeling = result.loc[result["included"]].copy().reset_index(drop=True)
    if modeling.empty:
        raise InputError("No usable reviews remain after preprocessing.")
    return PreprocessingResult(result, modeling, diagnostics)
~~~

Export PreprocessingResult, clean_text_basic, and preprocess_reviews from preprocessing/__init__.py. Add an empty src/reviewlens/resources/__init__.py so importlib.resources can load slang_id.json.

- [ ] **Step 5: Tighten the slang/negation assertion and verify**

Replace the conditional expression in test_slang_and_stopwords_preserve_negation with:

~~~python
assert result.modeling_frame.loc[0, "text_model"] == (
    "pelayanan gak cepat tidak ramah"
)
~~~

Run:

~~~bash
uv run pytest tests/unit/test_preprocessing.py -q
uv run ruff check src/reviewlens/preprocessing src/reviewlens/resources tests/unit/test_preprocessing.py
uv run mypy src/reviewlens/preprocessing tests/unit/test_preprocessing.py
~~~

Expected: all commands pass. If the Sastrawi stopword set removes a protected negation, fix model_tokens by subtracting the protected set after adding extra stopwords; do not weaken the assertion.

- [ ] **Step 6: Commit preprocessing**

~~~bash
git add src/reviewlens/preprocessing src/reviewlens/resources tests/unit/test_preprocessing.py
git commit -m "feat: add Indonesian review preprocessing"
~~~

### Task 4: Sparse TF-IDF feature extraction

**Files:**
- Create: src/reviewlens/analysis/__init__.py
- Create: src/reviewlens/analysis/vectorizer.py
- Create: tests/unit/test_vectorizer.py

**Interfaces:**
- Consumes: PreprocessingResult.modeling_frame and VectorizerConfig.
- Produces: VectorizationResult(matrix: csr_matrix, vectorizer: TfidfVectorizer) and vectorize_reviews.

- [ ] **Step 1: Write failing vectorizer tests**

Create tests/unit/test_vectorizer.py:

~~~python
import pandas as pd
import pytest

from reviewlens.analysis.vectorizer import vectorize_reviews
from reviewlens.config import VectorizerConfig
from reviewlens.exceptions import AnalysisError


def test_vectorizer_uses_sparse_unigrams_and_bigrams() -> None:
    frame = pd.DataFrame(
        {"text_model": ["pelayanan cepat ramah", "pelayanan lambat antre"]}
    )
    result = vectorize_reviews(frame, VectorizerConfig())
    features = set(result.vectorizer.get_feature_names_out())
    assert result.matrix.shape[0] == 2
    assert "pelayanan" in features
    assert "pelayanan cepat" in features


def test_identical_feature_rows_are_rejected() -> None:
    frame = pd.DataFrame({"text_model": ["sama persis", "sama persis", "sama persis"]})
    with pytest.raises(AnalysisError, match="distinguishable"):
        vectorize_reviews(frame, VectorizerConfig())


def test_empty_vocabulary_has_actionable_error() -> None:
    frame = pd.DataFrame({"text_model": ["a", "b"]})
    with pytest.raises(AnalysisError, match="vocabulary"):
        vectorize_reviews(frame, VectorizerConfig())
~~~

- [ ] **Step 2: Run the focused test and observe the missing module**

Run:

~~~bash
uv run pytest tests/unit/test_vectorizer.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.analysis.vectorizer.

- [ ] **Step 3: Implement vectorization and efficient distinct-row validation**

Create vectorizer.py:

~~~python
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from reviewlens.config import VectorizerConfig
from reviewlens.exceptions import AnalysisError


@dataclass(frozen=True, slots=True)
class VectorizationResult:
    matrix: csr_matrix
    vectorizer: TfidfVectorizer


def _has_two_distinct_rows(matrix: csr_matrix) -> bool:
    first = matrix.getrow(0)
    return any((matrix.getrow(index) != first).nnz for index in range(1, matrix.shape[0]))


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
~~~

Export VectorizationResult and vectorize_reviews from analysis/__init__.py.

- [ ] **Step 4: Verify and commit vectorization**

Run:

~~~bash
uv run pytest tests/unit/test_vectorizer.py -q
uv run ruff check src/reviewlens/analysis tests/unit/test_vectorizer.py
uv run mypy src/reviewlens/analysis/vectorizer.py tests/unit/test_vectorizer.py
~~~

Expected: all commands pass.

~~~bash
git add src/reviewlens/analysis tests/unit/test_vectorizer.py
git commit -m "feat: add TF-IDF feature extraction"
~~~

### Task 5: K-Means evaluation and deterministic cluster selection

**Files:**
- Create: src/reviewlens/analysis/evaluation.py
- Create: src/reviewlens/analysis/clustering.py
- Create: tests/unit/test_clustering.py

**Interfaces:**
- Consumes: csr_matrix and ClusteringConfig.
- Produces: ClusteringResult(model, labels, selected_k, evaluation) and cluster_features.

- [ ] **Step 1: Write failing clustering tests**

Create tests/unit/test_clustering.py:

~~~python
from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from reviewlens.analysis.clustering import cluster_features
from reviewlens.config import ClusteringConfig
from reviewlens.exceptions import AnalysisError, ConfigurationError


def _separated_matrix() -> csr_matrix:
    return csr_matrix(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.0, 1.0, 0.0],
                [0.1, 0.9, 0.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.1, 0.9],
            ]
        )
    )


def test_auto_k_returns_valid_evaluation_and_seeded_labels() -> None:
    first = cluster_features(_separated_matrix(), ClusteringConfig())
    second = cluster_features(_separated_matrix(), ClusteringConfig())
    assert 2 <= first.selected_k <= 5
    assert set(first.evaluation.columns) == {
        "k",
        "inertia",
        "silhouette",
        "valid",
        "reason",
    }
    assert first.labels.tolist() == second.labels.tolist()


def test_auto_k_requires_three_rows() -> None:
    with pytest.raises(AnalysisError, match="at least three"):
        cluster_features(csr_matrix([[1.0, 0.0], [0.0, 1.0]]), ClusteringConfig())


def test_manual_k_is_validated() -> None:
    with pytest.raises(ConfigurationError, match="2 <= k"):
        cluster_features(_separated_matrix(), ClusteringConfig(clusters=6))


def test_manual_k_skips_range_unless_requested() -> None:
    result = cluster_features(_separated_matrix(), ClusteringConfig(clusters=3))
    assert result.selected_k == 3
    assert result.evaluation.empty
~~~

- [ ] **Step 2: Run the focused tests and observe missing modules**

Run:

~~~bash
uv run pytest tests/unit/test_clustering.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.analysis.clustering.

- [ ] **Step 3: Implement candidate fitting and evaluation**

Create evaluation.py with an internal immutable EvaluationCandidate containing k, inertia, silhouette, valid, reason, and model. Fit KMeans once per candidate with random_state, n_init, and max_iter from ClusteringConfig. A fit is invalid when the number of unique labels differs from k or silhouette_score raises ValueError.

Use:

~~~python
@dataclass(frozen=True, slots=True)
class EvaluationCandidate:
    k: int
    inertia: float | None
    silhouette: float | None
    valid: bool
    reason: str | None
    model: KMeans | None


def fit_candidate(
    matrix: csr_matrix,
    k: int,
    config: ClusteringConfig,
) -> EvaluationCandidate:
    model = KMeans(
        n_clusters=k,
        random_state=config.random_state,
        n_init=config.n_init,
        max_iter=config.max_iter,
    )
    try:
        labels = model.fit_predict(matrix)
        if len(np.unique(labels)) != k:
            return EvaluationCandidate(
                k, float(model.inertia_), None, False, "fewer_labels_than_requested", None
            )
        sample_size = (
            config.silhouette_sample_size
            if matrix.shape[0] > config.silhouette_sample_size
            else None
        )
        score = silhouette_score(
            matrix,
            labels,
            metric="cosine",
            sample_size=sample_size,
            random_state=config.random_state,
        )
        return EvaluationCandidate(
            k, float(model.inertia_), float(score), True, None, model
        )
    except ValueError as error:
        return EvaluationCandidate(k, None, None, False, str(error), None)


def evaluate_candidates(
    matrix: csr_matrix,
    config: ClusteringConfig,
) -> list[EvaluationCandidate]:
    upper = min(config.k_max, matrix.shape[0] - 1)
    return [fit_candidate(matrix, k, config) for k in range(2, upper + 1)]
~~~

- [ ] **Step 4: Implement auto/manual selection**

Create clustering.py:

~~~python
@dataclass(frozen=True, slots=True)
class ClusteringResult:
    model: KMeans
    labels: NDArray[np.int_]
    selected_k: int
    evaluation: pd.DataFrame


def _evaluation_frame(
    candidates: list[EvaluationCandidate],
) -> pd.DataFrame:
    return pd.DataFrame.from_records(
        [
            {
                "k": candidate.k,
                "inertia": candidate.inertia,
                "silhouette": candidate.silhouette,
                "valid": candidate.valid,
                "reason": candidate.reason,
            }
            for candidate in candidates
        ],
        columns=["k", "inertia", "silhouette", "valid", "reason"],
    )


def cluster_features(
    matrix: csr_matrix,
    config: ClusteringConfig,
) -> ClusteringResult:
    row_count = matrix.shape[0]
    if config.clusters == "auto":
        if row_count < 3:
            raise AnalysisError("Automatic clustering requires at least three reviews.")
        candidates = evaluate_candidates(matrix, config)
        valid = [
            candidate
            for candidate in candidates
            if candidate.valid and candidate.silhouette is not None
        ]
        if not valid:
            raise AnalysisError(
                "No candidate cluster count produced a valid silhouette score."
            )
        winner = max(valid, key=lambda item: (float(item.silhouette), -item.k))
        assert winner.model is not None
        return ClusteringResult(
            model=winner.model,
            labels=np.asarray(winner.model.labels_, dtype=np.int_),
            selected_k=winner.k,
            evaluation=_evaluation_frame(candidates),
        )
    selected = int(config.clusters)
    if not 2 <= selected < row_count:
        raise ConfigurationError(
            f"Manual clusters must satisfy 2 <= k < {row_count}; received {selected}."
        )
    chosen = fit_candidate(matrix, selected, config)
    if not chosen.valid or chosen.model is None:
        raise AnalysisError(
            f"Manual cluster count {selected} is invalid: {chosen.reason}."
        )
    evaluation = (
        _evaluation_frame(evaluate_candidates(matrix, config))
        if config.evaluate_manual
        else _evaluation_frame([])
    )
    return ClusteringResult(
        model=chosen.model,
        labels=np.asarray(chosen.model.labels_, dtype=np.int_),
        selected_k=selected,
        evaluation=evaluation,
    )
~~~

- [ ] **Step 5: Verify tie behavior explicitly**

Add this test using monkeypatch so equal silhouette scores choose smaller k:

~~~python
def test_equal_silhouette_scores_choose_smaller_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "reviewlens.analysis.evaluation.silhouette_score",
        lambda *args, **kwargs: 0.5,
    )
    result = cluster_features(_separated_matrix(), ClusteringConfig())
    assert result.selected_k == 2
~~~

Run:

~~~bash
uv run pytest tests/unit/test_clustering.py -q
uv run ruff check src/reviewlens/analysis tests/unit/test_clustering.py
uv run mypy src/reviewlens/analysis tests/unit/test_clustering.py
~~~

Expected: all commands pass.

- [ ] **Step 6: Commit clustering**

~~~bash
git add src/reviewlens/analysis/evaluation.py src/reviewlens/analysis/clustering.py tests/unit/test_clustering.py
git commit -m "feat: add deterministic K-Means selection"
~~~

### Task 6: Deterministic cluster interpretation

**Files:**
- Create: src/reviewlens/analysis/interpretation.py
- Create: tests/unit/test_interpretation.py

**Interfaces:**
- Consumes: modeling_frame, VectorizationResult, ClusteringResult, InterpretationConfig.
- Produces: InterpretationResult(reviews, clusters, summary, keywords, presentation_labels).

- [ ] **Step 1: Write failing interpretation tests**

Create tests/unit/test_interpretation.py:

~~~python
from __future__ import annotations

import pandas as pd

from reviewlens.analysis.clustering import cluster_features
from reviewlens.analysis.interpretation import interpret_clusters
from reviewlens.analysis.vectorizer import vectorize_reviews
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


def test_representatives_are_nearest_and_source_order_breaks_ties() -> None:
    frame = _modeling_frame()
    vectorization = vectorize_reviews(frame, VectorizerConfig())
    clustering = cluster_features(
        vectorization.matrix,
        ClusteringConfig(clusters=2),
    )
    first = interpret_clusters(
        frame, vectorization, clustering, InterpretationConfig()
    )
    second = interpret_clusters(
        frame, vectorization, clustering, InterpretationConfig()
    )
    assert first.clusters["representative_source_rows"].tolist() == (
        second.clusters["representative_source_rows"].tolist()
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
~~~

- [ ] **Step 2: Run the focused tests and observe the missing module**

Run:

~~~bash
uv run pytest tests/unit/test_interpretation.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.analysis.interpretation.

- [ ] **Step 3: Implement keyword ranking, presentation IDs, and representatives**

Create InterpretationResult with the five fields in the interface ledger. Build per-original-label drafts first. For each label:

1. select row positions in the sparse matrix;
2. compute mean TF-IDF weights;
3. keep positive terms, sorting by descending score then ascending term;
4. create the theme by joining the first three terms with " · ";
5. compute cosine distance to the matching K-Means center;
6. sort representatives by distance then source_row and keep three.

Then sort drafts by (-count, theme, original_label), map to consecutive presentation IDs, and construct tidy DataFrames. Use this rating and prose logic:

~~~python
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
~~~

The cluster DataFrame columns, in order, are cluster_id, review_count, share, average_rating, rating_signal, theme, summary, keywords, representative_reviews, representative_source_rows. keywords and representative fields remain tuples in memory; the exporter serializes them later.

- [ ] **Step 4: Implement dataset summary rows**

Create rows with columns category, name, value, details:

- analysis/input-ready retained review count;
- analysis/selected_k;
- rating/overall_average_rating when ratings exist;
- highlight/largest_cluster;
- highlight/lowest_rated_cluster and highlight/highest_rated_cluster when ratings exist;
- rating/rating_unavailable when all ratings are missing.

Do not infer NLP sentiment beyond rating_signal. The lowest/highest rows refer to the deterministic presentation cluster ID and theme.

- [ ] **Step 5: Verify interpretation and commit**

Run:

~~~bash
uv run pytest tests/unit/test_interpretation.py -q
uv run ruff check src/reviewlens/analysis/interpretation.py tests/unit/test_interpretation.py
uv run mypy src/reviewlens/analysis/interpretation.py tests/unit/test_interpretation.py
~~~

Expected: all commands pass.

~~~bash
git add src/reviewlens/analysis/interpretation.py tests/unit/test_interpretation.py
git commit -m "feat: add deterministic cluster interpretation"
~~~

### Task 7: Two-dimensional projection

**Files:**
- Create: src/reviewlens/analysis/projection.py
- Create: tests/unit/test_projection.py

**Interfaces:**
- Consumes: matrix, presentation labels aligned with matrix rows, source-row array, ProjectionConfig.
- Produces: ProjectionResult(data with source_row/x/y/cluster_id, diagnostics).

- [ ] **Step 1: Write failing projection tests**

Create tests/unit/test_projection.py:

~~~python
import numpy as np
from scipy.sparse import csr_matrix

from reviewlens.analysis.projection import project_features
from reviewlens.config import ProjectionConfig


def test_projection_is_seeded_and_aligned() -> None:
    matrix = csr_matrix(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.9, 0.1],
            ]
        )
    )
    labels = np.array([0, 0, 1, 1])
    rows = np.array([10, 11, 12, 13])
    first = project_features(matrix, labels, rows, ProjectionConfig())
    second = project_features(matrix, labels, rows, ProjectionConfig())
    assert first.data.columns.tolist() == ["source_row", "x", "y", "cluster_id"]
    assert first.data.equals(second.data)
    assert first.data["source_row"].tolist() == [10, 11, 12, 13]


def test_projection_samples_at_most_configured_rows() -> None:
    matrix = csr_matrix(np.eye(20))
    labels = np.arange(20) % 2
    rows = np.arange(1, 21)
    result = project_features(
        matrix,
        labels,
        rows,
        ProjectionConfig(sample_size=5),
    )
    assert len(result.data) == 5
    assert result.data["source_row"].is_monotonic_increasing


def test_one_feature_uses_zero_y_and_warning() -> None:
    matrix = csr_matrix([[1.0], [2.0], [3.0]])
    result = project_features(
        matrix,
        np.array([0, 0, 1]),
        np.array([1, 2, 3]),
        ProjectionConfig(),
    )
    assert result.data["y"].tolist() == [0.0, 0.0, 0.0]
    assert result.diagnostics[0].code == "one_dimensional_projection"
~~~

- [ ] **Step 2: Run the focused tests and observe the missing module**

Run:

~~~bash
uv run pytest tests/unit/test_projection.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.analysis.projection.

- [ ] **Step 3: Implement deterministic sampling and projection**

Create projection.py:

~~~python
@dataclass(frozen=True, slots=True)
class ProjectionResult:
    data: pd.DataFrame
    diagnostics: tuple[Diagnostic, ...]


def project_features(
    matrix: csr_matrix,
    presentation_labels: NDArray[np.int_],
    source_rows: NDArray[np.int_],
    config: ProjectionConfig,
) -> ProjectionResult:
    row_count = matrix.shape[0]
    if len(presentation_labels) != row_count or len(source_rows) != row_count:
        raise AnalysisError("Projection labels and source rows must align with features.")
    indices = np.arange(row_count)
    if row_count > config.sample_size:
        rng = np.random.default_rng(config.random_state)
        indices = np.sort(
            rng.choice(indices, size=config.sample_size, replace=False)
        )
    selected = matrix[indices]
    diagnostics: tuple[Diagnostic, ...] = ()
    if selected.shape[1] == 1:
        x = selected.toarray()[:, 0].astype(float)
        y = np.zeros(len(indices), dtype=float)
        diagnostics = (
            Diagnostic(
                severity="warning",
                code="one_dimensional_projection",
                message="Projection used one feature dimension and a zero y-axis.",
            ),
        )
    else:
        reducer = TruncatedSVD(
            n_components=config.components,
            random_state=config.random_state,
        )
        coordinates = reducer.fit_transform(selected)
        x = coordinates[:, 0].astype(float)
        y = coordinates[:, 1].astype(float)
    data = pd.DataFrame(
        {
            "source_row": source_rows[indices],
            "x": x,
            "y": y,
            "cluster_id": presentation_labels[indices],
        }
    ).sort_values("source_row", ignore_index=True)
    return ProjectionResult(data=data, diagnostics=diagnostics)
~~~

- [ ] **Step 4: Verify and commit projection**

Run:

~~~bash
uv run pytest tests/unit/test_projection.py -q
uv run ruff check src/reviewlens/analysis/projection.py tests/unit/test_projection.py
uv run mypy src/reviewlens/analysis/projection.py tests/unit/test_projection.py
~~~

Expected: all commands pass.

~~~bash
git add src/reviewlens/analysis/projection.py tests/unit/test_projection.py
git commit -m "feat: add cluster projection data"
~~~

### Task 8: Side-effect-free public analysis API

**Files:**
- Modify: src/reviewlens/models.py
- Create: src/reviewlens/api.py
- Modify: src/reviewlens/__init__.py
- Create: tests/unit/test_api.py

**Interfaces:**
- Consumes: every stage interface from Tasks 1-7.
- Produces: AnalysisResult and analyze_reviews; the exporter method is added in Task 10.

- [ ] **Step 1: Write failing API tests**

Create tests/unit/test_api.py:

~~~python
from __future__ import annotations

from pathlib import Path

import pytest

from reviewlens import AnalysisConfig, AnalysisResult, analyze_reviews
from reviewlens.exceptions import ConfigurationError


def _write_reviews(path: Path) -> None:
    path.write_text(
        "text,rating\\n"
        "pelayanan lambat antre,2\\n"
        "antre lama pelayanan,1\\n"
        "petugas lambat antre,2\\n"
        "tempat bersih nyaman,5\\n"
        "bersih rapi nyaman,4\\n"
        "lokasi nyaman bersih,5\\n",
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
    result = analyze_reviews(source, clusters=2, config=AnalysisConfig())
    assert result.metadata["selected_k"] == 2


def test_non_indonesian_language_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    _write_reviews(source)
    with pytest.raises(ConfigurationError, match="language"):
        analyze_reviews(source, language="en")  # type: ignore[arg-type]
~~~

- [ ] **Step 2: Run the tests and observe missing public API exports**

Run:

~~~bash
uv run pytest tests/unit/test_api.py -q
~~~

Expected: import fails because AnalysisResult and analyze_reviews are not exported.

- [ ] **Step 3: Add AnalysisResult and ExportManifest models**

Extend models.py:

~~~python
@dataclass(frozen=True, slots=True)
class ExportManifest:
    workbook_path: Path
    chart_paths: tuple[Path, ...]


@dataclass(slots=True)
class AnalysisResult:
    reviews: pd.DataFrame
    clusters: pd.DataFrame
    summary: pd.DataFrame
    keywords: pd.DataFrame
    evaluation: pd.DataFrame
    visual_data: dict[str, pd.DataFrame]
    metadata: dict[str, object]
    diagnostics: tuple[Diagnostic, ...]
    source_stem: str
~~~

Do not add a method that imports a nonexistent exporter. Task 10 adds export_excel together with the concrete export_analysis implementation.

- [ ] **Step 4: Implement effective configuration, orchestration, and metadata**

In api.py, implement:

~~~python
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
    if effective.vectorizer.ngram_range[0] < 1:
        raise ConfigurationError("ngram_range minimum must be at least 1.")
    if effective.vectorizer.ngram_range[0] > effective.vectorizer.ngram_range[1]:
        raise ConfigurationError("ngram_range minimum cannot exceed maximum.")
    if effective.vectorizer.max_features < 1:
        raise ConfigurationError("max_features must be positive.")
    return effective
~~~

Orchestrate load -> preprocess -> vectorize -> cluster -> interpret -> project. Merge presentation cluster IDs into the full preprocessed frame by source_row so excluded rows remain with missing cluster IDs. Build visual tables:

~~~python
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
~~~

Metadata includes ReviewLens/dependency versions, effective dataclass configuration via asdict, source basename, SHA-256, datetime.now(timezone.utc).isoformat(), input/retained/excluded counts, and selected_k. Do not include source_path.

Concatenate diagnostics in stage order: ingestion, preprocessing, projection, followed by an info diagnostic when no valid rating exists. Return AnalysisResult.

- [ ] **Step 5: Export the public API surface**

Update src/reviewlens/__init__.py to export:

~~~python
from reviewlens.api import analyze_reviews
from reviewlens.config import AnalysisConfig
from reviewlens.exceptions import (
    AnalysisError,
    ConfigurationError,
    ExportError,
    InputError,
    ReviewLensError,
)
from reviewlens.models import AnalysisResult, Diagnostic, ExportManifest

__all__ = [
    "AnalysisConfig",
    "AnalysisError",
    "AnalysisResult",
    "ConfigurationError",
    "Diagnostic",
    "ExportError",
    "ExportManifest",
    "InputError",
    "ReviewLensError",
    "analyze_reviews",
]
__version__ = "0.1.0"
~~~

- [ ] **Step 6: Verify the complete in-memory pipeline**

Run:

~~~bash
uv run pytest tests/unit -q
uv run ruff check src tests/unit
uv run mypy src tests/unit
~~~

Expected: all commands pass and no test creates a workbook or chart.

- [ ] **Step 7: Commit the public API**

~~~bash
git add src/reviewlens/api.py src/reviewlens/models.py src/reviewlens/__init__.py tests/unit/test_api.py
git commit -m "feat: add public review analysis API"
~~~

### Task 9: Deterministic PNG chart generation

**Files:**
- Create: src/reviewlens/export/__init__.py
- Create: src/reviewlens/export/charts.py
- Create: tests/unit/test_charts.py

**Interfaces:**
- Consumes: AnalysisResult.visual_data and clusters.
- Produces: ordered tuple of ChartArtifact(name, path, title) and PNG files under an explicit staging directory.

- [ ] **Step 1: Write failing chart tests**

Create tests/unit/test_charts.py:

~~~python
from pathlib import Path

from reviewlens import analyze_reviews
from reviewlens.export.charts import generate_charts


def _source(tmp_path: Path, with_rating: bool = True) -> Path:
    path = tmp_path / "reviews.csv"
    header = "text,rating\\n" if with_rating else "text\\n"
    rows = [
        "pelayanan lambat antre,2\\n" if with_rating else "pelayanan lambat antre\\n",
        "antre lama pelayanan,1\\n" if with_rating else "antre lama pelayanan\\n",
        "petugas lambat antre,2\\n" if with_rating else "petugas lambat antre\\n",
        "tempat bersih nyaman,5\\n" if with_rating else "tempat bersih nyaman\\n",
        "bersih rapi nyaman,4\\n" if with_rating else "bersih rapi nyaman\\n",
        "lokasi nyaman bersih,5\\n" if with_rating else "lokasi nyaman bersih\\n",
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


def test_rating_chart_is_omitted_without_ratings(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path, with_rating=False), clusters=2)
    artifacts = generate_charts(result, tmp_path / "charts")
    assert "rating_distribution" not in [artifact.name for artifact in artifacts]
~~~

- [ ] **Step 2: Run the tests and observe the missing chart module**

Run:

~~~bash
uv run pytest tests/unit/test_charts.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.export.charts.

- [ ] **Step 3: Implement ChartArtifact and safe figure saving**

At the top of charts.py, select the Agg backend before importing pyplot. Define:

~~~python
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass(frozen=True, slots=True)
class ChartArtifact:
    name: str
    path: Path
    title: str


def _save(
    figure: Figure,
    output_dir: Path,
    name: str,
    title: str,
) -> ChartArtifact:
    path = output_dir / f"{name}.png"
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return ChartArtifact(name=name, path=path, title=title)
~~~

- [ ] **Step 4: Implement charts in deterministic order**

generate_charts creates output_dir and appends:

1. cluster_distribution bar chart from visual_data["cluster_distribution"];
2. rating_distribution histogram with bins 0.5 through 5.5 when data is nonempty;
3. one horizontal top-keyword chart per sorted cluster_id, named cluster_keywords_N;
4. cluster_projection scatter plot;
5. inertia_by_k and silhouette_by_k line charts when valid evaluation rows exist.

Every figure uses explicit title/x/y labels and figure size. Keyword bars reverse rank so rank 1 appears at the top. Scatter colors use tab10 and do not claim semantic axes. Evaluation charts use only rows where valid is true.

The return tuple preserves the order above and chart filenames contain only ASCII letters, digits, and underscores.

- [ ] **Step 5: Verify and commit charts**

Run:

~~~bash
uv run pytest tests/unit/test_charts.py -q
uv run ruff check src/reviewlens/export tests/unit/test_charts.py
uv run mypy src/reviewlens/export/charts.py tests/unit/test_charts.py
~~~

Expected: all commands pass and pytest closes every figure without warnings.

~~~bash
git add src/reviewlens/export tests/unit/test_charts.py
git commit -m "feat: add analysis chart generation"
~~~

### Task 10: Safe, atomic seven-sheet Excel export

**Files:**
- Create: src/reviewlens/export/safety.py
- Create: src/reviewlens/export/excel.py
- Modify: src/reviewlens/export/__init__.py
- Modify: src/reviewlens/models.py
- Create: tests/unit/test_export_safety.py
- Create: tests/integration/test_excel_export.py

**Interfaces:**
- Consumes: AnalysisResult and generate_charts.
- Produces: export_analysis(result, path=None, force=False), AnalysisResult.export_excel, ExportManifest.

- [ ] **Step 1: Write failing safety tests**

Create tests/unit/test_export_safety.py:

~~~python
import pandas as pd

from reviewlens.export.safety import safe_excel_value, sanitize_frame


def test_formula_like_strings_are_prefixed() -> None:
    assert safe_excel_value(" =HYPERLINK(\"https://bad\")")[0] == (
        "' =HYPERLINK(\"https://bad\")"
    )
    assert safe_excel_value("+SUM(1,1)")[0] == "'+SUM(1,1)"
    assert safe_excel_value("ordinary text")[0] == "ordinary text"


def test_structured_values_use_canonical_json() -> None:
    assert safe_excel_value({"b": 2, "a": 1})[0] == '{"a": 1, "b": 2}'
    assert safe_excel_value(("b", "a"))[0] == '["b", "a"]'


def test_final_excel_value_respects_cell_limit() -> None:
    value, truncated = safe_excel_value("=" + ("x" * 40_000))
    assert truncated is True
    assert isinstance(value, str)
    assert value.startswith("'=")
    assert len(value) == 32_767


def test_sanitize_frame_counts_truncated_cells() -> None:
    frame, count = sanitize_frame(pd.DataFrame({"value": ["x" * 40_000, "ok"]}))
    assert count == 1
    assert len(frame.loc[0, "value"]) == 32_767
~~~

- [ ] **Step 2: Run safety tests and observe the missing module**

Run:

~~~bash
uv run pytest tests/unit/test_export_safety.py -q
~~~

Expected: collection fails with ModuleNotFoundError for reviewlens.export.safety.

- [ ] **Step 3: Implement value safety**

Implement safe_excel_value(value) -> tuple[object, bool]:

- pd.NA, NaN, and None become None;
- dict uses json.dumps(..., ensure_ascii=False, sort_keys=True);
- list and tuple use JSON arrays;
- Path becomes str;
- strings whose first non-whitespace character is =, +, -, or @ receive a leading apostrophe;
- final strings are sliced to 32,767 characters;
- the boolean reports truncation.

Implement sanitize_frame by applying safe_excel_value cell by cell and returning a copied DataFrame plus total truncation count. Never mutate AnalysisResult frames.

- [ ] **Step 4: Write failing end-to-end export tests**

Create tests/integration/test_excel_export.py:

~~~python
from __future__ import annotations

import os
from pathlib import Path

import pytest
from openpyxl import load_workbook

from reviewlens import analyze_reviews
from reviewlens.exceptions import ExportError


def _source(tmp_path: Path, ratings: bool = True) -> Path:
    path = tmp_path / "reviews.csv"
    suffixes = [",2", ",1", ",2", ",5", ",4", ",5"] if ratings else [""] * 6
    texts = [
        "=pelayanan lambat antre",
        "antre lama pelayanan",
        "petugas lambat antre",
        "tempat bersih nyaman",
        "bersih rapi nyaman",
        "lokasi nyaman bersih",
    ]
    header = "text,rating\\n" if ratings else "text\\n"
    path.write_text(
        header + "".join(f"{text}{rating}\\n" for text, rating in zip(texts, suffixes)),
        encoding="utf-8",
    )
    return path


def test_export_has_ordered_sheets_embedded_images_and_pngs(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    output = tmp_path / "report.xlsx"
    manifest = result.export_excel(output)
    assert manifest.workbook_path == output.resolve()
    assert manifest.workbook_path.is_file()
    assert manifest.chart_paths
    workbook = load_workbook(output, data_only=False)
    assert workbook.sheetnames == [
        "metadata",
        "reviews",
        "clusters",
        "summary",
        "keywords",
        "visual_data",
        "visuals",
    ]
    headers = [cell.value for cell in workbook["reviews"][1]]
    review_column = headers.index("review_text") + 1
    assert workbook["reviews"].cell(2, review_column).value.startswith("'=")
    assert workbook["visuals"]._images


def test_export_refuses_existing_target_without_force(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    output = tmp_path / "report.xlsx"
    result.export_excel(output)
    with pytest.raises(ExportError, match="already exists"):
        result.export_excel(output)
    result.export_excel(output, force=True)


def test_rating_free_export_omits_rating_chart(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path, ratings=False), clusters=2)
    manifest = result.export_excel(tmp_path / "report.xlsx")
    assert not any(path.name == "rating_distribution.png" for path in manifest.chart_paths)


def test_force_export_restores_original_after_install_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    output = tmp_path / "report.xlsx"
    first = result.export_excel(output)
    original_workbook = output.read_bytes()
    original_charts = {
        path.name: path.read_bytes() for path in first.chart_paths
    }
    real_replace = os.replace
    failed = False

    def fail_once(source: str | Path, destination: str | Path) -> None:
        nonlocal failed
        if Path(destination) == output and not failed:
            failed = True
            raise OSError("simulated staged-workbook install failure")
        real_replace(source, destination)

    monkeypatch.setattr("reviewlens.export.excel.os.replace", fail_once)
    with pytest.raises(ExportError, match="report.xlsx"):
        result.export_excel(output, force=True)
    assert output.read_bytes() == original_workbook
    assert {
        path.name: path.read_bytes()
        for path in (tmp_path / "report_charts").iterdir()
    } == original_charts


def test_export_requires_xlsx_extension(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    with pytest.raises(ExportError, match=".xlsx"):
        result.export_excel(tmp_path / "report.xls")
~~~

- [ ] **Step 5: Run export tests and observe the missing method**

Run:

~~~bash
uv run pytest tests/integration/test_excel_export.py -q
~~~

Expected: tests fail because AnalysisResult has no export_excel method.

- [ ] **Step 6: Implement workbook tables and visuals**

Implement export_analysis in excel.py. Resolve a None path to Path.cwd() / f"{result.source_stem}-reviewlens.xlsx"; require .xlsx. Final chart directory is output.parent / f"{output.stem}_charts".

Before staging, reject an existing workbook or chart directory when force is false. Create a temporary sibling directory with tempfile.mkdtemp. Generate charts inside its chart directory. Sanitize every exported DataFrame and append one warning Diagnostic-equivalent metadata row when truncation occurs; do not mutate result.diagnostics.

Write with pandas.ExcelWriter(engine="openpyxl"):

- metadata is a key/value frame; serialize nested values canonically;
- reviews, clusters, summary, keywords use index=False;
- visual_data stacks each named table with a title row and two blank rows;
- visuals embeds ChartArtifact images in returned order, with a title cell before each image.

Apply bold colored headers, autofilters, A2 freeze panes, wrapped top-aligned body cells, and capped widths. Validate the closed staged workbook with openpyxl.load_workbook before installation.

- [ ] **Step 7: Implement atomic target installation**

Use this transaction:

1. stage workbook and charts completely;
2. if force is true, move existing final targets to unique sibling backup paths;
3. move the staged workbook and chart directory to final targets;
4. if any move fails, remove new partial targets and restore backups;
5. on success, remove backups and staging;
6. on any error, raise ExportError with the output basename and preserve the original exception as cause.

Use os.replace for files and Path.replace for directories only after ensuring the destination is absent. Keep the replacement operations in a small private transaction helper so the failure-injection test covers rollback. Return chart paths rewritten to the final chart directory.

- [ ] **Step 8: Add AnalysisResult.export_excel**

Add to AnalysisResult:

~~~python
def export_excel(
    self,
    path: str | Path | None = None,
    *,
    force: bool = False,
) -> ExportManifest:
    from reviewlens.export.excel import export_analysis

    return export_analysis(self, path, force=force)
~~~

Export export_analysis from reviewlens.export.

- [ ] **Step 9: Verify export safety, atomicity, and typing**

Run:

~~~bash
uv run pytest tests/unit/test_export_safety.py tests/integration/test_excel_export.py -q
uv run ruff check src/reviewlens/export src/reviewlens/models.py tests/unit/test_export_safety.py tests/integration/test_excel_export.py
uv run mypy src/reviewlens/export src/reviewlens/models.py tests/unit/test_export_safety.py tests/integration/test_excel_export.py
~~~

Expected: all commands pass; no workbook/chart artifacts remain outside pytest temporary directories.

- [ ] **Step 10: Commit reporting**

~~~bash
git add src/reviewlens/export src/reviewlens/models.py tests/unit/test_export_safety.py tests/integration/test_excel_export.py
git commit -m "feat: add safe Excel report export"
~~~

### Task 11: CLI and exit-code contract

**Files:**
- Create: src/reviewlens/cli.py
- Create: src/reviewlens/__main__.py
- Create: tests/integration/test_cli.py

**Interfaces:**
- Consumes: AnalysisConfig, analyze_reviews, AnalysisResult.export_excel, ReviewLensError hierarchy.
- Produces: main(argv=None) -> int, reviewlens analyze, and python -m reviewlens.

- [ ] **Step 1: Write failing CLI tests**

Create tests/integration/test_cli.py:

~~~python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "reviewlens", *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "reviews.csv"
    path.write_text(
        "text,rating\\n"
        "pelayanan lambat antre,2\\n"
        "antre lama pelayanan,1\\n"
        "petugas lambat antre,2\\n"
        "tempat bersih nyaman,5\\n"
        "bersih rapi nyaman,4\\n"
        "lokasi nyaman bersih,5\\n",
        encoding="utf-8",
    )
    return path


def test_cli_analyze_writes_requested_report(tmp_path: Path) -> None:
    source = _source(tmp_path)
    output = tmp_path / "report.xlsx"
    completed = _run(
        "analyze",
        str(source),
        "--clusters",
        "2",
        "--output",
        str(output),
    )
    assert completed.returncode == 0
    assert output.is_file()
    assert "Workbook:" in completed.stdout
    assert completed.stderr == ""


def test_cli_input_error_is_exit_two_without_traceback(tmp_path: Path) -> None:
    completed = _run("analyze", str(tmp_path / "missing.csv"))
    assert completed.returncode == 2
    assert "error:" in completed.stderr.lower()
    assert "Traceback" not in completed.stderr


def test_cli_analysis_failure_is_exit_one(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    source.write_text("text\\nsama\\nsama\\nsama\\n", encoding="utf-8")
    completed = _run("analyze", str(source))
    assert completed.returncode == 1
    assert "error:" in completed.stderr.lower()


def test_cli_quiet_suppresses_success_output(tmp_path: Path) -> None:
    source = _source(tmp_path)
    output = tmp_path / "report.xlsx"
    completed = _run(
        "analyze",
        str(source),
        "--clusters",
        "2",
        "--output",
        str(output),
        "--quiet",
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
~~~

- [ ] **Step 2: Run CLI tests and observe the missing module**

Run:

~~~bash
uv run pytest tests/integration/test_cli.py -q
~~~

Expected: subprocess fails because reviewlens.__main__ does not exist.

- [ ] **Step 3: Implement parser and config translation**

cli.py uses argparse with a required analyze subcommand and the approved options. Implement:

~~~python
def _cluster_count(value: str) -> int | Literal["auto"]:
    if value == "auto":
        return "auto"
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("clusters must be 'auto' or an integer") from error
    if number < 2:
        raise argparse.ArgumentTypeError("clusters must be at least 2")
    return number
~~~

Translate flags with dataclasses.replace:

- text/rating/language/clusters pass as analyze_reviews convenience arguments;
- ngram-range/min-df/max-features replace VectorizerConfig;
- stem/no-slang/no-stopwords replace PreprocessingConfig;
- evaluate replaces ClusteringConfig.evaluate_manual;
- output/force are export arguments.

The parser includes --version using reviewlens.__version__.

- [ ] **Step 4: Implement main and module entrypoint**

main(argv=None) returns 0 after printing selected k, workbook, and chart directory unless quiet. Catch InputError and ConfigurationError and return 2. Catch AnalysisError and ExportError and return 1. Print "error: MESSAGE" to stderr. When debug is true, call traceback.print_exc before returning the same code.

Create __main__.py:

~~~python
from reviewlens.cli import main

raise SystemExit(main())
~~~

- [ ] **Step 5: Verify CLI and installed entrypoint**

Run:

~~~bash
uv run pytest tests/integration/test_cli.py -q
uv run reviewlens --help
uv run python -m reviewlens --help
uv run ruff check src/reviewlens/cli.py src/reviewlens/__main__.py tests/integration/test_cli.py
uv run mypy src/reviewlens/cli.py src/reviewlens/__main__.py tests/integration/test_cli.py
~~~

Expected: tests pass; both help commands exit 0 and show the analyze subcommand.

- [ ] **Step 6: Commit CLI**

~~~bash
git add src/reviewlens/cli.py src/reviewlens/__main__.py tests/integration/test_cli.py
git commit -m "feat: add ReviewLens command line interface"
~~~

### Task 12: Synthetic examples and end-to-end reproducibility

**Files:**
- Create: examples/sample_reviews.csv
- Create: examples/sample_reviews.json
- Create: tests/conftest.py
- Create: tests/integration/test_examples.py

**Interfaces:**
- Consumes: public API, CLI, exporter.
- Produces: equivalent synthetic example inputs and integration proof for CSV, JSON list/object, repeated seeded runs, and the PRD report path semantics.

- [ ] **Step 1: Add the synthetic CSV**

Create examples/sample_reviews.csv:

~~~csv
reviewText,stars,createdAt,location
pelayanan gk cepat antre lama,2,2026-01-01,contoh-cabang-a
antre lama pelayanan lambat,1,2026-01-02,contoh-cabang-a
petugas lambat membuat antre,2,2026-01-03,contoh-cabang-a
tidak cepat antre panjang,2,2026-01-04,contoh-cabang-a
pelayanan lama antre terus,1,2026-01-05,contoh-cabang-a
tempat bersih nyaman rapi,5,2026-01-06,contoh-cabang-b
ruangan bersih dan sangat nyaman,5,2026-01-07,contoh-cabang-b
lokasi rapi bersih nyaman,4,2026-01-08,contoh-cabang-b
fasilitas bersih membuat nyaman,5,2026-01-09,contoh-cabang-b
suasana nyaman tempat terawat,4,2026-01-10,contoh-cabang-b
harga tiket mahal sekali,2,2026-01-11,contoh-cabang-c
tiket mahal namun fasilitas bagus,3,2026-01-12,contoh-cabang-c
harga cukup terjangkau keluarga,4,2026-01-13,contoh-cabang-c
promo tiket membuat harga murah,4,2026-01-14,contoh-cabang-c
biaya makanan mahal,2,2026-01-15,contoh-cabang-c
~~~

All names are explicitly fictional and no row may be replaced with legacy data.

- [ ] **Step 2: Add equivalent camelCase JSON**

Create examples/sample_reviews.json exactly:

~~~json
{
  "reviews": [
    {"reviewText": "pelayanan gk cepat antre lama", "stars": 2, "createdAt": "2026-01-01", "location": "contoh-cabang-a"},
    {"reviewText": "antre lama pelayanan lambat", "stars": 1, "createdAt": "2026-01-02", "location": "contoh-cabang-a"},
    {"reviewText": "petugas lambat membuat antre", "stars": 2, "createdAt": "2026-01-03", "location": "contoh-cabang-a"},
    {"reviewText": "tidak cepat antre panjang", "stars": 2, "createdAt": "2026-01-04", "location": "contoh-cabang-a"},
    {"reviewText": "pelayanan lama antre terus", "stars": 1, "createdAt": "2026-01-05", "location": "contoh-cabang-a"},
    {"reviewText": "tempat bersih nyaman rapi", "stars": 5, "createdAt": "2026-01-06", "location": "contoh-cabang-b"},
    {"reviewText": "ruangan bersih dan sangat nyaman", "stars": 5, "createdAt": "2026-01-07", "location": "contoh-cabang-b"},
    {"reviewText": "lokasi rapi bersih nyaman", "stars": 4, "createdAt": "2026-01-08", "location": "contoh-cabang-b"},
    {"reviewText": "fasilitas bersih membuat nyaman", "stars": 5, "createdAt": "2026-01-09", "location": "contoh-cabang-b"},
    {"reviewText": "suasana nyaman tempat terawat", "stars": 4, "createdAt": "2026-01-10", "location": "contoh-cabang-b"},
    {"reviewText": "harga tiket mahal sekali", "stars": 2, "createdAt": "2026-01-11", "location": "contoh-cabang-c"},
    {"reviewText": "tiket mahal namun fasilitas bagus", "stars": 3, "createdAt": "2026-01-12", "location": "contoh-cabang-c"},
    {"reviewText": "harga cukup terjangkau keluarga", "stars": 4, "createdAt": "2026-01-13", "location": "contoh-cabang-c"},
    {"reviewText": "promo tiket membuat harga murah", "stars": 4, "createdAt": "2026-01-14", "location": "contoh-cabang-c"},
    {"reviewText": "biaya makanan mahal", "stars": 2, "createdAt": "2026-01-15", "location": "contoh-cabang-c"}
  ]
}
~~~

Verify equivalence with:

~~~python
import json
from pathlib import Path

import pandas as pd

csv = pd.read_csv("examples/sample_reviews.csv")
payload = json.loads(Path("examples/sample_reviews.json").read_text(encoding="utf-8"))
assert len(payload["reviews"]) == len(csv) == 15
assert [row["reviewText"] for row in payload["reviews"]] == csv["reviewText"].tolist()
assert [row["stars"] for row in payload["reviews"]] == csv["stars"].tolist()
~~~

The committed JSON is static and human-readable; the check above verifies it but does not generate it.

- [ ] **Step 3: Write end-to-end example tests**

Create tests/conftest.py with repository_root and example_csv/example_json Path fixtures. Create tests/integration/test_examples.py:

~~~python
import json
from pathlib import Path

from openpyxl import load_workbook

from reviewlens import analyze_reviews


def test_seeded_example_is_reproducible(example_csv: Path) -> None:
    first = analyze_reviews(example_csv)
    second = analyze_reviews(example_csv)
    assert first.metadata["selected_k"] == second.metadata["selected_k"]
    assert first.reviews["cluster_id"].tolist() == second.reviews["cluster_id"].tolist()
    assert first.keywords.equals(second.keywords)
    assert first.clusters["representative_source_rows"].tolist() == (
        second.clusters["representative_source_rows"].tolist()
    )


def test_csv_and_json_have_same_manual_analysis(
    example_csv: Path,
    example_json: Path,
) -> None:
    csv_result = analyze_reviews(example_csv, clusters=3)
    json_result = analyze_reviews(example_json, clusters=3)
    assert csv_result.reviews["review_text"].tolist() == (
        json_result.reviews["review_text"].tolist()
    )
    assert csv_result.clusters["review_count"].tolist() == (
        json_result.clusters["review_count"].tolist()
    )


def test_json_list_and_object_have_same_manual_analysis(
    tmp_path: Path,
    example_json: Path,
) -> None:
    payload = json.loads(example_json.read_text(encoding="utf-8"))
    list_path = tmp_path / "reviews-list.json"
    list_path.write_text(
        json.dumps(payload["reviews"], ensure_ascii=False),
        encoding="utf-8",
    )
    object_result = analyze_reviews(example_json, clusters=3)
    list_result = analyze_reviews(list_path, clusters=3)
    assert object_result.reviews["review_text"].tolist() == (
        list_result.reviews["review_text"].tolist()
    )
    assert object_result.reviews["cluster_id"].tolist() == (
        list_result.reviews["cluster_id"].tolist()
    )


def test_prd_report_destination_is_temporary(
    tmp_path: Path,
    example_csv: Path,
) -> None:
    result = analyze_reviews(example_csv, clusters=3)
    output = tmp_path / "examples" / "output" / "report.xlsx"
    output.parent.mkdir(parents=True)
    result.export_excel(output)
    workbook = load_workbook(output, read_only=False)
    assert workbook.sheetnames == [
        "metadata",
        "reviews",
        "clusters",
        "summary",
        "keywords",
        "visual_data",
        "visuals",
    ]
~~~

- [ ] **Step 4: Verify examples through API and CLI**

Run:

~~~bash
uv run pytest tests/integration/test_examples.py -q
temporary_directory="$(mktemp -d)"
uv run reviewlens analyze examples/sample_reviews.csv --clusters 3 --output "$temporary_directory/report.xlsx"
test -f "$temporary_directory/report.xlsx"
test -d "$temporary_directory/report_charts"
rm -rf "$temporary_directory"
~~~

Expected: tests and CLI pass; the repository contains no generated workbook or chart directory.

- [ ] **Step 5: Commit examples and integration tests**

~~~bash
git add examples tests/conftest.py tests/integration/test_examples.py
git commit -m "test: add synthetic end-to-end examples"
~~~

### Task 13: Open-source documentation, license, and governance

**Files:**
- Modify: README.md
- Create: LICENSE
- Create: NOTICE
- Create: CONTRIBUTING.md
- Create: CODE_OF_CONDUCT.md
- Create: SECURITY.md
- Create: CHANGELOG.md
- Create: docs/api.md
- Create: docs/architecture.md
- Create: docs/data-format.md
- Create: tests/test_repository_contract.py

**Interfaces:**
- Consumes: final public CLI/API/contracts.
- Produces: complete user/developer documentation and all PRD-required policy artifacts with verified maintainer identity.

- [ ] **Step 1: Write a failing repository-contract test**

Create tests/test_repository_contract.py:

~~~python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "docs/api.md",
    "docs/architecture.md",
    "docs/data-format.md",
)


def test_required_open_source_documents_exist_without_placeholders() -> None:
    forbidden = ("TBD", "TODO", "FIXME", "fill in")
    for relative in REQUIRED:
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert content.strip(), relative
        assert not any(word.lower() in content.lower() for word in forbidden), relative


def test_readme_contains_required_user_sections() -> None:
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in (
        "## Installation",
        "## Quick start",
        "## Python API",
        "## Output",
        "## Architecture",
        "## Roadmap",
        "## Contributing",
    ):
        assert heading in content


def test_license_and_security_identity() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert "lisafronaldio123@gmail.com" in security
~~~

- [ ] **Step 2: Run the test and observe missing documents**

Run:

~~~bash
uv run pytest tests/test_repository_contract.py -q
~~~

Expected: failure on the first missing required file.

- [ ] **Step 3: Add canonical license, notice, conduct, and security policies**

- LICENSE is the unmodified canonical Apache License 2.0 text from https://www.apache.org/licenses/LICENSE-2.0.txt. It begins "Apache License" and "Version 2.0, January 2004" and includes all sections 1-9 plus the appendix.
- NOTICE contains:

~~~text
ReviewLens
Copyright 2026 Aldio Lisafron

Licensed under the Apache License, Version 2.0.
~~~

- CODE_OF_CONDUCT.md is the complete Contributor Covenant 2.1 text from https://www.contributor-covenant.org/version/2/1/code_of_conduct/ with enforcement contact lisafronaldio123@gmail.com.
- SECURITY.md states that 0.1.x is supported, requests private reports through GitHub private vulnerability reporting or lisafronaldio123@gmail.com, asks for impact/reproduction/version details, promises acknowledgment without an unverifiable response-time SLA, and forbids public disclosure before coordination.
- CONTRIBUTING.md contains uv installation, fork/branch workflow, uv sync --all-groups --locked, focused/full tests, Ruff, mypy, conventional commits, synthetic-data/privacy rules, and the clean-room prohibition.

Do not paraphrase the canonical license or Contributor Covenant legal text.

- [ ] **Step 4: Replace README with complete v0.1.0 usage documentation**

README must include:

- badges only for license/Python; omit CI badge until a remote workflow exists;
- scope and explicit non-goals;
- uv and pip installation commands;
- reviewlens analyze examples/sample_reviews.csv quick start;
- the advanced CLI example from the PRD using --language id and --clusters auto;
- the exact analyze_reviews(...), result.export_excel(...) Python API example;
- CSV/JSON aliases and optional rating behavior;
- seven workbook sheets and chart directory;
- reproducibility boundary (same input/config/ReviewLens/dependency versions);
- privacy/formula-safety statement;
- compact architecture pipeline;
- v0.2/v0.3/future roadmap from PRD;
- links to CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, CHANGELOG.md, and docs.

All shell/Python examples are copied into integration or doctest-style checks where feasible; no command may mention scraping or legacy paths.

- [ ] **Step 5: Add focused API, architecture, and data-format docs**

- docs/api.md lists every top-level export, analyze_reviews signature/precedence, AnalysisConfig sections, AnalysisResult frames, Diagnostic fields, exceptions, and export_excel behavior.
- docs/architecture.md maps every package directory to one responsibility, shows the side-effect boundary, documents auto-k and presentation relabeling, and states why SVD is visualization-only.
- docs/data-format.md gives complete CSV, JSON list, and JSON object examples; alias table; explicit override behavior; reserved output column names; blank/invalid rating behavior; UTF-8/delimiter rules; metadata preservation; and duplicate retention.
- CHANGELOG.md follows Keep a Changelog with an Unreleased section and 0.1.0 dated 2026-07-15. It lists ingestion, Indonesian preprocessing, TF-IDF/K-Means, deterministic interpretation, CLI/API, Excel/charts, tests, and OSS docs; it has no claim that the package was published.

- [ ] **Step 6: Verify documentation and commit**

Run:

~~~bash
uv run pytest tests/test_repository_contract.py -q
uv run ruff check tests/test_repository_contract.py
rg -n "TBD|TODO|FIXME|google-maps-review-analytics-tool|APIFY_TOKEN" README.md docs/api.md docs/architecture.md docs/data-format.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md CHANGELOG.md NOTICE LICENSE
~~~

Expected: pytest and Ruff pass; rg returns no matches.

~~~bash
git add README.md LICENSE NOTICE CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md CHANGELOG.md docs tests/test_repository_contract.py
git commit -m "docs: add open source project documentation"
~~~

### Task 14: Continuous integration and final release-candidate audit

**Files:**
- Create: .github/workflows/ci.yml
- Create: .github/dependabot.yml
- Create: .github/PULL_REQUEST_TEMPLATE.md
- Create: tests/integration/test_package_contract.py

**Interfaces:**
- Consumes: the complete package, examples, documentation, and Global Constraints.
- Produces: reproducible Linux quality gates, macOS/Windows smoke gates, automated dependency-update configuration, contributor checklist, and final local release-candidate evidence.

- [ ] **Step 1: Write the failing package/CI contract test**

Create tests/integration/test_package_contract.py:

~~~python
from __future__ import annotations

import tomllib
from pathlib import Path

import reviewlens

ROOT = Path(__file__).resolve().parents[2]


def test_package_metadata_and_version_are_consistent() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["name"] == "reviewlens"
    assert project["version"] == reviewlens.__version__ == "0.1.0"
    assert project["requires-python"] == ">=3.11"
    assert project["license"] == "Apache-2.0"
    assert project["scripts"]["reviewlens"] == "reviewlens.cli:main"


def test_ci_covers_supported_pythons_and_platform_smoke() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for value in ("3.11", "3.12", "3.13", "3.14"):
        assert value in workflow
    for value in ("ubuntu-latest", "macos-latest", "windows-latest", "production"):
        assert value in workflow


def test_runtime_has_no_out_of_scope_integrations() -> None:
    banned = ("apify", "dotenv", "mcp", "openai", "scrap")
    paths = [
        ROOT / "pyproject.toml",
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted((ROOT / "examples").glob("*")),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    assert not any(term in combined for term in banned)
~~~

- [ ] **Step 2: Run the contract and observe the missing workflow**

~~~bash
uv run pytest tests/integration/test_package_contract.py -q
~~~

Expected: metadata passes and CI coverage fails because .github/workflows/ci.yml does not exist.

- [ ] **Step 3: Add the exact CI workflow**

Create .github/workflows/ci.yml:

~~~yaml
name: CI

on:
  push:
    branches: [production]
  pull_request:
    branches: [production]

permissions:
  contents: read

jobs:
  quality:
    name: Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v8
        with:
          version: "0.11.28"
          enable-cache: true
          python-version: ${{ matrix.python-version }}
      - run: uv sync --all-groups --locked
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy src tests
      - run: uv run pytest --cov=reviewlens --cov-report=term-missing --cov-fail-under=90
      - run: uv build --no-sources
      - name: Verify wheel in an isolated environment
        shell: bash
        run: |
          uv venv .wheel-venv --python ${{ matrix.python-version }}
          uv pip install --python .wheel-venv/bin/python dist/*.whl
          .wheel-venv/bin/python -c "import reviewlens; assert reviewlens.__version__ == '0.1.0'"
          .wheel-venv/bin/reviewlens --help

  platform-smoke:
    name: ${{ matrix.os }} smoke
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v8
        with:
          version: "0.11.28"
          enable-cache: true
          python-version: "3.14"
      - run: uv sync --all-groups --locked
      - run: uv run python -c "import reviewlens; assert reviewlens.__version__ == '0.1.0'"
      - run: uv run reviewlens --help
      - name: Analyze the synthetic example
        shell: bash
        run: uv run reviewlens analyze examples/sample_reviews.csv --clusters 3 --output smoke-report.xlsx --quiet
~~~

Keep the workflow read-only except for ephemeral runner files. Do not add release, publish, deployment, secret, or GitHub-token permissions.

- [ ] **Step 4: Add Dependabot and the pull-request checklist**

Create .github/dependabot.yml:

~~~yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
~~~

Create .github/PULL_REQUEST_TEMPLATE.md:

~~~markdown
## Summary

Describe the user-visible or internal change.

## Verification

- [ ] Focused tests pass.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run mypy src tests` passes.
- [ ] `uv run pytest --cov=reviewlens --cov-fail-under=90` passes.
- [ ] No private, production, credential, or legacy-project data was added.
- [ ] Documentation and CHANGELOG were updated when behavior changed.
~~~

- [ ] **Step 5: Run all quality, behavior, and packaging gates**

Run from the repository root:

~~~bash
uv lock --check
uv sync --all-groups --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest --cov=reviewlens --cov-report=term-missing --cov-fail-under=90
uv build --no-sources
~~~

Expected: every command exits 0; pytest reports at least 90% line coverage; dist contains one 0.1.0 wheel and one source distribution.

- [ ] **Step 6: Verify the built wheel in an isolated environment**

~~~bash
temporary_directory="$(mktemp -d)"
uv venv "$temporary_directory/venv" --python 3.11
uv pip install --python "$temporary_directory/venv/bin/python" dist/reviewlens-0.1.0-py3-none-any.whl
"$temporary_directory/venv/bin/python" -c "import reviewlens; assert reviewlens.__version__ == '0.1.0'"
"$temporary_directory/venv/bin/reviewlens" --help
"$temporary_directory/venv/bin/reviewlens" analyze examples/sample_reviews.csv --clusters 3 --output "$temporary_directory/report.xlsx" --quiet
test -f "$temporary_directory/report.xlsx"
test -d "$temporary_directory/report_charts"
rm -rf "$temporary_directory" dist
~~~

Expected: clean installation, import, help, and end-to-end CLI analysis all pass without importing the source checkout.

- [ ] **Step 7: Run clean-room, artifact, and Git-state audits**

~~~bash
rg -ni "apify|dotenv|google-maps-review-analytics-tool|APIFY_TOKEN|Amanzi|https?://" pyproject.toml src tests examples || true
find . -type f \( -name '*.xlsx' -o -name '*.png' -o -name '.env' \) -not -path './.git/*' -print
git remote -v
git diff --check
git status --short
~~~

Inspect every rg match: only intentional synthetic formula-safety URLs in tests may remain. Expected: find prints nothing, git remote prints nothing, diff check passes, and status lists only the Task 14 files.

- [ ] **Step 8: Commit CI and final verification assets**

~~~bash
git add .github tests/integration/test_package_contract.py
git commit -m "chore: add continuous integration gates"
~~~

- [ ] **Step 9: Repeat the release-candidate audit after the commit**

~~~bash
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest --cov=reviewlens --cov-report=term-missing --cov-fail-under=90
git diff --check
git status --short
git log --oneline --decorate -15
git branch --show-current
git remote -v
~~~

Expected: all commands pass, the working tree is clean, branch is production, history contains the intentional conventional commits, and no remote is configured.

## Execution Completion Criteria

Implementation is complete only when all 14 task commits exist on production, the final verification commands pass from a clean checkout state, no generated reports or private/legacy artifacts are tracked, and repository identity matches Aldio Lisafron. Creating the GitHub repository, configuring origin, pushing, publishing a package, or releasing remains explicitly outside this plan and requires separate user authorization.
