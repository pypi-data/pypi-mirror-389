"""Example problem implementations demonstrating security backends.

This module provides example problems that demonstrate how to use the
different security backends (SubprocessProblem, DockerProblem) for
various use cases.

Examples:
    FeatureProblem: Feature engineering with subprocess isolation
    UntrustedCodeProblem: Untrusted code testing with Docker isolation
    FunctionTestProblem: Fast function testing with in-process execution
"""

from .feature import FeatureProblem
from .untrusted import UntrustedCodeProblem
from .function_test import FunctionTestProblem

__all__ = ["FeatureProblem", "UntrustedCodeProblem", "FunctionTestProblem"]
