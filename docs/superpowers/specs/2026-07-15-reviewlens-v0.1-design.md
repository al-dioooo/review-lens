# ReviewLens v0.1.0 Design Specification

- **Status:** Approved in conversation on 2026-07-15
- **Product source:** [`PRD.md`](../../../PRD.md)
- **Repository:** `https://github.com/al-dioooo/review-lens`
- **Default branch:** `production`

## Purpose

ReviewLens v0.1.0 is a clean-room, open-source Python toolkit for turning user-provided review datasets into reproducible Indonesian-language cluster analysis. It provides the same analysis pipeline through a Python API and a command-line interface, then exports transparent tabular results and charts without scraping, hosted services, external AI APIs, or model downloads.

The release is a reusable package rather than a research script. Its primary success criterion is that a developer, researcher, or business user can analyze a supported CSV or JSON dataset locally and inspect how every cluster, keyword, theme, summary, and chart was produced.

## Approved Product Decisions

- Implement the complete working v0.1.0 scope, not a scaffold-only repository.
- Use a clean-room implementation. The legacy project may inform observable requirements and known pitfalls, but none of its source code, datasets, output artifacts, credentials, or project-specific terms may be copied or mechanically translated.
- License ReviewLens under Apache-2.0 with Aldio Lisafron as the copyright holder and maintainer.
- Use GitHub identity `al-dioooo`, maintainer email `lisafronaldio123@gmail.com`, and project URL `https://github.com/al-dioooo/review-lens` in package and project metadata.
- Initialize the local repository on `production`. Do not add a Git remote, push, publish a package, or mutate GitHub state as part of v0.1.0 implementation.
- Target datasets of up to 50,000 reviews on a typical developer laptop. This is a design target, not a hard execution-time guarantee.
- Support Python 3.11 through 3.14 on Linux, macOS, and Windows.
- Use deterministic extractive cluster interpretation and silhouette-based automatic cluster selection.
- Commit only synthetic Indonesian example data.

## Scope

### Included

- CSV ingestion.
- JSON-list ingestion.
- JSON-object ingestion when review records appear under a supported array key.
- Column-name normalization and canonical review schema resolution.
- Indonesian-first cleaning, slang normalization, stopword removal, and optional Sastrawi stemming.
- Sparse TF-IDF features with configurable n-grams, minimum document frequency, and maximum feature count.
- Manual K-Means cluster count.
- Automatic K evaluation and selection using cosine silhouette, with inertia retained as an elbow diagnostic.
- Deterministic cluster keywords, themes, summaries, rating signals, and representative reviews.
- Two-dimensional TruncatedSVD projection for visualization only.
- Excel reports with data, interpretation, chart source tables, and embedded charts.
- PNG chart files adjacent to the workbook.
- A Python API and `reviewlens analyze` CLI.
- Unit, integration, CLI, export, packaging, and cross-platform smoke tests.
- Professional open-source documentation and repository policy files.

### Excluded

- Google Maps or other review scraping.
- Apify and all scraper credentials or environment variables.
- Hosted dashboards or SaaS behavior.
- HTML reports.
- External AI APIs, local generative models, and runtime model downloads.
- Multilingual processing beyond `language="id"`.
- Plugin architecture, custom analyzer protocols, and MCP servers.
- PyPI publishing, GitHub repository creation, remote configuration, pushing, and release creation.

Deferred features are not represented by empty modules in v0.1.0.

## Repository Foundation

The repository uses a focused `src/` package layout:

