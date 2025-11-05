from __future__ import annotations
from typing import Any, Protocol, NamedTuple
import time
import traceback
import json
import pathlib


class EvalResult(NamedTuple):
    """
    Result of evaluating a submission.

    Can be unpacked as tuple: score, ok, artifacts, error = result
    Or accessed by name: result.score, result.ok, etc.
    """
    score: float
    ok: bool = True
    artifacts: dict = {}
    error: str | None = None
    time_ms: int = 0


class Problem(Protocol):
    """
    Protocol for evaluation problems.

    Problems should implement a single evaluate() method that takes
    any submission format they choose and returns:
    - dict: just artifacts (no score - useful for analysis/reports)
    - float: just the score (assumes success, no artifacts)
    - EvalResult: detailed result with score, artifacts, errors
    """
    name: str

    def evaluate(self, submission: Any) -> dict | float | EvalResult:
        """
        Evaluate a submission and return artifacts and/or score.

        Args:
            submission: Any format - problem defines this (path, dict, object, etc.)

        Returns:
            dict: Just artifacts (score will be -inf) - for analysis/reporting
            float: Just score (assumes ok=True, no artifacts)
            EvalResult: Detailed result with score, ok, artifacts, error

        Examples:
            # Just artifacts (useful for backtests, reports)
            return {"backtest_results": {...}, "metrics": {...}}

            # Just score
            return 0.95

            # Both
            return EvalResult(score=0.95, artifacts={"details": ...})
        """
        ...


def evaluate(problem: Problem, submission: Any) -> EvalResult:
    """
    Evaluate a submission against a problem with timing and error handling.

    Args:
        problem: Problem instance with evaluate() method
        submission: Submission in whatever format the problem expects

    Returns:
        EvalResult with score, ok status, artifacts, timing, and error (if any)

    Note:
        If evaluate() returns just a dict (artifacts only), score will be -inf.
        This is useful for analysis/reporting workflows where scoring is optional.
    """
    start = time.perf_counter()

    try:
        result = problem.evaluate(submission)

        # Normalize result to EvalResult
        if isinstance(result, dict) and not isinstance(result, EvalResult):
            # Dict return - just artifacts, no score
            normalized = EvalResult(score=float("-inf"), ok=True, artifacts=result, error=None, time_ms=0)
        elif isinstance(result, (int, float)):
            # Simple float return - assume success
            score = float(result)
            normalized = EvalResult(score=score, ok=True, artifacts={}, error=None, time_ms=0)
        elif isinstance(result, EvalResult):
            # Already EvalResult
            normalized = result
        elif isinstance(result, tuple):
            # Tuple return - try to unpack
            if len(result) == 5:
                score, ok, artifacts, error, _ = result  # ignore time_ms from tuple
                normalized = EvalResult(score=score, ok=ok, artifacts=artifacts, error=error, time_ms=0)
            elif len(result) == 4:
                score, ok, artifacts, error = result
                normalized = EvalResult(score=score, ok=ok, artifacts=artifacts, error=error, time_ms=0)
            elif len(result) == 2:
                score, artifacts = result
                normalized = EvalResult(score=score, ok=True, artifacts=artifacts, error=None, time_ms=0)
            else:
                raise ValueError(f"Invalid tuple length: {len(result)}, expected 2, 4, or 5")
        else:
            raise TypeError(f"evaluate() must return dict, float, or EvalResult, got {type(result)}")

        # Add timing
        wall_ms = int((time.perf_counter() - start) * 1000)
        return EvalResult(
            score=normalized.score,
            ok=normalized.ok,
            artifacts=normalized.artifacts,
            error=normalized.error,
            time_ms=wall_ms
        )

    except Exception as e:
        # Evaluation failed
        wall_ms = int((time.perf_counter() - start) * 1000)
        return EvalResult(
            score=float("-inf"),
            ok=False,
            artifacts={},
            error=traceback.format_exc(),
            time_ms=wall_ms
        )


# Utilities

def load_submission(path: str) -> dict[str, Any]:
    """
    Load a submission from a file path.

    This is a convenience utility. Problems can define their own
    submission loading logic and formats.

    Args:
        path: Path to submission file

    Returns:
        dict: Loaded submission
            - .json files: parsed JSON dict
            - .py files: {"kind": "python_script", "code": "..."}

    Raises:
        ValueError: If file type is not supported
    """
    p = pathlib.Path(path)
    if p.suffix == ".json":
        return json.loads(p.read_text())
    if p.suffix == ".py":
        return {"kind": "python_script", "code": p.read_text()}
    raise ValueError(f"Unsupported submission type: {p.suffix}")
