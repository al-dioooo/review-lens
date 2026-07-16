from __future__ import annotations

import re
import subprocess
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path

import reviewlens

ROOT = Path(__file__).resolve().parents[2]


def test_package_metadata_and_version_are_consistent() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["name"] == "review-lens"
    assert project["version"] == reviewlens.__version__ == "0.1.0"
    assert project["requires-python"] == ">=3.11"
    assert project["license"] == "Apache-2.0"
    assert project["scripts"]["reviewlens"] == "reviewlens.cli:main"
    assert metadata["tool"]["uv"]["build-backend"]["module-name"] == "reviewlens"


def test_initial_pypi_release_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "python -m pip install review-lens" in readme
    assert "These commands install local source" not in readme
    assert "## [Unreleased]\n\n## [0.1.0] - 2026-07-16" in changelog
    assert changelog.index("### Fixed") > changelog.index("## [0.1.0]")


def test_ci_covers_supported_pythons_and_platform_smoke() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for value in ("3.11", "3.12", "3.13", "3.14"):
        assert value in workflow
    for value in ("ubuntu-latest", "macos-latest", "windows-latest", "production"):
        assert value in workflow
    assert re.search(r"astral-sh/setup-uv@v\d+\.\d+\.\d+\b", workflow)
    assert re.search(
        r"if: matrix\.python-version == '3\.11'\n\s+run: uv run mypy src tests",
        workflow,
    )


def test_runtime_has_no_out_of_scope_integrations() -> None:
    banned = ("apify", "dotenv", "mcp", "openai", "scrap")
    paths = [
        ROOT / "pyproject.toml",
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted((ROOT / "examples").glob("*")),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    assert not any(term in combined for term in banned)


def test_built_archives_include_apache_license_and_notice(tmp_path: Path) -> None:
    completed = subprocess.run(
        ["uv", "build", "--no-sources", "--out-dir", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    wheel_path = next(tmp_path.glob("*.whl"))
    sdist_path = next(tmp_path.glob("*.tar.gz"))
    legal_payloads = {
        name: (ROOT / name).read_bytes() for name in ("LICENSE", "NOTICE")
    }
    with zipfile.ZipFile(wheel_path) as wheel:
        wheel_names = set(wheel.namelist())
        metadata_name = next(
            name for name in wheel_names if name.endswith(".dist-info/METADATA")
        )
        metadata = Parser().parsestr(wheel.read(metadata_name).decode("utf-8"))
        for basename, expected in legal_payloads.items():
            member_name = next(
                name
                for name in wheel_names
                if name.endswith(f".dist-info/licenses/{basename}")
            )
            assert wheel.read(member_name) == expected

    assert set(metadata.get_all("License-File", [])) == {"LICENSE", "NOTICE"}

    with tarfile.open(sdist_path, mode="r:gz") as sdist:
        sdist_names = set(sdist.getnames())
        for basename, expected in legal_payloads.items():
            member_name = next(
                name for name in sdist_names if name.endswith(f"/{basename}")
            )
            member = sdist.extractfile(member_name)
            assert member is not None
            assert member.read() == expected
