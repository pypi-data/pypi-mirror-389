"""
SecureCodeProblem: Abstract base class for secure Python code evaluation.

This module provides AST-based security validation for Python code submissions.
It defines a template method pattern for evaluation that enforces:
- Code validation (imports, builtins, length)
- Environment setup
- Code execution (subclass-specific)
- Output validation

Subclasses choose their execution backend (subprocess, docker, etc.) while
inheriting security checks and evaluation flow.
"""

from __future__ import annotations
import ast
import json
import sys
import pickle
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Set, Optional

import docker
from docker.errors import DockerException, ImageNotFound

from optelier.core import EvalResult, Problem


class SecureCodeProblem(ABC, Problem):
    """
    Abstract base class for problems that evaluate Python code with security checks.

    This class provides AST-based validation and defines the evaluation template.
    Subclasses must implement execution strategy (subprocess, docker, etc.).

    Example:
        >>> class MySecureProblem(SecureCodeProblem):
        ...     def __init__(self):
        ...         super().__init__(
        ...             name="my_problem",
        ...             allowed_imports={"pandas", "numpy"},
        ...             max_code_length=5000
        ...         )
        ...
        ...     def setup_environment(self):
        ...         return {"data": [1, 2, 3]}
        ...
        ...     def validate_output(self, namespace):
        ...         if "result" not in namespace:
        ...             raise ValueError("Must assign to 'result'")
        ...         score = 1.0 if namespace["result"] == 6 else 0.0
        ...         return score, {"result": namespace["result"]}
        ...
        ...     def _execute_code(self, code, environment):
        ...         namespace = environment.copy()
        ...         exec(code, namespace)
        ...         return namespace
        ...
        >>> problem = MySecureProblem()
        >>> result = problem.evaluate({"code": "result = sum(data)"})
        >>> result.ok
        True
        >>> result.score
        1.0

    Attributes:
        name: Problem name
        allowed_imports: Set of allowed module names (whitelist)
        forbidden_builtins: Set of forbidden builtin names (blacklist)
        max_code_length: Maximum allowed code length in characters
    """

    def __init__(
        self,
        name: str,
        allowed_imports: Optional[Set[str]] = None,
        forbidden_builtins: Optional[Set[str]] = None,
        max_code_length: int = 10000,
    ):
        """
        Initialize secure code problem.

        Args:
            name: Problem name
            allowed_imports: Set of allowed module names (whitelist).
                Default: {"pandas", "numpy"}
            forbidden_builtins: Set of forbidden builtin names (blacklist).
                Default: {"eval", "exec", "compile", "__import__", "open"}
            max_code_length: Maximum allowed code length in characters.
                Default: 10000

        Example:
            >>> problem = MySecureProblem(
            ...     name="feature_engineering",
            ...     allowed_imports={"pandas", "numpy", "sklearn"},
            ...     forbidden_builtins={"eval", "exec", "compile"},
            ...     max_code_length=5000
            ... )
        """
        self.name = name
        self.allowed_imports = allowed_imports or {"pandas", "numpy"}
        self.forbidden_builtins = forbidden_builtins or {
            "eval",
            "exec",
            "compile",
            "__import__",
            "open",
        }
        self.max_code_length = max_code_length

    def _validate_length(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Check code length against limit.

        Args:
            code: Code string to validate

        Returns:
            (True, None) if valid
            (False, error_message) if too long
        """
        if len(code) > self.max_code_length:
            return False, (
                f"Code exceeds maximum length of {self.max_code_length} characters "
                f"(got {len(code)})"
            )
        return True, None

    def _parse_ast(self, code: str) -> tuple[Optional[ast.Module], Optional[str]]:
        """
        Parse code into AST, return (tree, error).

        Args:
            code: Python code string to parse

        Returns:
            (ast_tree, None) if parsing succeeds
            (None, error_message) if parsing fails
        """
        try:
            tree = ast.parse(code)
            return tree, None
        except SyntaxError as e:
            return None, f"Syntax error on line {e.lineno}: {e.msg}"
        except Exception as e:
            return None, f"Failed to parse code: {e}"

    def _validate_imports(self, tree: ast.Module) -> tuple[bool, Optional[str]]:
        """
        Check all imports are in allowed set using AST visitor.

        Args:
            tree: Parsed AST tree

        Returns:
            (True, None) if all imports allowed
            (False, error_message) if forbidden imports found
        """

        class ImportVisitor(ast.NodeVisitor):
            def __init__(self, allowed: Set[str]):
                self.allowed_imports = allowed
                self.forbidden: list[str] = []

            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    if alias.name not in self.allowed_imports:
                        self.forbidden.append(alias.name)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                if node.module and node.module not in self.allowed_imports:
                    self.forbidden.append(node.module)

        visitor = ImportVisitor(self.allowed_imports)
        visitor.visit(tree)

        if visitor.forbidden:
            return False, (
                f"Forbidden imports: {', '.join(visitor.forbidden)}. "
                f"Allowed: {', '.join(sorted(self.allowed_imports))}"
            )
        return True, None

    def _validate_builtins(self, tree: ast.Module) -> tuple[bool, Optional[str]]:
        """
        Check for forbidden builtin usage using AST visitor.

        Args:
            tree: Parsed AST tree

        Returns:
            (True, None) if no forbidden builtins used
            (False, error_message) if forbidden builtins found
        """

        class BuiltinVisitor(ast.NodeVisitor):
            def __init__(self, forbidden: Set[str]):
                self.forbidden_set = forbidden
                self.violations: list[str] = []

            def visit_Name(self, node: ast.Name) -> None:
                if node.id in self.forbidden_set:
                    self.violations.append(node.id)
                self.generic_visit(node)

        visitor = BuiltinVisitor(self.forbidden_builtins)
        visitor.visit(tree)

        if visitor.violations:
            return False, (
                f"Forbidden builtins used: {', '.join(set(visitor.violations))}"
            )
        return True, None

    def validate_code(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate code using AST analysis.

        Checks performed:
        1. Code length against max_code_length
        2. Syntax validity (AST parsing)
        3. Imports against allowed_imports whitelist
        4. Builtins against forbidden_builtins blacklist

        Args:
            code: Python code string to validate

        Returns:
            (True, None) if valid
            (False, error_message) if invalid

        Example:
            >>> problem = MySecureProblem()
            >>> is_valid, error = problem.validate_code("import pandas\\nresult = 1")
            >>> is_valid
            True
            >>> is_valid, error = problem.validate_code("import os\\nresult = 1")
            >>> is_valid
            False
            >>> "Forbidden imports" in error
            True
        """
        # Check length
        is_valid, error = self._validate_length(code)
        if not is_valid:
            return False, error

        # Parse AST
        tree, error = self._parse_ast(code)
        if tree is None:
            return False, error

        # Check imports
        is_valid, error = self._validate_imports(tree)
        if not is_valid:
            return False, error

        # Check builtins
        is_valid, error = self._validate_builtins(tree)
        if not is_valid:
            return False, error

        return True, None

    @abstractmethod
    def setup_environment(self) -> dict[str, Any]:
        """
        Prepare environment for code execution.

        Subclasses implement this to provide the execution namespace.
        The returned dict contains variables that will be available to
        the submitted code.

        Returns:
            dict: Variables to inject into execution namespace

        Example:
            >>> def setup_environment(self):
            ...     return {
            ...         "df": self.test_data,
            ...         "ctx": self.context,
            ...         "train_size": 1000
            ...     }
        """
        pass

    @abstractmethod
    def validate_output(
        self, namespace: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """
        Validate output and compute score.

        Subclasses implement this to check the execution result and
        compute a score. Should raise ValueError/AssertionError if
        output is invalid.

        Args:
            namespace: Execution namespace after code runs

        Returns:
            (score, artifacts): Score (0-1) and artifacts dict

        Example:
            >>> def validate_output(self, namespace):
            ...     if "result" not in namespace:
            ...         raise ValueError("Code must assign to 'result'")
            ...     expected = self.expected_output
            ...     actual = namespace["result"]
            ...     score = compute_similarity(expected, actual)
            ...     artifacts = {
            ...         "output_length": len(actual),
            ...         "expected_length": len(expected)
            ...     }
            ...     return score, artifacts
        """
        pass

    @abstractmethod
    def _execute_code(self, code: str, environment: dict[str, Any]) -> dict[str, Any]:
        """
        Execute code and return resulting namespace.

        Subclasses implement this to provide execution backend
        (subprocess, docker, in-process, etc.).

        Args:
            code: Validated Python code to execute
            environment: Variables to inject into namespace

        Returns:
            dict: Namespace after execution (includes environment + new variables)

        Example:
            >>> def _execute_code(self, code, environment):
            ...     # Simple in-process execution (NOT SECURE - use subprocess/docker)
            ...     namespace = environment.copy()
            ...     exec(code, namespace)
            ...     return namespace
        """
        pass

    def evaluate(self, submission: Any) -> EvalResult:
        """
        Evaluate submission using template method pattern.

        Flow: validate → setup → execute → validate output

        This method orchestrates the evaluation process:
        1. Extract code from submission (dict or string)
        2. Validate code (AST analysis)
        3. Setup environment (subclass-specific)
        4. Execute code (subclass-specific)
        5. Validate output and compute score (subclass-specific)

        Args:
            submission: Dict with "code" key or raw code string

        Returns:
            EvalResult with score, ok status, artifacts, errors

        Example:
            >>> problem = MySecureProblem()
            >>> result = problem.evaluate({"code": "result = sum(data)"})
            >>> result.ok
            True
            >>> result = problem.evaluate("import os")
            >>> result.ok
            False
            >>> "Forbidden imports" in result.error
            True
        """
        # Extract code from submission
        if isinstance(submission, dict):
            if "code" not in submission:
                return EvalResult(
                    score=-float("inf"),
                    ok=False,
                    error="Submission dict must have 'code' key",
                )
            code = submission["code"]
        elif isinstance(submission, str):
            code = submission
        else:
            return EvalResult(
                score=-float("inf"),
                ok=False,
                error=f"Invalid submission type: {type(submission).__name__}",
            )

        # Validate code
        is_valid, error = self.validate_code(code)
        if not is_valid:
            return EvalResult(
                score=-float("inf"), ok=False, error=f"Code validation failed: {error}"
            )

        # Setup environment
        try:
            environment = self.setup_environment()
        except Exception as e:
            return EvalResult(
                score=-float("inf"), ok=False, error=f"Environment setup failed: {e}"
            )

        # Execute code (subclass-specific)
        try:
            namespace = self._execute_code(code, environment)
        except Exception as e:
            return EvalResult(
                score=-float("inf"), ok=False, error=f"Execution failed: {e}"
            )

        # Validate output and compute score
        try:
            score, artifacts = self.validate_output(namespace)
            return EvalResult(score=score, ok=True, artifacts=artifacts)
        except Exception as e:
            return EvalResult(
                score=-float("inf"), ok=False, error=f"Output validation failed: {e}"
            )


class SubprocessProblem(SecureCodeProblem):
    """
    Execute code in subprocess with timeout and pickle serialization.

    Provides medium security through process isolation. Suitable for
    trusted or semi-trusted environments (internal team, controlled access).

    Features:
    - Process isolation: Crashes don't affect parent process
    - Timeout protection: Configurable execution time limit
    - Pickle serialization: Supports DataFrames and complex objects
    - Error propagation: Clear error messages from subprocess
    - Automatic cleanup: Temporary files removed after execution

    Overhead: ~400ms (process spawn + pickle I/O)

    Example:
        >>> class MyProblem(SubprocessProblem):
        ...     def __init__(self):
        ...         super().__init__(name="test", timeout=30)
        ...
        ...     def setup_environment(self):
        ...         return {"x": 5}
        ...
        ...     def validate_output(self, namespace):
        ...         if "result" not in namespace:
        ...             raise ValueError("Must assign to 'result'")
        ...         score = 1.0 if namespace["result"] == 10 else 0.0
        ...         return score, {"result": namespace["result"]}
        ...
        >>> problem = MyProblem()
        >>> result = problem.evaluate({"code": "result = x * 2"})
        >>> result.score
        1.0

    Attributes:
        timeout: Maximum execution time in seconds
    """

    def __init__(
        self,
        name: str,
        timeout: int = 30,
        allowed_imports: Optional[Set[str]] = None,
        forbidden_builtins: Optional[Set[str]] = None,
        max_code_length: int = 10000,
    ):
        """
        Initialize subprocess problem.

        Args:
            name: Problem name
            timeout: Maximum execution time in seconds (default 30)
            allowed_imports: Set of allowed module names (default {"pandas", "numpy"})
            forbidden_builtins: Set of forbidden builtin names
                (default {"eval", "exec", "compile", "__import__", "open"})
            max_code_length: Maximum code length in characters (default 10000)

        Example:
            >>> problem = SubprocessProblem(
            ...     name="feature_eng",
            ...     timeout=60,
            ...     allowed_imports={"pandas", "numpy", "sklearn"}
            ... )
        """
        super().__init__(name, allowed_imports, forbidden_builtins, max_code_length)
        self.timeout = timeout

    def _write_environment(self, environment: dict[str, Any], path: Path) -> None:
        """
        Write environment to pickle file.

        Args:
            environment: Dict to serialize
            path: Path to pickle file

        Raises:
            RuntimeError: If serialization fails
        """
        try:
            with open(path, "wb") as f:
                pickle.dump(environment, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            raise RuntimeError(f"Failed to serialize environment: {e}")

    def _read_result(self, path: Path) -> dict[str, Any]:
        """
        Read result namespace from pickle file.

        Args:
            path: Path to pickle file

        Returns:
            Deserialized namespace dict

        Raises:
            RuntimeError: If file missing or deserialization fails
        """
        try:
            with open(path, "rb") as f:
                result: dict[str, Any] = pickle.load(f)
                return result
        except FileNotFoundError:
            raise RuntimeError("Subprocess did not produce result file")
        except Exception as e:
            raise RuntimeError(f"Failed to deserialize result: {e}")

    def _create_wrapper_script(
        self, env_path: Path, code_path: Path, result_path: Path
    ) -> str:
        """
        Generate Python script to execute in subprocess.

        The wrapper script:
        1. Loads environment from pickle
        2. Executes user code
        3. Saves result namespace to pickle
        4. Exits with error code on exception

        Args:
            env_path: Path to environment pickle file
            code_path: Path to code file
            result_path: Path to result pickle file

        Returns:
            Python script as string
        """
        return f"""
import pickle
import sys
import traceback
import types

try:
    # Load environment
    with open("{env_path}", "rb") as f:
        namespace = pickle.load(f)

    # Execute user code
    with open("{code_path}") as f:
        code = f.read()

    exec(code, namespace)

    # Save result namespace (filter out non-picklable objects)
    # Skip modules, types, and builtins that can't be pickled
    picklable = {{}}
    for key, value in namespace.items():
        if not key.startswith("__"):
            # Skip module objects and type objects
            if isinstance(value, (types.ModuleType, type)):
                continue
            # Try to pickle the value
            try:
                pickle.dumps(value)
                picklable[key] = value
            except (TypeError, AttributeError, pickle.PicklingError):
                # Skip non-picklable values
                pass

    with open("{result_path}", "wb") as f:
        pickle.dump(picklable, f, protocol=pickle.HIGHEST_PROTOCOL)

except Exception as e:
    # Write error to stderr and exit with error code
    traceback.print_exc()
    sys.exit(1)
"""

    def _execute_code(self, code: str, environment: dict[str, Any]) -> dict[str, Any]:
        """
        Execute code in subprocess with timeout.

        Creates temporary directory, serializes environment, runs code
        in isolated subprocess, and deserializes result. Automatically
        cleans up temporary files.

        Args:
            code: Python code to execute (already validated)
            environment: Variables to inject into namespace

        Returns:
            dict: Namespace after execution (includes environment + new variables)

        Raises:
            TimeoutError: If execution exceeds timeout
            RuntimeError: If subprocess fails or produces no result

        Example:
            >>> # Internal use - called by evaluate()
            >>> namespace = problem._execute_code(
            ...     "result = x * 2",
            ...     {"x": 5}
            ... )
            >>> namespace["result"]
            10
        """
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)

            # Write environment to pickle
            env_path = tmpdir / "env.pkl"
            self._write_environment(environment, env_path)

            # Write code to file
            code_path = tmpdir / "code.py"
            code_path.write_text(code, encoding="utf-8")

            # Create and write wrapper script
            result_path = tmpdir / "result.pkl"
            wrapper_script = self._create_wrapper_script(
                env_path, code_path, result_path
            )
            wrapper_path = tmpdir / "wrapper.py"
            wrapper_path.write_text(wrapper_script, encoding="utf-8")

            # Execute subprocess
            try:
                result = subprocess.run(
                    [sys.executable, str(wrapper_path)],
                    timeout=self.timeout,
                    capture_output=True,
                    text=True,
                    cwd=str(tmpdir),
                )
            except subprocess.TimeoutExpired:
                raise TimeoutError(
                    f"Code execution exceeded {self.timeout} second timeout"
                )

            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                raise RuntimeError(f"Subprocess execution failed:\n{error_msg}")

            # Load and return result
            return self._read_result(result_path)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"SubprocessProblem(name={self.name!r}, timeout={self.timeout}, "
            f"allowed_imports={len(self.allowed_imports)})"
        )


class DockerProblem(SecureCodeProblem):
    """
    Execute code in Docker container with resource limits and network isolation.

    Provides maximum security through containerization. Suitable for
    untrusted code (external contributors, competitions, public APIs).

    Features:
    - Complete isolation: Separate filesystem, process space, network
    - Resource limits: Memory, CPU constraints enforced by Docker
    - Network isolation: Disabled by default
    - Read-only execution: Prevents host filesystem modification
    - JSON serialization: Secure, language-agnostic data transfer
    - Automatic cleanup: Containers removed after execution

    Overhead: ~600ms (container start + volume mount + JSON I/O)

    Requires Docker daemon running on host system.

    Example:
        >>> class UntrustedMathProblem(DockerProblem):
        ...     def __init__(self):
        ...         super().__init__(
        ...             name="untrusted_math",
        ...             image="python:3.10-slim",
        ...             timeout=30,
        ...             memory_limit="256m"
        ...         )
        ...
        ...     def setup_environment(self):
        ...         return {"x": 5, "y": 10}
        ...
        ...     def validate_output(self, namespace):
        ...         if "result" not in namespace:
        ...             raise ValueError("Must assign to 'result'")
        ...         score = 1.0 if namespace["result"] == 15 else 0.0
        ...         return score, {"result": namespace["result"]}
        ...
        >>> problem = UntrustedMathProblem()
        >>> result = problem.evaluate({"code": "result = x + y"})
        >>> result.score
        1.0

    Attributes:
        image: Docker image to use
        timeout: Maximum execution time in seconds
        memory_limit: Container memory limit (e.g., "512m", "1g")
        client: Docker client instance
    """

    def __init__(
        self,
        name: str,
        image: str = "python:3.10-slim",
        timeout: int = 60,
        memory_limit: str = "512m",
        allowed_imports: Optional[Set[str]] = None,
        forbidden_builtins: Optional[Set[str]] = None,
        max_code_length: int = 10000,
    ):
        """
        Initialize Docker problem.

        Args:
            name: Problem name
            image: Docker image to use (default: python:3.10-slim)
            timeout: Maximum execution time in seconds (default 60)
            memory_limit: Container memory limit (default: 512m)
            allowed_imports: Set of allowed module names (default {"pandas", "numpy"})
            forbidden_builtins: Set of forbidden builtin names
                (default {"eval", "exec", "compile", "__import__", "open"})
            max_code_length: Maximum code length in characters (default 10000)

        Raises:
            DockerException: If Docker daemon not available

        Example:
            >>> problem = DockerProblem(
            ...     name="secure_problem",
            ...     image="python:3.10-slim",
            ...     timeout=30,
            ...     memory_limit="256m",
            ...     allowed_imports={"pandas", "numpy", "sklearn"}
            ... )
        """
        super().__init__(name, allowed_imports, forbidden_builtins, max_code_length)
        self.image = image
        self.timeout = timeout
        self.memory_limit = memory_limit

        # Initialize Docker client
        try:
            self.client = docker.from_env()
            # Verify image exists or pull it
            self._ensure_image()
        except DockerException as e:
            raise DockerException(
                f"Docker not available. Please install and start Docker daemon.\n"
                f"Error: {e}"
            )

    def _ensure_image(self) -> None:
        """
        Ensure Docker image exists, pull if necessary.

        Checks if the configured image is available locally. If not,
        pulls it from Docker Hub.

        Raises:
            ImageNotFound: If image cannot be found or pulled
            DockerException: If pull operation fails
        """
        try:
            self.client.images.get(self.image)
        except ImageNotFound:
            print(f"Pulling Docker image {self.image}...")
            self.client.images.pull(self.image)

    def serialize_environment(self, environment: dict[str, Any]) -> str:
        """
        Convert environment to JSON string.

        Default implementation serializes simple types (int, str, list, dict).
        Override this method to handle complex types like DataFrames.

        Args:
            environment: Environment dict to serialize

        Returns:
            str: JSON string

        Raises:
            TypeError: If environment contains non-JSON-serializable types

        Example override for DataFrames:
            >>> def serialize_environment(self, environment):
            ...     serializable = {}
            ...     for key, value in environment.items():
            ...         if isinstance(value, pd.DataFrame):
            ...             serializable[key] = value.to_dict('records')
            ...         else:
            ...             serializable[key] = value
            ...     return json.dumps(serializable)
        """
        try:
            return json.dumps(environment, indent=2)
        except TypeError as e:
            raise TypeError(
                f"Environment contains non-JSON-serializable types: {e}\n"
                f"Override serialize_environment() to handle complex types"
            )

    def deserialize_result(self, result_json: str) -> dict[str, Any]:
        """
        Parse result JSON to dict.

        Default implementation parses JSON to dict. Override this method
        to reconstruct complex types from their JSON representation.

        Args:
            result_json: JSON string from container

        Returns:
            dict: Parsed result

        Raises:
            RuntimeError: If JSON parsing fails

        Example override for DataFrames:
            >>> def deserialize_result(self, result_json):
            ...     data = json.loads(result_json)
            ...     if 'df' in data and isinstance(data['df'], dict):
            ...         if data['df'].get('type') == 'dataframe':
            ...             data['df'] = pd.DataFrame(data['df']['data'])
            ...     return data
        """
        try:
            result: dict[str, Any] = json.loads(result_json)
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse result JSON: {e}")

    def _create_wrapper_script(self) -> str:
        """
        Generate Python script to execute in container.

        The wrapper script:
        1. Loads environment from JSON file
        2. Executes user code
        3. Filters namespace to JSON-serializable values
        4. Saves result to JSON file
        5. Writes errors to error.json on failure

        Returns:
            Python script as string
        """
        return """
import json
import sys
import traceback

try:
    # Load environment from JSON
    with open("/data/env.json") as f:
        namespace = json.load(f)

    # Execute user code
    with open("/data/code.py") as f:
        code = f.read()

    exec(code, namespace)

    # Save result namespace
    # Note: Only JSON-serializable values will be saved
    serializable = {}
    for key, value in namespace.items():
        if not key.startswith("__"):
            try:
                json.dumps(value)
                serializable[key] = value
            except (TypeError, ValueError):
                # Skip non-serializable values
                pass

    with open("/data/result.json", "w") as f:
        json.dump(serializable, f, indent=2)

except Exception as e:
    # Write error details
    error_info = {
        "error": str(e),
        "traceback": traceback.format_exc()
    }
    with open("/data/error.json", "w") as f:
        json.dump(error_info, f, indent=2)
    sys.exit(1)
"""

    def _execute_code(self, code: str, environment: dict[str, Any]) -> dict[str, Any]:
        """
        Execute code in Docker container with resource limits.

        Creates temporary directory, serializes environment to JSON,
        runs code in isolated container, and deserializes result.
        Container is automatically removed after execution.

        Args:
            code: Python code to execute (already validated)
            environment: Variables to inject into namespace

        Returns:
            dict: Namespace after execution (includes environment + new variables)

        Raises:
            TimeoutError: If execution exceeds timeout
            RuntimeError: If container fails or produces no result
            DockerException: If Docker error occurs

        Example:
            >>> # Internal use - called by evaluate()
            >>> namespace = problem._execute_code(
            ...     "result = x * 2",
            ...     {"x": 5}
            ... )
            >>> namespace["result"]
            10
        """
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)

            # Write environment to JSON
            env_json = self.serialize_environment(environment)
            (tmpdir / "env.json").write_text(env_json, encoding="utf-8")

            # Write code
            (tmpdir / "code.py").write_text(code, encoding="utf-8")

            # Write wrapper script
            wrapper_script = self._create_wrapper_script()
            (tmpdir / "wrapper.py").write_text(wrapper_script, encoding="utf-8")

            # Run container
            container: Any = None
            try:
                container = self.client.containers.run(
                    self.image,
                    command=["python", "/data/wrapper.py"],
                    volumes={str(tmpdir): {"bind": "/data", "mode": "rw"}},
                    mem_limit=self.memory_limit,
                    network_mode="none",  # Disable network
                    detach=True,
                    remove=True,  # Auto-remove after exit
                )

                # Wait for completion with timeout
                result = container.wait(timeout=self.timeout)

            except Exception as e:
                # Catch timeout or other errors
                if "timeout" in str(e).lower():
                    if container:
                        try:
                            container.kill()
                        except Exception:
                            pass
                    raise TimeoutError(
                        f"Container execution exceeded {self.timeout} second timeout"
                    )
                raise RuntimeError(f"Container execution failed: {e}")

            # Check exit code
            if result["StatusCode"] != 0:
                # Try to read error details
                error_path = tmpdir / "error.json"
                if error_path.exists():
                    error_data = json.loads(error_path.read_text())
                    raise RuntimeError(
                        f"Container execution failed:\n{error_data['traceback']}"
                    )
                else:
                    # Fallback: try to get logs
                    try:
                        logs = container.logs().decode()
                        raise RuntimeError(f"Container failed:\n{logs}")
                    except Exception:
                        raise RuntimeError(
                            f"Container failed with exit code {result['StatusCode']}"
                        )

            # Read result
            result_path = tmpdir / "result.json"
            if not result_path.exists():
                raise RuntimeError("Container did not produce result file")

            result_json = result_path.read_text(encoding="utf-8")
            return self.deserialize_result(result_json)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"DockerProblem(name={self.name!r}, image={self.image!r}, "
            f"timeout={self.timeout}, memory_limit={self.memory_limit!r})"
        )
