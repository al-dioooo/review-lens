# Changelog

All notable changes to ReviewLens are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Included `LICENSE` and `NOTICE` in built wheels and source distributions,
  with standards-compliant wheel license-file metadata.
- Preserved CSV sentinel-like text, leading zeros, blank records, and raw header
  and record-width validation while reporting empty files and NUL characters as
  `InputError`.
- Translated JSON digit limits into `InputError`, enforced a deterministic
  64-container nesting limit, and safely classified extreme or non-finite
  ratings without pandas overflow or CLI tracebacks.
- Preserved explicit JSON `NaN`/infinity rating provenance for invalid-rating
  diagnostics and exported out-of-range Python integers as exact decimal text
  without mutating analysis results.
- Rejected structured review text and boolean or structured ratings at the
  public input boundary.
- Validated every public configuration field and nested section before loading
  data, while preserving convenience-argument precedence.
- Suppressed only expected K-Means convergence warnings for duplicate-heavy
  candidates so successful API and quiet CLI calls remain silent.
- Made Unicode NFKC column normalization idempotent while retaining Unicode
  letters, digits, and attached combining marks.
- Classified `rating_unavailable` as a warning and included it in warning
  diagnostic totals.

## [0.1.0] - 2026-07-15

### Added

- CSV ingestion with UTF-8/BOM handling, delimiter detection, normalized column
  aliases, explicit text/rating overrides, rating diagnostics, and retained
  duplicates and metadata.
- JSON-list and JSON-object ingestion with supported record keys and explicit
  record-key configuration.
- Indonesian-first preprocessing with deterministic cleaning, slang
  normalization, protected negations, stopword removal, and optional Sastrawi
  stemming.
- Sparse TF-IDF feature extraction and seeded K-Means clustering with manual or
  cosine-silhouette automatic cluster selection.
- Deterministic cluster relabeling, extractive keywords, themes, rating signals,
  summaries, and representative reviews.
- A shared Python API and `reviewlens analyze` command-line interface.
- Seven-sheet Excel reports and adjacent PNG charts with atomic installation,
  overwrite protection, formula-injection protection, and cell-length safety.
- Unit and integration coverage for ingestion, preprocessing, analysis,
  interpretation, projection, CLI behavior, reproducibility, and export safety.
- Open-source license, governance, security, contribution, architecture, API,
  and data-format documentation.
