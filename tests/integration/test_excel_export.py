from __future__ import annotations

import os
from pathlib import Path

import pytest
from openpyxl import load_workbook

from reviewlens import analyze_reviews
from reviewlens.exceptions import ExportError


def _source(tmp_path: Path, ratings: bool = True) -> Path:
    path = tmp_path / "reviews.csv"
    suffixes = [",2", ",1", ",2", ",5", ",4", ",5"] if ratings else [""] * 6
    texts = [
        "=pelayanan lambat antre",
        "antre lama pelayanan",
        "petugas lambat antre",
        "tempat bersih nyaman",
        "bersih rapi nyaman",
        "lokasi nyaman bersih",
    ]
    header = "text,rating\n" if ratings else "text\n"
    path.write_text(
        header
        + "".join(
            f"{text}{rating}\n" for text, rating in zip(texts, suffixes, strict=True)
        ),
        encoding="utf-8",
    )
    return path


def test_export_has_ordered_sheets_embedded_images_and_pngs(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    output = tmp_path / "report.xlsx"
    manifest = result.export_excel(output)
    assert manifest.workbook_path == output.resolve()
    assert manifest.workbook_path.is_file()
    assert manifest.chart_paths
    workbook = load_workbook(output, data_only=False)
    assert workbook.sheetnames == [
        "metadata",
        "reviews",
        "clusters",
        "summary",
        "keywords",
        "visual_data",
        "visuals",
    ]
    headers = [cell.value for cell in workbook["reviews"][1]]
    review_column = headers.index("review_text") + 1
    assert workbook["reviews"].cell(2, review_column).value.startswith("'=")
    assert workbook["visuals"]._images


def test_export_refuses_existing_target_without_force(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    output = tmp_path / "report.xlsx"
    result.export_excel(output)
    with pytest.raises(ExportError, match="already exists"):
        result.export_excel(output)
    result.export_excel(output, force=True)


def test_rating_free_export_omits_rating_chart(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path, ratings=False), clusters=2)
    manifest = result.export_excel(tmp_path / "report.xlsx")
    assert not any(
        path.name == "rating_distribution.png" for path in manifest.chart_paths
    )


def test_force_export_restores_original_after_install_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    output = tmp_path / "report.xlsx"
    first = result.export_excel(output)
    original_workbook = output.read_bytes()
    original_charts = {path.name: path.read_bytes() for path in first.chart_paths}
    real_replace = os.replace
    failed = False

    def fail_once(source: str | Path, destination: str | Path) -> None:
        nonlocal failed
        if Path(destination) == output and not failed:
            failed = True
            raise OSError("simulated staged-workbook install failure")
        real_replace(source, destination)

    monkeypatch.setattr("reviewlens.export.excel.os.replace", fail_once)
    with pytest.raises(ExportError, match=r"report\.xlsx"):
        result.export_excel(output, force=True)
    assert output.read_bytes() == original_workbook
    assert {
        path.name: path.read_bytes() for path in (tmp_path / "report_charts").iterdir()
    } == original_charts


def test_force_export_preserves_original_after_backup_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    output = tmp_path / "report.xlsx"
    first = result.export_excel(output)
    original_workbook = output.read_bytes()
    original_charts = {path.name: path.read_bytes() for path in first.chart_paths}
    real_replace = os.replace

    def fail_workbook_backup(source: str | Path, destination: str | Path) -> None:
        if Path(source) == output and "reviewlens-backup" in Path(destination).name:
            raise OSError("simulated workbook backup failure")
        real_replace(source, destination)

    monkeypatch.setattr("reviewlens.export.excel.os.replace", fail_workbook_backup)
    with pytest.raises(ExportError, match=r"report\.xlsx"):
        result.export_excel(output, force=True)
    assert output.read_bytes() == original_workbook
    assert {
        path.name: path.read_bytes() for path in (tmp_path / "report_charts").iterdir()
    } == original_charts


def test_export_requires_xlsx_extension(tmp_path: Path) -> None:
    result = analyze_reviews(_source(tmp_path), clusters=2)
    with pytest.raises(ExportError, match=r"\.xlsx"):
        result.export_excel(tmp_path / "report.xls")