```text
review-lens/
├── .github/
│   ├── workflows/ci.yml
│   ├── dependabot.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── data-format.md
│   └── superpowers/
│       ├── plans/
│       └── specs/
├── examples/
│   ├── sample_reviews.csv
│   └── sample_reviews.json
├── src/reviewlens/
│   ├── __init__.py
│   ├── __main__.py
│   ├── api.py
│   ├── cli.py
│   ├── config.py
│   ├── exceptions.py
│   ├── models.py
│   ├── py.typed
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── csv_loader.py
│   │   ├── json_loader.py
│   │   ├── normalization.py
│   │   └── schema.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── cleaner.py
│   │   ├── indonesian.py
│   │   └── slang.py
│   ├── resources/
│   │   └── slang_id.json
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── clustering.py
│   │   ├── evaluation.py
│   │   ├── interpretation.py
│   │   ├── projection.py
│   │   └── vectorizer.py
│   └── export/
│       ├── __init__.py
│       ├── charts.py
│       ├── excel.py
│       └── safety.py
├── tests/
│   ├── integration/
│   ├── unit/
│   └── conftest.py
├── .editorconfig
├── .gitignore
├── .python-version
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── NOTICE
├── PRD.md
├── README.md
├── SECURITY.md
├── pyproject.toml
└── uv.lock
```

Files are divided by responsibility rather than by a generic helper layer. HTML, scraper, environment-secret, dashboard, AI, and plugin modules are absent.

## Packaging and Tooling

- Distribution name: `reviewlens`.
- Import package: `reviewlens`.
- Console command: `reviewlens`.
- Initial version: `0.1.0`.
- Python requirement: `>=3.11`.
- Build backend: `uv_build>=0.11.28,<0.12` with `build-backend = "uv_build"`.
- Package workflow: uv with a committed `uv.lock`.
- Runtime dependencies: pandas, NumPy, SciPy, scikit-learn, Sastrawi, matplotlib, openpyxl, and Pillow.
- Development dependencies: pytest, pytest-cov, Ruff, and mypy.
- The project declares minimum compatible runtime versions and uses the lockfile for exact development and CI resolution. Upper bounds are added only when an upstream incompatibility is demonstrated; the build backend retains its documented compatible-series upper bound.
- Matplotlib uses its non-interactive `Agg` backend for CLI, test, and server-safe rendering.
- No NLTK, dotenv, Apify, CLI framework, logging framework, or generative-model dependency is added.

The native uv backend is appropriate because ReviewLens is a pure-Python package and the backend directly supports the selected `src/` structure. Package builds must produce both a wheel and source distribution.

## Public Interfaces

### Python API

The top-level package exports `analyze_reviews`, `AnalysisConfig`, `AnalysisResult`, `Diagnostic`, `ExportManifest`, and the public exception types.

The primary function has this interface:

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
    """Analyze one supported review dataset without writing output files."""
```

`None` means use the configuration value; with no supplied configuration, the effective defaults are `language="id"` and `clusters="auto"`. Non-`None` convenience arguments override the corresponding configuration fields.

`AnalysisConfig` is an immutable dataclass composed of immutable ingestion, preprocessing, vectorizer, clustering, interpretation, and projection configurations. It is the supported way to change advanced behavior from Python.

`AnalysisResult` contains:

- normalized review rows, including excluded rows and their exclusion reasons;
- one row per interpreted cluster;
- dataset-level summary rows;
- tidy keyword scores;
- cluster-evaluation rows when evaluation ran;
- chart-source tables;
- reproducibility metadata;
- structured diagnostics.

It exposes:

```python
def export_excel(
    self,
    path: str | Path | None = None,
    *,
    force: bool = False,
) -> ExportManifest:
    """Export this analysis and return the paths of completed artifacts."""
