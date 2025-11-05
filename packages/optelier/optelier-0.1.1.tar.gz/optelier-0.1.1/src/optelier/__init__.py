"""
Optelier - DX-first evaluator: submission -> evaluation -> score
"""

__version__ = "0.1.0"

from .core import EvalResult, evaluate, Problem, load_submission

__all__ = [
    "__version__",
    "EvalResult",
    "evaluate",
    "Problem",
    "load_submission",
]
