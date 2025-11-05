from .sum_json import SumJSONProblem
from .text_regex import TextRegexProblem
from .validation import (
    validate_type,
    validate_series,
    run_test_cases,
    compute_fitness,
)
from .secure import SecureCodeProblem, SubprocessProblem, DockerProblem
from .examples import FeatureProblem, UntrustedCodeProblem, FunctionTestProblem

REGISTRY = {
    "sum-json": SumJSONProblem,
    "text-regex": TextRegexProblem,
}

__all__ = [
    "SumJSONProblem",
    "TextRegexProblem",
    "validate_type",
    "validate_series",
    "run_test_cases",
    "compute_fitness",
    "SecureCodeProblem",
    "SubprocessProblem",
    "DockerProblem",
    "FeatureProblem",
    "UntrustedCodeProblem",
    "FunctionTestProblem",
    "REGISTRY",
]
