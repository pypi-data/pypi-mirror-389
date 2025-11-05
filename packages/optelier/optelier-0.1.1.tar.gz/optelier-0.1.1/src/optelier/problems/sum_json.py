from __future__ import annotations
import json
import tempfile
import subprocess
import sys
import os


class SumJSONProblem:
    """
    Evaluates Python scripts that read a JSON file with numbers and output their sum.

    Submission format: dict with {"kind": "python_script", "code": "..."}
    or use load_submission("file.py") which returns this format.

    Contract:
    - Script is executed as: python script.py <input.json> <output.json>
    - input.json contains: {"numbers": [1, 2, 3, ...]}
    - Script must write: {"sum": <int>} to output.json
    """

    name = "sum-json"

    def __init__(self, fixtures_dir: str = "examples/fixtures"):
        """
        Args:
            fixtures_dir: Directory containing numbers.json fixture
        """
        self.fixtures_dir = fixtures_dir

    def evaluate(self, submission: dict) -> float:
        """
        Evaluate a Python script submission.

        Args:
            submission: dict with {"kind": "python_script", "code": "..."}

        Returns:
            float: 1.0 if sum is correct, 0.0 otherwise
        """
        assert submission.get("kind") == "python_script", "Submission must be a Python script"
        code = submission["code"]

        # Create temp directory for execution
        tmpdir = tempfile.TemporaryDirectory()
        in_path = os.path.join(self.fixtures_dir, "numbers.json")
        out_path = os.path.join(tmpdir.name, "output.json")
        script_path = os.path.join(tmpdir.name, "candidate.py")

        # Write script and execute
        with open(script_path, "w") as f:
            f.write(code)

        subprocess.run([sys.executable, script_path, in_path, out_path], check=True)

        # Load result
        with open(out_path) as f:
            result = json.load(f)

        # Load expected
        with open(in_path) as f:
            data = json.load(f)

        expected = sum(data["numbers"])
        got = result.get("sum")

        return 1.0 if got == expected else 0.0
