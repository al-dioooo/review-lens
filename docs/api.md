# Python API

ReviewLens exposes a small, typed public surface from `reviewlens`. Analysis is
quiet and creates no output files; export is a separate explicit call.

## Top-level package exports

| Export | Purpose |
| --- | --- |
| `analyze_reviews` | Run the complete ingestion-through-analysis pipeline. |
| `AnalysisConfig` | Immutable configuration composed of six focused sections. |
| `AnalysisResult` | In-memory tables, metadata, diagnostics, and export method. |
| `Diagnostic` | Structured non-fatal information or warning. |
| `ExportManifest` | Final workbook path and ordered PNG chart paths. |
| `ReviewLensError` | Base class for expected public failures. |
| `InputError` | Invalid file, encoding, JSON shape, schema, or usable rows. |
| `ConfigurationError` | Invalid analysis configuration or convenience value. |
| `AnalysisError` | Data that cannot produce a valid feature/clustering result. |
| `ExportError` | Unsafe output request or failed artifact transaction. |

The package also exposes `reviewlens.__version__`, currently `"0.1.0"`, as its
version attribute. The ten names in the table above are the package's declared
`__all__` exports.

## `analyze_reviews`

```python
def analyze_reviews(
    file: str | Path,
    *,
    language: Literal["id"] | None = None,
    clusters: int | Literal["auto"] | None = None,
    text_column: str | None = None,
    rating_column: str | None = None,
    config: AnalysisConfig | None = None,
) -> AnalysisResult:
    ...
```

`file` is a CSV or JSON path. All other parameters are keyword-only.

Precedence is explicit:

1. `config=None` starts from a new `AnalysisConfig()` with Indonesian and
   automatic clustering defaults.
2. A supplied `config` provides every advanced setting.
3. Non-`None` `language` and `clusters` convenience arguments override
   `config.language` and `config.clustering.clusters`, respectively. The input
   configuration remains unchanged because every configuration object is
   immutable.
4. Non-`None` `text_column` and `rating_column` select normalized source columns
   directly and take precedence over automatic aliases. They are ingestion
   arguments rather than stored `AnalysisConfig` fields.

Version 0.1.0 accepts only `language="id"`. A manual cluster count must be an
integer satisfying `2 <= k < usable_review_count`; `"auto"` evaluates a bounded
candidate range and selects by cosine silhouette.

The function reads the named file and returns an `AnalysisResult`. It performs
no network access and writes no workbook, chart, cache, or model file.

## `AnalysisConfig`

`AnalysisConfig` and its nested dataclasses are frozen and slotted. Advanced
callers can import the nested types from `reviewlens.config`, or use
`dataclasses.replace` to derive a configuration from defaults.

| Section | Fields and defaults |
| --- | --- |
| Root | `language="id"` |
| `IngestionConfig` | `records_key=None`, `csv_delimiter=None` |
| `PreprocessingConfig` | `normalize_slang=True`, `remove_stopwords=True`, `stem=False`, `protected_negations=("tidak", "tak", "bukan", "belum", "jangan", "gak", "nggak", "enggak")`, `extra_slang=()`, `extra_stopwords=()` |
| `VectorizerConfig` | `ngram_range=(1, 2)`, `min_df=1`, `max_df=1.0`, `max_features=50_000`, `sublinear_tf=True` |
| `ClusteringConfig` | `clusters="auto"`, `random_state=42`, `n_init=20`, `max_iter=300`, `k_max=10`, `silhouette_sample_size=5_000`, `evaluate_manual=False` |
| `InterpretationConfig` | `keyword_count=10`, `representative_count=3` |
| `ProjectionConfig` | `components=2`, `sample_size=10_000`, `random_state=42` |

Every public configuration field is validated, including every nested section,
before the input file is loaded. Validation covers section and scalar types,
boolean fields, tuple and token shapes, supported language and delimiters, and
documented numeric bounds. Non-`None` convenience arguments are applied before
the final effective configuration is validated, so an explicit valid
`language=` or `clusters=` value can replace an invalid value in the immutable
base configuration. Invalid effective configuration always raises
`ConfigurationError`.

Example of a derived immutable configuration:

```python
from dataclasses import replace

from reviewlens import AnalysisConfig, analyze_reviews

base = AnalysisConfig()
config = replace(
    base,
    preprocessing=replace(base.preprocessing, stem=True),
    vectorizer=replace(base.vectorizer, max_features=20_000),
    clustering=replace(base.clustering, clusters=4),
)
result = analyze_reviews("reviews.csv", config=config)
```

`IngestionConfig.records_key` resolves a particular JSON-object array.
`csv_delimiter` bypasses delimiter detection. `extra_slang` is a tuple of
`(source, replacement)` pairs; `extra_stopwords` is a tuple of tokens.

Manual clustering normally leaves the public `evaluation` frame empty. Set
`evaluate_manual=True` to evaluate the bounded range as additional diagnostic
data while retaining the requested manual `k`.

## `AnalysisResult`

`AnalysisResult` is a frozen container, but its pandas frames and dictionaries
should be treated as caller-owned mutable data. Export sanitizes copies and does
not mutate any result component.
Preserved Python integers outside Excel's floating-point range remain integers
in `AnalysisResult` and are written as exact decimal strings only in the
sanitized workbook representation.

### `reviews`

One row for every source record, including excluded rows. Unrecognized input
columns are normalized and retained alongside these canonical/result columns:

