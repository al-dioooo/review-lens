"""ReviewLens public package."""

from reviewlens.api import analyze_reviews
from reviewlens.config import AnalysisConfig
from reviewlens.exceptions import (
    AnalysisError,
    ConfigurationError,
    ExportError,
    InputError,
    ReviewLensError,
)
from reviewlens.models import AnalysisResult, Diagnostic, ExportManifest

__all__ = [
    "AnalysisConfig",
    "AnalysisError",
    "AnalysisResult",
    "ConfigurationError",
    "Diagnostic",
    "ExportError",
    "ExportManifest",
    "InputError",
    "ReviewLensError",
    "analyze_reviews",
]
__version__ = "0.1.0"
