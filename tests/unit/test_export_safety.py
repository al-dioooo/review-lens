from pathlib import Path

import pandas as pd

from reviewlens.export.safety import safe_excel_value, sanitize_frame


def test_formula_like_strings_are_prefixed() -> None:
    assert safe_excel_value(' =HYPERLINK("https://bad")')[0] == (
        '\' =HYPERLINK("https://bad")'
    )
    assert safe_excel_value("+SUM(1,1)")[0] == "'+SUM(1,1)"
    assert safe_excel_value("-1")[0] == "'-1"
    assert safe_excel_value(" @command")[0] == "' @command"
    assert safe_excel_value("ordinary text")[0] == "ordinary text"


def test_structured_values_use_canonical_json() -> None:
    assert safe_excel_value({"b": 2, "a": 1})[0] == '{"a": 1, "b": 2}'
    assert safe_excel_value(("b", "a"))[0] == '["b", "a"]'
    assert safe_excel_value([{"b": 2, "a": 1}])[0] == '[{"a": 1, "b": 2}]'


def test_missing_values_and_paths_are_normalized() -> None:
    assert safe_excel_value(None) == (None, False)
    assert safe_excel_value(pd.NA) == (None, False)
    assert safe_excel_value(float("nan")) == (None, False)
    assert safe_excel_value(Path("reports/final.xlsx")) == (
        "reports/final.xlsx",
        False,
    )


def test_final_excel_value_respects_cell_limit() -> None:
    value, truncated = safe_excel_value("=" + ("x" * 40_000))
    assert truncated is True
    assert isinstance(value, str)
    assert value.startswith("'=")
    assert len(value) == 32_767


def test_sanitize_frame_counts_truncated_cells() -> None:
    source = pd.DataFrame({"value": ["x" * 40_000, "ok"]})
    frame, count = sanitize_frame(source)
    assert count == 1
    value = frame.loc[0, "value"]
    assert isinstance(value, str)
    assert len(value) == 32_767
    original = source.loc[0, "value"]
    assert isinstance(original, str)
    assert len(original) == 40_000
