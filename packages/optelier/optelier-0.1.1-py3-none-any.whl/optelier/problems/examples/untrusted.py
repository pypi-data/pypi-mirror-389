"""UntrustedCodeProblem: Maximum security for untrusted code execution.

This module provides a concrete implementation using DockerProblem for evaluating
untrusted code submissions (e.g., from LLMs, code competitions, public APIs).

The problem runs test cases against a submitted function with maximum security:
- Docker container isolation
- Restrictive import whitelist (only math, statistics, json)
- Network disabled
- Memory limits enforced
- Timeout protection

Example:
    >>> problem = UntrustedCodeProblem(
    ...     name="sum_two_numbers",
    ...     function_name="add",
    ...     test_cases=[
    ...         ((1, 2), 3),
    ...         ((5, 10), 15),
    ...     ]
    ... )
    >>> result = problem.evaluate({
    ...     "code": "def add(x, y): return x + y"
    ... })
    >>> result.score
    1.0
"""

from __future__ import annotations

from typing import Any, List, Tuple

from optelier.problems.secure import DockerProblem
from optelier.problems.validation import run_test_cases


class UntrustedCodeProblem(DockerProblem):
    """
    Problem for running untrusted code against test cases with maximum security.

    This problem is designed for scenarios where the code cannot be trusted:
    - LLM-generated code submissions
    - Public code competitions
    - External contributor submissions
    - API endpoints accepting arbitrary code

    Security features:
    - Complete Docker isolation (separate filesystem, process space)
    - Restrictive import whitelist (math, statistics, json only)
    - Network disabled
    - Memory limits enforced (default 256MB)
    - Short timeout (default 60s)
    - No access to host filesystem

    The problem runs test cases against a submitted function and returns
    the pass rate as the score. Test cases are tuples of (inputs, expected_output).

    Example:
        >>> # Create problem for simple math function
        >>> problem = UntrustedCodeProblem(
        ...     name="fibonacci",
        ...     function_name="fib",
        ...     test_cases=[
        ...         ((0,), 0),
        ...         ((1,), 1),
        ...         ((5,), 5),
        ...         ((10,), 55),
        ...     ]
        ... )
        >>>
        >>> # Evaluate correct solution
        >>> code = '''
        ... def fib(n):
        ...     if n <= 1:
        ...         return n
        ...     a, b = 0, 1
        ...     for _ in range(n - 1):
        ...         a, b = b, a + b
        ...     return b
        ... '''
        >>> result = problem.evaluate({"code": code})
        >>> result.score
        1.0
        >>> result.artifacts["passed"]
        4
        >>>
        >>> # Evaluate incorrect solution
        >>> bad_code = "def fib(n): return n * 2"
        >>> result = problem.evaluate({"code": bad_code})
        >>> result.score
        0.25
        >>> result.artifacts["passed"]
        1
        >>> result.artifacts["failed"]
        3

    Attributes:
        function_name: Name of the function to test
        test_cases: List of (input_tuple, expected_output) pairs
    """

    def __init__(
        self,
        name: str,
        function_name: str,
        test_cases: List[Tuple[Tuple[Any, ...], Any]],
        image: str = "python:3.10-slim",
        timeout: int = 60,
        memory_limit: str = "256m",
    ):
        """
        Initialize untrusted code problem.

        Args:
            name: Problem name
            function_name: Name of the function that code must define
            test_cases: List of (inputs, expected) tuples where inputs is
                a tuple of arguments to pass to the function
            image: Docker image to use (default: python:3.10-slim)
            timeout: Maximum execution time in seconds (default: 60)
            memory_limit: Container memory limit (default: 256m)

        Example:
            >>> problem = UntrustedCodeProblem(
            ...     name="is_palindrome",
            ...     function_name="is_palindrome",
            ...     test_cases=[
            ...         (("racecar",), True),
            ...         (("hello",), False),
            ...         (("",), True),
            ...     ],
            ...     timeout=30,
            ...     memory_limit="128m"
            ... )
        """
        # Very restrictive imports - only basic math and data handling
        allowed_imports = {"math", "statistics", "json"}

        super().__init__(
            name=name,
            image=image,
            timeout=timeout,
            memory_limit=memory_limit,
            allowed_imports=allowed_imports,
            max_code_length=10000,
        )

        self.function_name = function_name
        self.test_cases = test_cases

    def setup_environment(self) -> dict[str, Any]:
        """
        Setup environment for code execution.

        Returns empty dict since test cases don't need external data.

        Returns:
            dict: Empty environment dict

        Example:
            >>> problem = UntrustedCodeProblem("test", "func", [])
            >>> env = problem.setup_environment()
            >>> env
            {}
        """
        return {}

    def validate_output(
        self, namespace: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """
        Validate that function is defined and run test cases.

        Checks that the submitted code defines the expected function,
        then runs all test cases against it. Score is the pass rate
        (number passed / total tests).

        Args:
            namespace: Execution namespace after code runs

        Returns:
            (score, artifacts): Score is pass rate (0-1), artifacts contain
                test results with passed/failed counts and failure details

        Raises:
            ValueError: If function is not defined in namespace

        Example:
            >>> problem = UntrustedCodeProblem(
            ...     name="add",
            ...     function_name="add",
            ...     test_cases=[((1, 2), 3), ((5, 10), 15)]
            ... )
            >>> # Simulate namespace after execution
            >>> namespace = {"add": lambda x, y: x + y}
            >>> score, artifacts = problem.validate_output(namespace)
            >>> score
            1.0
            >>> artifacts["passed"]
            2
            >>> artifacts["failed"]
            0
        """
        if self.function_name not in namespace:
            raise ValueError(
                f"Code must define '{self.function_name}' function. "
                f"Found variables: {', '.join(k for k in namespace.keys() if not k.startswith('__'))}"
            )

        func = namespace[self.function_name]
        score, artifacts = run_test_cases(func, self.test_cases)

        return score, artifacts

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"UntrustedCodeProblem(name={self.name!r}, "
            f"function={self.function_name!r}, "
            f"test_cases={len(self.test_cases)}, "
            f"timeout={self.timeout}s, "
            f"memory={self.memory_limit})"
        )
