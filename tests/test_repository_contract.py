import hashlib
import re
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
_LOCAL_LINK = re.compile(
    r"(?<!!)\[[^\]]+\]\((?![a-z][a-z0-9+.-]*:)([^)#]+)(?:#[^)]*)?\)"
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


def test_canonical_policy_texts_are_unmodified_except_for_contact() -> None:
    expected_hashes = {
        "LICENSE": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        "CODE_OF_CONDUCT.md": (
            "99a08b9dd6f347f7610602fa1b79c3b55c7922cfea1c31569198d49f54e93a14"
        ),
    }
    for relative, expected in expected_hashes.items():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert digest == expected, relative


def test_readme_examples_match_supported_contracts() -> None:
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "reviewlens analyze examples/sample_reviews.csv" in content
    assert (
        "reviewlens analyze reviews.csv --text-column text --rating-column rating "
        "--language id --clusters auto --output report.xlsx"
    ) in content
    assert "result = analyze_reviews(" in content
    assert '    file="reviews.csv",' in content
    assert '    language="id",' in content
    assert "    clusters=5" in content
    assert '    "report.xlsx"' in content


def test_local_documentation_links_resolve() -> None:
    for relative in REQUIRED:
        if not relative.endswith(".md"):
            continue
        content = (ROOT / relative).read_text(encoding="utf-8")
        for target in _LOCAL_LINK.findall(content):
            resolved = (ROOT / relative).parent / target
            assert resolved.resolve().exists(), f"{relative}: {target}"
