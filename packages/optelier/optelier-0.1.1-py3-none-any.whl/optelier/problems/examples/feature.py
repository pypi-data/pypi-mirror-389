"""FeatureProblem: Example problem for feature engineering evaluation.

This module provides an example problem that uses SubprocessProblem for
medium-security evaluation of feature engineering code. It validates that
generated features are pandas Series with sufficient variance and acceptable
null rates.

The problem demonstrates:
- SubprocessProblem usage for process isolation
- Feature quality validation (variance, null rate)
- Integration with validation helpers
- Clear error messages for common issues

Example:
    >>> import pandas as pd
    >>> from optelier.problems.examples import FeatureProblem
    >>>
    >>> # Create sample data
    >>> df = pd.DataFrame({
    ...     'price': [100, 110, 105, 120, 115],
    ...     'volume': [1000, 1200, 950, 1500, 1100]
    ... })
    >>>
    >>> # Define problem
    >>> problem = FeatureProblem(
    ...     name="momentum_feature",
    ...     data=df,
    ...     min_variance=0.01,
    ...     max_null_rate=0.1
    ... )
    >>>
    >>> # Evaluate feature code
    >>> code = '''
    ... import pandas as pd
    ... feature = df['price'].pct_change()
    ... '''
    >>> result = problem.evaluate({"code": code})
    >>> result.ok
    True
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from optelier.problems.secure import SubprocessProblem
from optelier.problems.validation import validate_series


class FeatureProblem(SubprocessProblem):
    """Problem for evaluating feature engineering code.

    This problem uses SubprocessProblem for medium-security evaluation
    of feature engineering code. The submitted code should:
    1. Receive a DataFrame via 'df' variable
    2. Create a feature (pandas Series)
    3. Assign result to 'feature' variable

    The feature is validated for:
    - Type: Must be pandas Series
    - Variance: Must meet minimum variance threshold
    - Null rate: Must not exceed maximum null rate

    Score is computed based on feature variance, with higher variance
    (up to 1.0) receiving better scores.

    Attributes:
        data: DataFrame to provide as input
        min_variance: Minimum required variance (default 0.01)
        max_null_rate: Maximum allowed null rate (default 0.1)

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'price': [100, 110, 105, 120, 115],
        ...     'volume': [1000, 1200, 950, 1500, 1100]
        ... })
        >>>
        >>> problem = FeatureProblem(
        ...     name="price_momentum",
        ...     data=df,
        ...     min_variance=0.001,
        ...     max_null_rate=0.2
        ... )
        >>>
        >>> # Submit feature code
        >>> code = "feature = df['price'].pct_change()"
        >>> result = problem.evaluate(code)
        >>> result.ok
        True
        >>> result.score > 0
        True
    """

    def __init__(
        self,
        name: str,
        data: pd.DataFrame,
        min_variance: float = 0.01,
        max_null_rate: float = 0.1,
        timeout: int = 30,
    ):
        """Initialize FeatureProblem.

        Args:
            name: Problem name (for identification)
            data: DataFrame to provide as input to submitted code
            min_variance: Minimum required variance for feature (default 0.01)
            max_null_rate: Maximum allowed null rate for feature (default 0.1)
            timeout: Maximum execution time in seconds (default 30)

        Raises:
            TypeError: If data is not a pandas DataFrame
            ValueError: If min_variance < 0 or max_null_rate < 0 or > 1

        Example:
            >>> df = pd.DataFrame({'x': [1, 2, 3, 4, 5]})
            >>> problem = FeatureProblem(
            ...     name="simple_feature",
            ...     data=df,
            ...     min_variance=0.1,
            ...     max_null_rate=0.05
            ... )
        """
        # Validate inputs
        if not isinstance(data, pd.DataFrame):
            raise TypeError(f"data must be pandas DataFrame, got {type(data).__name__}")

        if min_variance < 0:
            raise ValueError(f"min_variance must be >= 0, got {min_variance}")

        if not 0 <= max_null_rate <= 1:
            raise ValueError(f"max_null_rate must be in [0, 1], got {max_null_rate}")

        # Initialize parent with subprocess execution
        super().__init__(
            name=name,
            timeout=timeout,
            allowed_imports={"pandas", "numpy"},
        )

        # Store problem-specific attributes
        self.data = data
        self.min_variance = min_variance
        self.max_null_rate = max_null_rate

    def setup_environment(self) -> dict[str, Any]:
        """Prepare environment for code execution.

        Returns:
            dict: Contains 'df' key with the input DataFrame

        Example:
            >>> env = problem.setup_environment()
            >>> 'df' in env
            True
            >>> isinstance(env['df'], pd.DataFrame)
            True
        """
        return {"df": self.data}

    def validate_output(
        self, namespace: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """Validate feature output and compute score.

        The submitted code must assign a pandas Series to the 'feature'
        variable. The series is validated for type, variance, and null rate.

        Score is computed as: min(1.0, variance / 1.0)
        This rewards features with higher variance (up to 1.0).

        Args:
            namespace: Execution namespace after code runs

        Returns:
            (score, artifacts): Score in [0, 1] and validation artifacts

        Raises:
            ValueError: If 'feature' variable missing or validation fails
            TypeError: If 'feature' is not a pandas Series

        Example:
            >>> # Internal use - called by evaluate()
            >>> namespace = {
            ...     'df': df,
            ...     'feature': pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
            ... }
            >>> score, artifacts = problem.validate_output(namespace)
            >>> score > 0
            True
            >>> 'feature_variance' in artifacts
            True
        """
        # Check feature variable exists
        if "feature" not in namespace:
            raise ValueError(
                "Code must assign result to 'feature' variable. "
                "Example: feature = df['price'].pct_change()"
            )

        # Validate feature using validation helper
        artifacts = validate_series(
            namespace["feature"],
            min_variance=self.min_variance,
            max_null_rate=self.max_null_rate,
            name="feature",
        )

        # Compute score based on variance
        # Higher variance (up to 1.0) gets better score
        variance = artifacts["feature_variance"]
        score = min(1.0, variance / 1.0)

        return score, artifacts

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"FeatureProblem(name={self.name!r}, "
            f"data_shape={self.data.shape}, "
            f"min_variance={self.min_variance}, "
            f"max_null_rate={self.max_null_rate})"
        )