```

Analysis itself performs no output writes. `ExportManifest` reports the final workbook path and ordered chart paths.

### CLI

The supported command is:

```text
reviewlens analyze INPUT
```

It supports the PRD options plus explicit reproducibility and preprocessing controls:

- `--text-column NAME`
- `--rating-column NAME`
- `--language id`
- `--clusters auto|N`
- `--output PATH`
- `--ngram-range MIN MAX`
- `--min-df N`
- `--max-features N`
- `--stem`
- `--no-slang`
- `--no-stopwords`
- `--evaluate` for evaluation alongside a manually selected cluster count
- `--force`
- `--quiet`
- `--debug`

The CLI is implemented with `argparse` and delegates to the public API rather than maintaining a second pipeline. `python -m reviewlens` delegates to the same CLI.

## Canonical Input Contract

### File handling

- CSV accepts UTF-8 and UTF-8 with BOM.
- CSV dialect detection considers comma, semicolon, tab, and pipe delimiters, then falls back to comma when detection is inconclusive.
- JSON must be UTF-8.
- A top-level JSON list must contain only objects.
- A top-level JSON object may contain the records list under `reviews`, `data`, `items`, or `results`.
- When more than one supported JSON key contains a list, ingestion fails unless an explicit `records_key` is supplied through `AnalysisConfig`.
- Malformed records are never silently skipped.

### Column normalization

Source column names are normalized to snake case by separating case transitions and replacing runs of punctuation or whitespace with one underscore. A normalization collision is an input error; columns are never silently discarded.

Canonical fields and automatic aliases are:

| Canonical field | Accepted aliases after normalization |
| --- | --- |
| `review_text` | `review_text`, `text`, `review`, `content`, `review_body` |
| `rating` | `rating`, `stars`, `score`, `star_rating` |
| `timestamp` | `timestamp`, `created_at`, `date`, `review_date` |
| `location` | `location`, `place`, `venue`, `address` |
| `metadata` | `metadata`, `meta` |

Explicit text and rating column arguments take precedence. Without an explicit override, multiple present aliases for the same canonical field are an error. Unrecognized columns are retained.

### Row validation

- A review-text field is required for the dataset.
- Null, empty, or cleaning-empty review text excludes that row from modeling. The row remains in the public review table with `included=False` and a stable `drop_reason`.
- Ratings are optional and must parse as numeric values from 1 through 5 inclusive.
- Invalid or out-of-range ratings become missing values and emit a counted diagnostic rather than excluding the review.
- Timestamps and locations are preserved without semantic parsing in v0.1.0.
- Nested metadata is preserved in memory and serialized to canonical, key-sorted JSON for Excel.
- Exact duplicate reviews are retained by default because duplicate frequency can be analytically meaningful.
- A stable source-row number is assigned before filtering and is used for deterministic tie-breaking.

## Indonesian Preprocessing

The pipeline preserves the original `review_text` and derives `text_clean` and `text_model`.

Processing order is fixed:

1. Unicode NFKC normalization.
2. Lowercase conversion.
3. URL removal.
4. Emoji removal.
5. Punctuation replacement with spaces.
6. Whitespace normalization.
7. Token-aware Indonesian slang normalization.
8. Tokenization.
9. Sastrawi stopword removal, excluding the package's protected negation set.
10. Optional Sastrawi stemming.
11. Token reassembly and final whitespace normalization.

The protected negation set is `tidak`, `tak`, `bukan`, `belum`, `jangan`, `gak`, `nggak`, and `enggak`; slang variants normalized to one of these forms remain protected. The slang dictionary is newly authored for ReviewLens, stored as package data, covered by Apache-2.0, and may be extended through `AnalysisConfig`. `AnalysisConfig` also accepts extra stopwords without defining venue-specific defaults. Neither resource is copied from the legacy project.

Basic cleaning, slang normalization, and stopword removal are enabled by default. Stemming is available but disabled by default for traceability and to avoid unnecessary loss of readable keyword forms. No resource is downloaded at runtime.

## Feature Extraction

The default TF-IDF configuration is:

- `ngram_range=(1, 2)`
- `min_df=1`
- `max_df=1.0`
- `max_features=50_000`
- `sublinear_tf=True`
- deterministic vocabulary ordering provided by scikit-learn for identical input and configuration

The resulting sparse matrix is the direct K-Means input. Dimensionality reduction is not silently inserted into the clustering pipeline.

An empty vocabulary or fewer than two distinguishable feature vectors is an analysis error with guidance to retain more reviews, disable an aggressive preprocessing option, or adjust vectorizer thresholds.

## Cluster Evaluation and Selection

K-Means uses these defaults:

- `random_state=42`
- `n_init=20`
- `max_iter=300`

For automatic selection, candidate values are the integers from 2 through the smallest of 10 and `usable_review_count - 1`. Automatic analysis requires at least three usable reviews. Each candidate is fitted once and evaluated with cosine silhouette; silhouette computation uses at most 5,000 deterministically sampled rows. Inertia is recorded for elbow inspection but does not choose the cluster count.

A candidate that produces fewer distinct labels than requested or cannot produce a silhouette score is recorded as invalid and excluded from selection. The candidate with the greatest silhouette score wins. An exact numerical tie selects the smaller `k`. The already-fitted winning model is retained rather than refitted.

If every candidate is invalid, analysis fails with a diagnostic explaining the likely degenerate or insufficient dataset. Manual cluster counts must satisfy `2 <= k < usable_review_count`; the fitted model must produce the requested number of nonempty labels. Manual analysis evaluates only the chosen model unless the caller or CLI enables the evaluation range.

## Cluster Interpretation

Interpretation is deterministic and extractive:

- Term importance is the mean TF-IDF weight among reviews in a cluster.
- Keywords are ordered by descending score and then ascending term for numerical ties.
- The default keyword count is 10 per cluster.
- The theme joins the first three ranked terms into a concise display label.
- Three representative reviews are selected by ascending cosine distance to the cluster centroid, with source-row order as the tie-breaker.
- Average rating ignores missing values.
- Rating signal is `complaint` below 3.0, `mixed` from 3.0 up to but excluding 4.0, `positive` at or above 4.0, and `unknown` when the cluster has no valid ratings.

Cluster prose uses fixed Indonesian templates. With ratings, the template reports cluster size, dataset share, average rating, and top terms. Without ratings, it omits rating language. The wording never claims causality, sentiment beyond the documented rating signal, or generative understanding.

Presentation cluster IDs are assigned after fitting by sorting clusters by descending review count, then ascending theme, then original model label. IDs are consecutive integers starting at zero. This does not promise stable IDs when the dataset changes.

Dataset-level summary rows include input and retained counts, selected `k`, overall rating when present, largest themes, lowest-rated complaint themes, and highest-rated positive themes. Without valid ratings, the summary falls back to prevalence-based highlights and states that rating-based insights were unavailable.

## Two-Dimensional Projection

Projection uses the sparse TF-IDF matrix and TruncatedSVD with two components and seed 42. At most 10,000 reviews are sampled deterministically for chart rendering. Projection never affects cluster fitting or interpretation.

If the feature space has only one usable dimension, the chart uses that dimension as x and zero as y, and records a diagnostic. Projection output contains source-row number, x, y, and presentation cluster ID.

## Data Flow

```text
file
  -> load records
  -> normalize columns and resolve schema
  -> validate rows and preserve diagnostics
  -> preprocess included review text
  -> build sparse TF-IDF features
  -> evaluate/select or validate manual k
  -> fit/retain K-Means model
  -> relabel and interpret clusters
  -> build projection and chart-source tables
  -> return AnalysisResult
  -> explicitly export workbook and PNG charts
