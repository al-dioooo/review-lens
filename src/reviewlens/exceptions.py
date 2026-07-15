class ReviewLensError(Exception):
    """Base class for expected ReviewLens failures."""


class InputError(ReviewLensError):
    """The supplied file or dataset contract is invalid."""


class ConfigurationError(ReviewLensError):
    """The supplied analysis configuration is invalid."""


class AnalysisError(ReviewLensError):
    """The dataset cannot produce a valid analysis."""


class ExportError(ReviewLensError):
    """The completed analysis cannot be exported safely."""
