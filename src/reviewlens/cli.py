from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Literal, cast

from reviewlens import (
    AnalysisConfig,
    AnalysisError,
    ConfigurationError,
    ExportError,
    InputError,
    __version__,
    analyze_reviews,
)


def _cluster_count(value: str) -> int | Literal["auto"]:
    if value == "auto":
        return "auto"
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "clusters must be 'auto' or an integer"
        ) from error
    if number < 2:
        raise argparse.ArgumentTypeError("clusters must be at least 2")
    return number


def _positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("value must be an integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return number


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reviewlens",
        description="Analyze review datasets and export an Excel report.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser(
        "analyze",
        help="analyze a CSV or JSON review dataset",
    )
    analyze.add_argument("input", type=Path, metavar="INPUT")
    analyze.add_argument("--text-column", metavar="NAME")
    analyze.add_argument("--rating-column", metavar="NAME")
    analyze.add_argument("--language", choices=("id",))
    analyze.add_argument("--clusters", type=_cluster_count, default="auto")
    analyze.add_argument("--output", type=Path, metavar="PATH")
    analyze.add_argument(
        "--ngram-range",
        type=_positive_integer,
        nargs=2,
        metavar=("MIN", "MAX"),
    )
    analyze.add_argument("--min-df", type=_positive_integer, metavar="N")
    analyze.add_argument("--max-features", type=_positive_integer, metavar="N")
    analyze.add_argument("--stem", action="store_true")
    analyze.add_argument("--no-slang", action="store_true")
    analyze.add_argument("--no-stopwords", action="store_true")
    analyze.add_argument("--evaluate", action="store_true")
    analyze.add_argument("--force", action="store_true")
    analyze.add_argument("--quiet", action="store_true")
    analyze.add_argument("--debug", action="store_true")
    return parser


def _analysis_config(arguments: argparse.Namespace) -> AnalysisConfig:
    config = AnalysisConfig()
    ngram_range = config.vectorizer.ngram_range
    if arguments.ngram_range is not None:
        ngram_range = cast(tuple[int, int], tuple(arguments.ngram_range))
    vectorizer = replace(
        config.vectorizer,
        ngram_range=ngram_range,
        min_df=(
            config.vectorizer.min_df if arguments.min_df is None else arguments.min_df
        ),
        max_features=(
            config.vectorizer.max_features
            if arguments.max_features is None
            else arguments.max_features
        ),
    )
    preprocessing = replace(
        config.preprocessing,
        stem=arguments.stem,
        normalize_slang=not arguments.no_slang,
        remove_stopwords=not arguments.no_stopwords,
    )
    clustering = replace(
        config.clustering,
        evaluate_manual=arguments.evaluate,
    )
    return replace(
        config,
        preprocessing=preprocessing,
        vectorizer=vectorizer,
        clustering=clustering,
    )


def _report_error(error: Exception, *, debug: bool) -> None:
    if debug:
        traceback.print_exc()
    print(f"error: {error}", file=sys.stderr)


def _run_analyze(arguments: argparse.Namespace) -> int:
    if not arguments.quiet:
        print(f"Analyzing: {arguments.input}")
    try:
        result = analyze_reviews(
            arguments.input,
            language=arguments.language,
            clusters=arguments.clusters,
            text_column=arguments.text_column,
            rating_column=arguments.rating_column,
            config=_analysis_config(arguments),
        )
        if not arguments.quiet:
            print("Exporting workbook and charts...")
        manifest = result.export_excel(arguments.output, force=arguments.force)
    except (InputError, ConfigurationError) as error:
        _report_error(error, debug=arguments.debug)
        return 2
    except (AnalysisError, ExportError) as error:
        _report_error(error, debug=arguments.debug)
        return 1

    if not arguments.quiet:
        chart_directory = (
            manifest.chart_paths[0].parent
            if manifest.chart_paths
            else manifest.workbook_path.parent / f"{manifest.workbook_path.stem}_charts"
        )
        print(f"Selected k: {result.metadata['selected_k']}")
        print(f"Workbook: {manifest.workbook_path}")
        print(f"Chart directory: {chart_directory}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    return _run_analyze(arguments)


__all__ = ["main"]