```

Each stage consumes and produces a typed result. The CLI owns progress presentation; library calls remain quiet and expose structured diagnostics on `AnalysisResult`.

## Excel and Chart Contract

The workbook contains exactly these ordered sheets:

1. `metadata`
2. `reviews`
3. `clusters`
4. `summary`
5. `keywords`
6. `visual_data`
7. `visuals`

### Sheet meanings

- `metadata`: package and dependency versions, effective configuration, source basename, input SHA-256, an ISO 8601 UTC generation timestamp, counts, selected cluster count, and diagnostic totals. It does not expose the absolute input path.
- `reviews`: all normalized source rows, inclusion state, exclusion reason, processed text, normalized rating, and cluster assignment for included rows.
- `clusters`: one row per presentation cluster with size, share, average rating, rating signal, theme, deterministic summary, keywords, and representative review text/source-row references.
- `summary`: tidy dataset metrics and selected prevalence/rating insights.
- `keywords`: one row per cluster, rank, term, and TF-IDF score.
- `visual_data`: named table blocks that reproduce every chart.
- `visuals`: embedded charts in deterministic order.

Generated PNG charts are:

- cluster distribution;
- rating distribution when at least one valid rating exists;
- top-keyword chart for each cluster;
- two-dimensional cluster projection;
- inertia by `k` when evaluation data exists;
- silhouette by `k` when evaluation data exists.

The default workbook path is `<input-stem>-reviewlens.xlsx` in the process working directory. PNG files are written to `<output-stem>_charts/` beside the workbook. Existing workbook or chart-directory targets are rejected unless `force=True` or `--force` is set.

The exporter stages all new files in a temporary sibling directory, closes and validates the workbook, then moves successful artifacts into place. On failure it removes staged files and leaves pre-existing targets unchanged.

Any user-controlled string whose first non-whitespace character is `=`, `+`, `-`, or `@` is prefixed with a single apostrophe before Excel serialization to prevent formula injection. Escaping occurs before length enforcement, and the final stored string never exceeds Excel's 32,767-character cell limit. Truncation affects only the export representation and produces a counted diagnostic; the in-memory analysis result retains the complete value.

## Errors and Diagnostics

The public exception hierarchy is:

- `ReviewLensError`
  - `InputError`
  - `ConfigurationError`
  - `AnalysisError`
  - `ExportError`

Expected invalid user input raises one of these exceptions with an actionable message and no partial output. Structured diagnostics use a stable code, human-readable message, `info` or `warning` severity, and optional affected-row count. Fatal conditions are represented by exceptions rather than error-severity diagnostics.

The CLI maps argument and input/configuration errors to exit code 2 and analysis/export failures to exit code 1. Success is exit code 0. Normal failures print concise stderr messages without tracebacks; `--debug` includes a traceback. `--quiet` suppresses progress and informational output but not errors.

Missing ratings, invalid individual ratings, excluded blank reviews, one-dimensional projection, skipped rating charts, and export truncation are warnings rather than fatal errors. Malformed files, schema ambiguity, normalization collisions, no usable reviews, empty vocabulary, impossible clustering, and unsafe output replacement are fatal.

## Security and Privacy

- Analysis has no network behavior.
- The package reads only the explicitly supplied input and writes only during explicit export.
- No environment secrets or credential files are required.
- Absolute input paths are excluded from report metadata.
- Input content is not logged by default.
- Excel formula injection is neutralized.
- Synthetic examples contain no real people, businesses, URLs, or copied reviews.
- Generated workbooks, chart directories, local datasets, environments, caches, and secrets are ignored by Git except for explicitly named synthetic example inputs.
- `SECURITY.md` directs private reports to the verified maintainer email and the repository's GitHub private-vulnerability reporting channel when available.

## Performance Boundaries

ReviewLens is designed for in-memory analysis of up to 50,000 reviews on a typical laptop. Memory is bounded primarily through the sparse matrix representation, 50,000-feature TF-IDF cap, 5,000-row silhouette sample, and 10,000-row projection sample. CSV and JSON loaders may still materialize the complete dataset, and v0.1.0 does not promise streaming or out-of-core behavior.

The documentation states these limits and recommends lowering `max_features`, specifying `k`, or disabling manual evaluation for constrained machines. CI verifies representative correctness, not a hardware-specific timing SLA.

## Testing Strategy

### Unit tests

- CSV dialect and encoding handling.
- Every supported JSON shape and ambiguous-record-key rejection.
- Snake-case normalization, alias resolution, explicit overrides, and collision failures.
- Blank review retention/exclusion metadata and rating coercion.
- Unicode cleaning, URLs, emoji, punctuation, whitespace, slang, negation preservation, stopwords, and optional stemming.
- TF-IDF configuration and empty-vocabulary errors.
- Candidate-range bounds, silhouette selection, tie-breaking, invalid candidates, manual `k`, and seed reproducibility.
- Keyword scores, cluster relabeling, theme construction, summary templates, rating signals, and centroid-nearest examples.
- Projection sampling and one-dimensional fallback.
- Formula escaping, cell-length handling, overwrite prevention, atomic staging, sheet order, and optional rating/evaluation charts.
- Exception and diagnostic contracts.

### Integration tests

- Analyze the synthetic CSV through the Python API and export a workbook plus charts in a temporary directory.
- Analyze each JSON shape and compare the normalized semantic result with the CSV input.
- Assert workbook sheet names, headers, key metrics, embedded images, chart files, and reproducibility metadata without committing a binary golden workbook.
- Run rating-free input and verify successful omission of rating-dependent output.
- Run the installed CLI as a subprocess and verify stdout/stderr and exit codes.
- Repeat a seeded analysis and assert selected `k`, presentation labels, keywords, and representative source rows are identical.

The PRD's `examples/output/report.xlsx` path is treated as an illustrative integration-test destination. Tests create an equivalent `report.xlsx` inside a temporary directory and never commit a generated binary workbook.

### Quality gates

- Ruff lint passes.
- Ruff format check passes.
- Mypy passes for package and tests.
- Pytest line coverage is at least 90%.
- Wheel and source distribution build successfully with `uv build --no-sources`.
- The built wheel installs into an isolated environment, imports, and exposes the CLI.

GitHub Actions runs the full quality gates on Ubuntu for Python 3.11, 3.12, 3.13, and 3.14. Windows and macOS run Python 3.14 smoke tests covering installation, import, CLI help, and the small end-to-end example. Workflows trigger for pull requests and pushes targeting `production`.

## Documentation and Governance

`README.md` includes the product introduction, supported scope, installation with uv and pip, CLI and API quick starts, sample outputs, architecture summary, data contract, reproducibility notes, privacy guidance, roadmap, and links to contribution and security policies.

Additional documentation covers:

- `docs/data-format.md`: canonical fields, aliases, JSON shapes, validation, and examples.
- `docs/api.md`: public functions, types, exceptions, diagnostics, and export behavior.
- `docs/architecture.md`: module boundaries, pipeline, deterministic algorithms, and extension constraints.
- `CONTRIBUTING.md`: uv setup, tests, formatting, types, conventional commits, and clean-room rule.
- `CODE_OF_CONDUCT.md`: Contributor Covenant behavior and enforcement contact.
- `SECURITY.md`: supported versions and private reporting routes.
- `CHANGELOG.md`: Keep a Changelog structure with the 0.1.0 feature set.
- `NOTICE`: Apache attribution for Aldio Lisafron and ReviewLens.

Dependabot tracks GitHub Actions and Python dependency updates. No automated release or publish workflow is included.

## Acceptance Criteria

The v0.1.0 implementation is complete when all of the following are true:

1. The repository is on `production`, has conventional local commits, and has no configured remote.
2. `uv sync --all-groups --locked` succeeds on the development machine.
3. Ruff lint and format checks pass.
4. Mypy passes.
5. Pytest passes with at least 90% line coverage.
6. `uv build --no-sources` creates a wheel and source distribution.
7. The built wheel installs and exposes both `import reviewlens` and the `reviewlens` command.
8. The documented API call analyzes `examples/sample_reviews.csv` without writing until `export_excel` is called.
9. The documented CLI call analyzes the same input and creates the seven-sheet workbook plus required PNG charts.
10. Repeated seeded runs produce the same selected cluster count, presentation labels, ranked keywords, and representative source rows.
11. CSV, JSON list, and JSON object inputs are covered by integration tests.
12. Missing ratings succeed with explicit diagnostics and no rating-dependent chart.
13. Unsafe spreadsheet text is escaped and pre-existing output is protected without `--force`.
14. README and every required open-source policy file are present and contain no placeholders.
15. The repository contains no legacy source, real review data, generated report, secret, scraper dependency, HTML exporter, AI integration, dashboard, plugin scaffold, or MCP code.

The deterministic-results guarantee applies to repeated runs with the same input, ReviewLens version, dependency versions, configuration, and supported execution environment. Report timestamps and filesystem paths are not part of the deterministic comparison, and byte-identical workbooks are not promised across dependency versions.

## Implementation Constraint

Implementation proceeds test-first from this specification. The legacy project is not an implementation source. When behavior is uncertain, the approved PRD and this specification control; any newly discovered material product ambiguity returns to user review rather than being resolved by copying legacy behavior.
