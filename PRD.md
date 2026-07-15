# PRD.md — ReviewLens

## Project Overview

**Project Name:** ReviewLens  
**Type:** Open Source Python Toolkit  
**License Target:** Apache-2.0  
**Primary Language:** Python 3.11+

## Vision

ReviewLens is an open-source review intelligence toolkit that helps developers, researchers, and businesses transform raw customer feedback into actionable insights.

The project analyzes customer reviews using NLP and machine learning techniques to discover:
- recurring feedback themes
- customer complaints
- positive patterns
- review clusters
- representative keywords
- summarized insights

ReviewLens should become a reusable Python package and developer tool, not a one-off research script.

---

# Problem Statement

Organizations collect thousands of customer reviews but often lack accessible tools to understand what customers actually experience.

Current problems:
- Enterprise analytics tools are expensive.
- Small businesses lack technical resources.
- Research workflows require complex manual preprocessing.
- Existing solutions are often not Indonesian-language friendly.

ReviewLens provides an open-source alternative focused on simplicity, reproducibility, and extensibility.

---

# Target Users

## Developers

Needs:
- Python library
- CLI interface
- automation support
- integration capability

## Researchers

Needs:
- reproducible NLP workflows
- configurable analysis pipeline
- exportable results

## Businesses

Needs:
- understandable reports
- complaint discovery
- customer satisfaction insights

---

# MVP Goals

The first release must:

1. Convert existing review analytics logic into a production-ready Python package.
2. Support CSV and JSON review datasets.
3. Provide Indonesian-first NLP preprocessing.
4. Provide review clustering analysis.
5. Generate exportable reports.
6. Provide CLI and Python API.
7. Include professional open-source documentation.

---

# Non Goals

The MVP will not:

- scrape Google Maps automatically.
- provide a hosted SaaS dashboard.
- depend on external AI APIs.
- replace enterprise BI systems.

Data should come from user-provided datasets.

---

# Core Features

## 1. Data Ingestion

Supported formats:

- CSV
- JSON list
- JSON object containing review arrays

Example:

```json
[
  {
    "text": "Pelayanan sangat lambat",
    "rating": 2
  }
]
```

Automatic column normalization:

Example:

```
reviewText -> review_text
createdAt -> created_at
```

Required:
- review text

Optional:
- rating
- timestamp
- location
- metadata

---

# 2. Text Processing

Support:

Basic cleaning:
- lowercase conversion
- URL removal
- emoji removal
- punctuation normalization
- whitespace cleanup

Indonesian processing:
- stopword removal
- stemming using Sastrawi
- slang normalization

---

# 3. Feature Extraction

Default:

TF-IDF vectorization

Configurable:
- n-gram range
- max features
- minimum document frequency

---

# 4. Clustering Engine

MVP algorithm:

K-Means clustering

Features:
- manual cluster count
- automatic cluster evaluation

Evaluation:
- Elbow method
- Silhouette score

---

# 5. Cluster Interpretation

Each cluster should provide:

- cluster ID
- number of reviews
- average rating
- important keywords
- example reviews

Example:

```
Cluster 2

Theme:
Slow Service

Keywords:
- waiting
- queue
- slow

Examples:
- "Service took too long"
```

---

# 6. Export System

Generate:

## Excel Report

Sheets:

```
metadata
reviews
clusters
summary
keywords
visual_data
```

## Visualization

Generate:

- cluster distribution chart
- rating distribution
- keyword visualization
- dimensionality reduction plot

---

# CLI Interface

Example:

```bash
reviewlens analyze reviews.csv
```

Advanced:

```bash
reviewlens analyze reviews.csv --text-column text --rating-column rating --language id --clusters auto --output report.xlsx
```

---

# Python API

Example:

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

---

# Recommended Architecture

```
reviewlens/

├── src/
│   └── reviewlens/
│       ├── cli.py
│       ├── api.py
│       ├── config.py
│       │
│       ├── ingestion/
│       │   ├── csv_loader.py
│       │   ├── json_loader.py
│       │   └── schema.py
│       │
│       ├── preprocessing/
│       │   ├── cleaner.py
│       │   ├── stemming.py
│       │   └── slang.py
│       │
│       ├── analysis/
│       │   ├── vectorizer.py
│       │   ├── clustering.py
│       │   └── evaluator.py
│       │
│       └── export/
│           ├── excel.py
│           ├── charts.py
│           └── html.py
│
├── tests/
├── examples/
├── docs/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── pyproject.toml
```

---

# Technology Stack

Core:
- Python 3.11+
- pandas
- numpy
- scipy
- scikit-learn

NLP:
- Sastrawi
- nltk-compatible utilities

Visualization:
- matplotlib

Packaging:
- pyproject.toml
- uv

Testing:
- pytest

---

# Testing Requirements

Unit tests:

- loaders
- preprocessing
- vectorization
- clustering
- exporters

Integration test:

Input:

```
examples/sample_reviews.csv
```

Expected:

```
examples/output/report.xlsx
```

---

# Open Source Requirements

Before first release:

Required:

```
README.md
LICENSE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
CHANGELOG.md
```

README should include:

- introduction
- installation
- quick start
- examples
- architecture
- roadmap
- contribution guide

---

# Roadmap

## v0.1.0

- CSV import
- JSON import
- Indonesian preprocessing
- TF-IDF
- K-Means
- Excel export
- CLI

## v0.2.0

- HTML reports
- improved visualization
- multilingual support
- better cluster interpretation

## v0.3.0

- plugin architecture
- custom analyzers
- dashboard integration

## Future

Create:

```
reviewlens-mcp
```

Purpose:

Allow AI assistants to interact with ReviewLens analysis results.

Possible tools:

```
list_reports()
summarize_clusters()
find_common_complaints()
compare_reviews()
generate_recommendations()
```

---

# Development Rules

Requirements:

- Type hints required.
- Public APIs require documentation.
- Use pytest.
- Use ruff formatting.
- Maintain backward compatibility after v1.0.

Commit format:

```
feat:
fix:
docs:
test:
refactor:
chore:
```

---

# Initial Claude Code Task

Build ReviewLens MVP.

Priority:

1. Initialize Python package.
2. Migrate existing analytics logic.
3. Implement data ingestion.
4. Implement preprocessing.
5. Implement clustering engine.
6. Implement export system.
7. Implement CLI.
8. Add tests.
9. Create OSS documentation.
10. Prepare v0.1.0 release.

Do not implement:
- scraping
- dashboard
- AI integrations
- MCP server

until the core package is stable.