| Column | Meaning |
| --- | --- |
| `source_row` | Stable one-based source order assigned before filtering. |
| `review_text` | Original review value under the canonical text name. |
| `rating` | Nullable numeric rating in the inclusive range 1–5. |
| `timestamp` | Preserved optional timestamp value; no semantic parsing. |
| `location` | Preserved optional location value. |
| `metadata` | Preserved optional metadata value. |
| `text_clean` | NFKC/lowercase text after URL, emoji, punctuation, and whitespace cleaning. |
| `text_model` | Tokens after configured slang, stopword, and stemming operations. |
| `included` | Whether the row was usable for modeling. |
| `drop_reason` | `"blank_review"` for excluded rows; otherwise missing. |
| `cluster_id` | Nullable presentation cluster ID; missing for excluded rows. |

### `clusters`

One row per presentation cluster with columns `cluster_id`, `review_count`,
`share`, `average_rating`, `rating_signal`, `theme`, `summary`, `keywords`,
`representative_reviews`, and `representative_source_rows`.

`rating_signal` is `complaint` below 3.0, `mixed` from 3.0 up to but excluding
4.0, `positive` at or above 4.0, and `unknown` when no valid rating is present.
Themes and summaries are deterministic and extractive; they are not generated
by an AI service.

### `summary`

A tidy dataset-level table with `category`, `name`, `value`, and `details`.
Rows cover retained input, selected `k`, the largest cluster, overall rating
when available, and highest/lowest rated cluster highlights. Rating-free input
instead includes a `rating_unavailable` row.

### `keywords`

A tidy table with `cluster_id`, one-based `rank`, `term`, and mean TF-IDF
`score`. Ranking uses descending score and ascending term for a numerical tie.

### `evaluation`

Candidate cluster diagnostics with `k`, `inertia`, `silhouette`, `valid`, and
`reason`. Automatic mode records candidates from 2 through
`min(k_max, usable_review_count - 1)`. Invalid candidates remain visible with a
reason and are excluded from selection.

### `visual_data`

A dictionary of the exact frames used to produce charts:

| Key | Columns |
| --- | --- |
| `cluster_distribution` | `cluster_id`, `review_count` |
| `rating_distribution` | `source_row`, `rating` |
| `keywords` | `cluster_id`, `rank`, `term`, `score` |
| `projection` | `source_row`, `x`, `y`, `cluster_id` |
| `evaluation` | `k`, `inertia`, `silhouette`, `valid`, `reason` |

The rating frame is empty when no valid rating exists. The evaluation frame is
empty for manual clustering unless manual range evaluation is enabled.

### Metadata and remaining fields

`metadata` contains `reviewlens_version`, `dependency_versions`, effective
`config`, `source_name`, `source_sha256`, UTC `generated_at`, `input_count`,
`retained_count`, `excluded_count`, `selected_k`, and `diagnostic_counts`. It
contains the input basename and content hash, never the absolute source path.

`diagnostics` is a tuple of `Diagnostic` objects. `source_stem` supplies the
default export filename prefix.

## Diagnostics

```text
Diagnostic(
    severity: Literal["info", "warning"],
    code: str,
    message: str,
    count: int | None = None,
)
```

Diagnostics describe recoverable conditions such as invalid ratings, excluded
blank reviews, one-dimensional projection, unavailable ratings, or export-time
cell truncation. `code` is stable for programmatic handling; `message` is for
people; `count` reports affected rows or values when meaningful. Fatal
conditions raise exceptions instead of creating error-severity diagnostics.

## Exceptions

All expected public failures inherit from `ReviewLensError`:

```text
ReviewLensError
├── InputError
├── ConfigurationError
├── AnalysisError
└── ExportError
```

- Catch `InputError` for missing/unsupported files, unreadable encoding, CSV
  NUL characters, malformed or decoder-limited JSON, non-scalar review text,
  schema ambiguity/collisions, or no usable rows.
- Catch `ConfigurationError` for an invalid effective configuration field,
  section type, collection shape, token, boolean, delimiter, or numeric bound.
- Catch `AnalysisError` for data-dependent feasibility failures after valid
  configuration and input have been established. For example, `min_df` or
  `max_df` values that leave no terms for a particular dataset raise
  `AnalysisError`, as do empty/distinguishability-limited features or an
  impossible clustering result.
- Catch `ExportError` for non-`.xlsx` destinations, protected existing targets,
  staging/validation failures, or unsuccessful installation/rollback.

Catch `ReviewLensError` when an application wants one boundary for all expected
user-facing failures. Unexpected programming or dependency errors are not
wrapped universally.

## Excel export

```python
manifest = result.export_excel(path=None, force=False)
```

With `path=None`, export targets `<source-stem>-reviewlens.xlsx` in the process
working directory. A supplied path must end in `.xlsx`. Charts are installed in
`<output-stem>_charts/` beside the workbook.

The method returns:

```text
ExportManifest(
    workbook_path: Path,
    chart_paths: tuple[Path, ...],
)
```

The workbook contains `metadata`, `reviews`, `clusters`, `summary`, `keywords`,
`visual_data`, and `visuals` in that order. Chart paths preserve generation
order. Existing workbook or chart-directory targets raise `ExportError` unless
`force=True` is explicit.

Export generates all charts and workbook content in a temporary sibling
directory, validates the workbook and embedded images, and then installs the
workbook and chart directory as one protected transaction. A failed operation
removes staged artifacts and attempts to restore pre-existing targets.

User-controlled formula-like strings are apostrophe-prefixed, nested values are
serialized deterministically for Excel, and stored strings are capped at 32,767
characters. Truncation is reported in exported metadata without changing the
in-memory `AnalysisResult`.

See [Data formats](data-format.md), [Architecture](architecture.md), and the
[project README](../README.md) for the surrounding contracts.
