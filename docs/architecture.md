# Architecture

ReviewLens is one typed, deterministic analysis pipeline shared by the Python
API and CLI. Package boundaries follow data responsibilities, and output writes
are isolated behind `AnalysisResult.export_excel(...)`.

## Design boundaries

- Inputs are user-supplied CSV or JSON files.
- Analysis runs locally without network calls, runtime downloads, credentials,
  or hidden model services.
- Sparse TF-IDF is the clustering feature space.
- Interpretation is deterministic and extractive.
- Analysis returns inspectable pandas frames and structured diagnostics.
- Only explicit export writes a workbook and PNG files.

The v0.1 package contains no scraper, hosted dashboard, HTML exporter,
generative model, plugin protocol, or MCP implementation.

## Package responsibility map

Every package directory under `src/reviewlens` has one primary responsibility:

| Package directory | Responsibility |
| --- | --- |
| `src/reviewlens/` | Public contract, immutable configuration/result models, CLI boundary, and end-to-end orchestration. |
| `src/reviewlens/ingestion/` | Read CSV/JSON, hash the input, normalize columns, resolve aliases, coerce ratings, and preserve source-row diagnostics. |
| `src/reviewlens/preprocessing/` | Produce deterministic cleaned/model text with Indonesian slang, protected negations, stopwords, and optional stemming. |
| `src/reviewlens/resources/` | Ship newly authored, static package data used by preprocessing without runtime downloads. |
| `src/reviewlens/analysis/` | Build sparse features, evaluate/select K-Means, interpret/relabel clusters, and create visualization-only projection data. |
| `src/reviewlens/export/` | Sanitize user-controlled values, render deterministic charts, build/validate Excel, and install artifacts transactionally. |

The root modules are deliberately narrow:

| Module | Role |
| --- | --- |
| `__init__.py` | Declares top-level exports and package version. |
| `__main__.py` | Sends `python -m reviewlens` to the same CLI. |
| `api.py` | Orchestrates all pure analysis stages and assembles metadata. |
| `cli.py` | Parses arguments, translates configuration, presents progress/errors, and invokes the public API. |
| `config.py` | Defines frozen configuration sections and defaults. |
| `models.py` | Defines `Diagnostic`, `AnalysisResult`, and `ExportManifest`. |
| `exceptions.py` | Defines the stable public exception hierarchy. |

Inside each stage package, modules remain similarly focused. Ingestion separates
CSV parsing, JSON shape handling, name normalization, and canonical schema
resolution. Analysis separates vectorization, candidate evaluation, cluster
selection, interpretation, and projection. Export separates formula/cell
safety, chart rendering, and workbook transactions.

## Data flow

```text
input path
  -> load CSV/JSON and calculate source SHA-256
  -> normalize names and resolve the canonical schema
  -> preserve all rows; mark invalid ratings through diagnostics
  -> clean and preprocess review text
  -> retain excluded rows while selecting usable modeling rows
  -> build sparse TF-IDF features
  -> evaluate/select automatic k or validate manual k
  -> retain the fitted K-Means model and labels
  -> deterministically relabel and interpret clusters
  -> build visualization-only projection and chart-source frames
  -> assemble AnalysisResult and reproducibility metadata
  -> optionally export Excel and PNG artifacts
```

Focused immutable stage results carry frames, matrices, models, and diagnostics
between boundaries. `api.py` coordinates them without duplicating algorithms.
The CLI delegates to `analyze_reviews` rather than maintaining another
pipeline.

## Side-effect boundary

`analyze_reviews(...)` reads exactly the explicitly named dataset. It performs
no output write, network request, environment-secret lookup, logging of review
text, or model download. It returns all state needed for inspection or later
export.

`AnalysisResult.export_excel(...)` is the sole public output side-effect. The
export layer:

1. resolves the workbook and adjacent chart-directory targets;
2. rejects a non-`.xlsx` path and protects existing targets unless force is
   explicit;
3. renders charts and workbook content in a temporary sibling directory;
4. sanitizes formula-like cells and enforces Excel's cell limit;
5. closes and validates the seven-sheet workbook and embedded images; and
6. installs both targets, restoring earlier targets if a forced transaction
   fails.

CLI stdout/stderr is a presentation concern in `cli.py`. Library analysis stays
quiet and exposes non-fatal conditions as `Diagnostic` objects.

## Automatic cluster selection

The sparse TF-IDF matrix is passed directly to K-Means. With `clusters="auto"`,
candidate values are integers from 2 through
`min(k_max, usable_review_count - 1)`, so automatic mode needs at least three
usable reviews.

Each candidate is fitted once with the configured `random_state`, `n_init`, and
`max_iter`. ReviewLens records inertia for elbow inspection and calculates
cosine silhouette on at most `silhouette_sample_size` deterministically selected
rows. Inertia does not choose `k`.

A candidate that produces too few distinct labels or cannot produce a
silhouette score remains in the evaluation table as invalid and is excluded
from selection. The highest silhouette wins; an exact numerical tie selects the
smaller `k`. ReviewLens retains the already fitted winning model rather than
refitting it.

Manual mode validates `2 <= k < usable_review_count` and requires the fitted
model to produce the requested number of non-empty labels. Its public
evaluation frame is empty unless `evaluate_manual=True` or CLI `--evaluate`
requests the wider diagnostic range.

## Interpretation and presentation relabeling

K-Means model labels are arbitrary. ReviewLens converts them into presentation
IDs only after fitting and interpretation:

1. sort clusters by descending review count;
2. break a tie by ascending theme;
3. break any remaining tie by ascending original model label; and
4. assign consecutive IDs beginning at zero.

The relabeling is applied consistently to review assignments, summaries,
keywords, projections, and charts. It improves stable presentation for an
unchanged analysis, but cluster IDs are not promised to remain the same after
the dataset or configuration changes.

Cluster term importance is mean TF-IDF weight within the cluster. Keywords use
descending score and ascending term tie-breaking. Themes join the first three
terms. Representative reviews are nearest to the fitted centroid by cosine
distance, with `source_row` as the tie-breaker. Fixed Indonesian templates
describe only observed size, share, ratings, and terms; they make no causal or
generative claim.

## Why SVD is visualization-only

ReviewLens uses `TruncatedSVD` only to provide two-dimensional coordinates for
the cluster-projection chart. K-Means fits the original sparse TF-IDF matrix,
and keyword scoring and representative selection use that same feature space.

Keeping SVD out of clustering avoids making analytical results depend on a
lossy display transformation. Projection sampling is separately bounded and
seeded. If the feature space has one usable dimension, the visualization uses
that dimension as x and zero as y and records a diagnostic; analytical results
remain unchanged.

## Determinism, scale, and privacy

The reproducibility boundary is the same input, effective configuration,
ReviewLens version, dependency versions, and supported execution environment.
Seeds, stable source-row numbering, sorted ties, retained winning models, and
deterministic samples support repeatable selected `k`, labels, keywords, and
representatives. Generation timestamps and byte-level workbook serialization
are outside this boundary.

The pipeline is designed for in-memory analysis of up to 50,000 reviews on a
typical laptop. Sparse features, a 50,000-feature default cap, a 5,000-row
silhouette sample, and a 10,000-row projection sample bound expensive stages,
but CSV/JSON loading still materializes the full input and no timing SLA or
streaming behavior is promised.

Only the source basename and SHA-256 enter metadata; absolute input paths do
not. User content is nevertheless retained in result tables and reports, so
callers remain responsible for access control and appropriate handling.

See the [API reference](api.md), [data-format guide](data-format.md), and
[project README](../README.md).
