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
