from pathlib import Path

import pytest


@pytest.fixture
def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def example_csv(repository_root: Path) -> Path:
    return repository_root / "examples" / "sample_reviews.csv"


@pytest.fixture
def example_json(repository_root: Path) -> Path:
    return repository_root / "examples" / "sample_reviews.json"
