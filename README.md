# ReviewLens

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Python: 3.11–3.14](https://img.shields.io/badge/Python-3.11%E2%80%933.14-3776AB.svg)](pyproject.toml)

ReviewLens is a deterministic, Indonesian-first Python toolkit for turning
user-provided review datasets into inspectable clusters, keywords, summaries,
Excel tables, and PNG charts.

It is designed for developers, researchers, and businesses that need a local,
reproducible analysis path without a hosted service or opaque generated
interpretation. ReviewLens accepts CSV and JSON, preserves source rows and
diagnostics, builds sparse TF-IDF features, selects or validates a K-Means
cluster count, and produces deterministic extractive interpretations.

## Scope

Version 0.1.0 includes CSV and JSON ingestion, Indonesian cleaning and slang
normalization, protected negations, stopword removal, optional stemming,
TF-IDF, manual or automatic K-Means clustering, deterministic cluster
interpretation, two-dimensional chart projection, a Python API, a CLI, and
Excel/PNG export.

ReviewLens analyzes files supplied by the user. It does not collect reviews,
provide a hosted dashboard, call external AI APIs, download models at runtime,
support languages other than Indonesian, or replace an enterprise BI system.
HTML reports, plugin interfaces, custom analyzer protocols, dashboards, and MCP
integration are not part of v0.1.0.

## Installation

ReviewLens requires Python 3.11 or newer. Install from a source checkout with
[uv](https://docs.astral.sh/uv/) as an isolated command-line tool:

```bash
uv tool install .
```

For development, create the locked project environment instead:

```bash
uv sync --all-groups --locked
```

You can also install the checkout with pip, preferably inside a virtual
environment:

```bash
python -m pip install .
```

These commands install local source; this document does not assume a package
registry release.

## Quick start

From the repository root after installing the command, analyze the committed
synthetic example:

```bash
reviewlens analyze examples/sample_reviews.csv
```

This selects `k` automatically and writes `sample_reviews-reviewlens.xlsx` plus
`sample_reviews-reviewlens_charts/` in the current directory. Existing targets
are protected; pass `--force` only when you intend to replace both.

The PRD-style advanced command chooses columns explicitly and names the output:

```bash
reviewlens analyze reviews.csv --text-column text --rating-column rating --language id --clusters auto --output report.xlsx
```

Useful controls include `--clusters N`, `--ngram-range MIN MAX`, `--min-df N`,
`--max-features N`, `--stem`, `--no-slang`, `--no-stopwords`, `--evaluate`,
`--quiet`, and `--debug`. Run `reviewlens analyze --help` for the full CLI
contract.

## Python API

The equivalent public API separates analysis from output writes:

```python
from reviewlens import analyze_reviews

result = analyze_reviews(
    file="reviews.csv",
    language="id",
    clusters=5
)

result.export_excel(
    "report.xlsx"
)
```

`analyze_reviews(...)` reads and analyzes the supplied dataset but creates no
output files. `result.export_excel(...)` is the explicit side-effect boundary
and returns an `ExportManifest` containing the final workbook and ordered chart
paths. See the [API reference](docs/api.md) for configuration, result frames,
diagnostics, and exceptions.

## Input data

Input must be a non-empty `.csv` or `.json` file with a review-text column.
Column names are normalized before schema resolution. Automatic aliases are:

| Canonical field | Accepted aliases |
| --- | --- |
| `review_text` | `review_text`, `text`, `review`, `content`, `review_body` |
| `rating` | `rating`, `stars`, `score`, `star_rating` |
| `timestamp` | `timestamp`, `created_at`, `date`, `review_date` |
| `location` | `location`, `place`, `venue`, `address` |
| `metadata` | `metadata`, `meta` |

Use `--text-column` and `--rating-column`, or the matching Python arguments,
when automatic aliases are ambiguous or your dataset uses different names.
Ratings are optional. Numeric values from 1 through 5 are retained; blank,
non-numeric, and out-of-range values become missing without excluding an
otherwise usable review. Unrecognized columns and exact duplicate rows are
preserved. The complete CSV/JSON rules and examples are in the
[data-format guide](docs/data-format.md).

## Output

Every workbook contains exactly seven ordered sheets:

1. `metadata` — versions, effective configuration, source hash, counts, and
   diagnostic totals;
2. `reviews` — every normalized source row, preprocessing state, inclusion
   status, exclusion reason, and cluster assignment;
3. `clusters` — cluster sizes, ratings, themes, summaries, keywords, and
   representative reviews;
4. `summary` — dataset-level metrics and highlights;
5. `keywords` — tidy ranked TF-IDF terms and scores;
6. `visual_data` — the source tables used for every chart; and
7. `visuals` — the charts embedded in deterministic order.

PNG files are placed beside the workbook in `<output-stem>_charts/`. They
include cluster distribution, per-cluster keywords, cluster projection,
optional rating distribution, and inertia/silhouette plots when evaluation data
exists.

Export escapes user-controlled strings whose first non-whitespace character is
`=`, `+`, `-`, or `@` before Excel serialization and enforces Excel's 32,767
character cell limit. The exporter stages and validates all artifacts before
installation and refuses to overwrite an existing workbook or chart directory
unless `force=True` or `--force` is explicit.

## Reproducibility and privacy

Deterministic results require the same input, configuration, ReviewLens version,
dependency versions, and supported execution environment. Under that boundary,
selected `k`, presentation labels, keywords, and representative source rows are
repeatable. Report timestamps and filesystem paths are outside the deterministic
comparison, and byte-identical workbooks are not promised across dependency
versions.

Analysis is local and has no network behavior. ReviewLens reads only the input
you name and writes only when export is requested. It requires no credentials,
does not include the absolute input path in report metadata, and does not log
review text by default. Reports still contain user-supplied review data, so
store and share them according to the source dataset's privacy requirements.
Formula-like text is neutralized for Excel safety, but that does not anonymize
the content.

## Architecture

The CLI and Python API share one typed pipeline:

```text
CSV/JSON -> schema -> preprocessing -> sparse TF-IDF -> K-Means
         -> deterministic interpretation -> chart data -> AnalysisResult
         -> explicit Excel/PNG export
```

K-Means operates directly on sparse TF-IDF features. TruncatedSVD is used only
to draw a two-dimensional projection and never changes clustering or
interpretation. The [architecture guide](docs/architecture.md) maps package
boundaries, automatic cluster selection, presentation relabeling, and export
side effects.

ReviewLens is designed for in-memory analysis of up to 50,000 reviews on a
typical developer laptop; this is a design target, not a timing guarantee. For
constrained machines, lower `max_features`, choose `k` manually, or avoid the
manual evaluation range.

## Roadmap

### v0.2.0

- HTML reports
- improved visualization
- multilingual support
- better cluster interpretation

### v0.3.0

- plugin architecture
- custom analyzers
- dashboard integration

### Future

A separate `reviewlens-mcp` project may let AI assistants inspect completed
ReviewLens results through tools such as report listing, cluster summaries,
common-complaint discovery, review comparison, and recommendation generation.
These integrations are deliberately outside the core package until it is
stable.

## Contributing

Development setup, tests, clean-room rules, synthetic-data requirements, and
commit conventions are in [CONTRIBUTING.md](CONTRIBUTING.md). Participation is
governed by the [Contributor Covenant](CODE_OF_CONDUCT.md). Please report
vulnerabilities privately according to [SECURITY.md](SECURITY.md).

Project history is recorded in [CHANGELOG.md](CHANGELOG.md). ReviewLens is
licensed under the [Apache License 2.0](LICENSE); attribution is in
[NOTICE](NOTICE).

Maintainer: [Aldio Lisafron](https://github.com/al-dioooo)
([al-dioooo](https://github.com/al-dioooo)).
