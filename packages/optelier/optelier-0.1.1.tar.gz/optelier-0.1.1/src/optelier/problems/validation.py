"""Validation helpers for problem implementations.

This module provides reusable validation utilities that problem implementations
commonly need. These helpers reduce boilerplate in problem classes and
standardize validation patterns across the codebase.

Functions:
    validate_type: Type validation with clear error messages
    validate_series: Pandas Series validation with variance and null rate checks
    run_test_cases: Test case runner for function testing
    compute_fitness: Fitness computation with penalties
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

import pandas as pd


def validate_type(value: Any, expected_type: type, name: str = "value") -> None:
    """Validate value is expected type, raise TypeError if not.

    Args:
        value: Value to check
        expected_type: Expected type
        name: Variable name for error message

    Raises:
        TypeError: If value is not expected_type

    Example:
        >>> validate_type(42, int, "count")
        >>> validate_type("hello", int, "count")  # Raises TypeError
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{name} must be {expected_type.__name__}, " f"got {type(value).__name__}"
        )


def validate_series(
    series: Any,  # pd.Series but mypy has issues with pandas types
    min_variance: float = 0.0,
    max_null_rate: float = 1.0,
    name: str = "series",
) -> Dict[str, Any]:
    """Validate pandas Series meets criteria.

    Args:
        series: Series to validate
        min_variance: Minimum required variance (default: 0.0)
        max_null_rate: Maximum allowed null rate (default: 1.0)
        name: Variable name for error/artifact messages

    Returns:
        dict: Artifacts with length, null_rate, variance

    Raises:
        TypeError: If not a pandas Series
        ValueError: If variance or null rate outside limits

    Example:
        >>> s = pd.Series([1, 2, 3, 4, 5])
        >>> artifacts = validate_series(s, min_variance=0.1)
        >>> assert artifacts["series_variance"] > 0.1
    """
    validate_type(series, pd.Series, name)

    # Cast to float to satisfy mypy
    null_rate_raw: Any = series.isna().mean()
    null_rate = float(null_rate_raw)
    variance_raw: Any = series.var() if len(series) > 1 else 0.0
    variance = float(variance_raw) if variance_raw is not None else 0.0

    artifacts: Dict[str, Any] = {
        f"{name}_length": len(series),
        f"{name}_null_rate": null_rate,
        f"{name}_variance": variance,
    }

    if null_rate > max_null_rate:
        raise ValueError(
            f"{name} null rate {null_rate:.2%} " f"exceeds maximum {max_null_rate:.2%}"
        )

    if variance < min_variance:
        raise ValueError(
            f"{name} variance {variance:.4f} " f"below minimum {min_variance:.4f}"
        )

    return artifacts


def run_test_cases(
    func: Callable[..., Any], test_cases: List[Tuple[Tuple[Any, ...], Any]]
) -> Tuple[float, Dict[str, Any]]:
    """Run test cases against function, return (score, artifacts).

    Args:
        func: Function to test
        test_cases: List of (inputs_tuple, expected_output)

    Returns:
        (score, artifacts): Score is pass_rate (0-1), artifacts contain details

    Example:
        >>> def add(x, y): return x + y
        >>> cases = [((1, 2), 3), ((2, 3), 5)]
        >>> score, artifacts = run_test_cases(add, cases)
        >>> assert score == 1.0
        >>> assert artifacts["passed"] == 2
    """
    passed = 0
    failed = 0
    failures: List[Dict[str, Any]] = []

    for inputs, expected in test_cases:
        try:
            result = func(*inputs)
            if result == expected:
                passed += 1
            else:
                failed += 1
                failures.append({"inputs": inputs, "expected": expected, "got": result})
        except Exception as e:
            failed += 1
            failures.append({"inputs": inputs, "expected": expected, "error": str(e)})

    total = passed + failed
    score = passed / total if total > 0 else 0.0

    artifacts: Dict[str, Any] = {
        "passed": passed,
        "failed": failed,
        "total": total,
        "failures": failures[:5],  # Limit to first 5 for readability
    }

    return score, artifacts


def compute_fitness(score: float, penalties: Dict[str, float] | None = None) -> float:
    """Compute final fitness with penalties.

    Args:
        score: Base score (0-1)
        penalties: Dict of penalty_name -> penalty_fraction (0-1)
            Each penalty multiplies score by (1 - penalty)

    Returns:
        float: Final fitness score (0-1)

    Raises:
        ValueError: If any penalty is not in range [0, 1]

    Example:
        >>> fitness = compute_fitness(0.8, {"null_rate": 0.1, "low_variance": 0.2})
        >>> # 0.8 * (1-0.1) * (1-0.2) = 0.8 * 0.9 * 0.8 = 0.576
    """
    fitness = score
    if penalties:
        for name, penalty in penalties.items():
            if not 0 <= penalty <= 1:
                raise ValueError(f"Penalty {name} must be 0-1, got {penalty}")
            fitness *= 1.0 - penalty
    return max(0.0, fitness)
