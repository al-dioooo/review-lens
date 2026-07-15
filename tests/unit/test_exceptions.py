from reviewlens.exceptions import (
    AnalysisError,
    ConfigurationError,
    ExportError,
    InputError,
    ReviewLensError,
)
from reviewlens.models import Diagnostic


def test_public_errors_share_one_base() -> None:
    for error_type in (InputError, ConfigurationError, AnalysisError, ExportError):
        assert issubclass(error_type, ReviewLensError)


def test_diagnostic_is_structured_and_immutable() -> None:
    diagnostic = Diagnostic(
        severity="warning",
        code="invalid_rating",
        message="One rating was ignored.",
        count=1,
    )
    assert diagnostic.code == "invalid_rating"
    assert diagnostic.count == 1
