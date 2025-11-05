"""
FunctionTestProblem: Simple in-process function testing with test cases.

This module provides a lightweight example of using SecureCodeProblem for
fast, in-process function testing. Suitable for trusted code in controlled
environments (internal team, code challenges, educational contexts).

Example:
    >>> problem = FunctionTestProblem(
    ...     name="add_function",
    ...     function_name="add",
    ...     test_cases=[
    ...         ((2, 3), 5),
    ...         ((0, 0), 0),
    ...         ((-1, 1), 0)
    ...     ]
    ... )
    >>> result = problem.evaluate('''
    ... def add(x, y):
    ...     return x + y
    ... ''')
    >>> result.ok
    True
    >>> result.score
    1.0
"""

from __future__ import annotations

from typing import Any, Callable, List, Tuple

from optelier.problems.secure import SecureCodeProblem
from optelier.problems.validation import run_test_cases


class FunctionTestProblem(SecureCodeProblem):
    """
    Test function implementations against test cases with in-process execution.

    This problem evaluates Python functions by running them against a set of
    test cases. Returns pass rate as fitness score (0.0 to 1.0).

    Security: Uses SecureCodeProblem's AST validation but executes in-process.
    Only use with trusted code in controlled environments.

    Attributes:
        function_name: Name of function to test
        test_cases: List of (inputs, expected) tuples

    Example:
        >>> problem = FunctionTestProblem(
        ...     name="fibonacci",
        ...     function_name="fib",
        ...     test_cases=[
        ...         ((0,), 0),
        ...         ((1,), 1),
        ...         ((5,), 5),
        ...         ((10,), 55)
        ...     ]
        ... )
        >>> code = '''
        ... def fib(n):
        ...     if n <= 1:
        ...         return n
        ...     return fib(n-1) + fib(n-2)
        ... '''
        >>> result = problem.evaluate(code)
        >>> result.score
        1.0
        >>> result.artifacts["passed"]
        4
    """

    def __init__(
        self,
        name: str,
        function_name: str,
        test_cases: List[Tuple[Tuple[Any, ...], Any]],
    ):
        """
        Initialize function test problem.

        Args:
            name: Problem name
            function_name: Name of function to test (e.g., "add", "factorial")
            test_cases: List of (inputs_tuple, expected_output) pairs
                Example: [((1, 2), 3), ((5, 10), 15)]

        Example:
            >>> problem = FunctionTestProblem(
            ...     name="multiply",
            ...     function_name="mul",
            ...     test_cases=[((2, 3), 6), ((4, 5), 20)]
            ... )
        """
        # Pass empty set explicitly - parent class has 'or' logic that would
        # replace empty set with default, so we set it after init
        super().__init__(name=name)
        self.allowed_imports = set()  # No imports allowed for function tests
        self.function_name = function_name
        self.test_cases = test_cases

    def setup_environment(self) -> dict[str, Any]:
        """
        Prepare environment for code execution.

        Returns empty dict since we only need the submitted code,
        no additional data or context.

        Returns:
            dict: Empty dict (no environment variables needed)
        """
        return {}

    def _execute_code(self, code: str, environment: dict[str, Any]) -> dict[str, Any]:
        """
        Execute code in-process using Python exec().

        This provides fast execution but NO security isolation.
        Only use with trusted code.

        Args:
            code: Python code to execute (already validated)
            environment: Variables to inject into namespace (empty for this problem)

        Returns:
            dict: Namespace after execution (contains defined functions/variables)

        Example:
            >>> # Internal use - called by evaluate()
            >>> namespace = problem._execute_code(
            ...     "def add(x, y): return x + y",
            ...     {}
            ... )
            >>> namespace["add"](2, 3)
            5
        """
        namespace = environment.copy()
        exec(code, namespace)
        return namespace

    def validate_output(
        self, namespace: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """
        Validate output and compute score.

        Checks that the required function exists and runs it against
        all test cases using the run_test_cases helper.

        Args:
            namespace: Execution namespace after code runs

        Returns:
            (score, artifacts): Score is pass rate (0-1), artifacts contain test results

        Raises:
            ValueError: If required function not defined

        Example:
            >>> # Internal use - called by evaluate()
            >>> namespace = {"add": lambda x, y: x + y}
            >>> score, artifacts = problem.validate_output(namespace)
            >>> score
            1.0
            >>> artifacts["passed"]
            2
        """
        if self.function_name not in namespace:
            raise ValueError(
                f"Code must define '{self.function_name}' function. "
                f"Found variables: {[k for k in namespace.keys() if not k.startswith('__')]}"
            )

        func: Callable[..., Any] = namespace[self.function_name]
        score, artifacts = run_test_cases(func, self.test_cases)
        return score, artifacts

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"FunctionTestProblem(name={self.name!r}, "
            f"function_name={self.function_name!r}, "
            f"test_cases={len(self.test_cases)})"
        )
