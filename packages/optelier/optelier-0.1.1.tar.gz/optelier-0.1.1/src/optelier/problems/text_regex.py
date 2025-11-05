from __future__ import annotations
import re
import pathlib
import tempfile
import subprocess
import sys
import os
from ..core import EvalResult


class TextRegexProblem:
    """
    Evaluates regex patterns against a labeled text dataset.

    Submission format:
    - JSON dict: {"pattern": "regex"}
    - Python script: {"kind": "python_script", "code": "..."} that prints pattern

    Contract:
    - text.txt contains lines labeled "OK:" (should match) or "NO:" (should not match)
    - Scoring: F1 score of pattern matches
    """

    name = "text-regex"

    def __init__(self, fixtures_dir: str = "examples/fixtures"):
        """
        Args:
            fixtures_dir: Directory containing text.txt fixture
        """
        self.fixtures_dir = fixtures_dir

    def evaluate(self, submission: dict) -> EvalResult:
        """
        Evaluate a regex pattern submission.

        Args:
            submission: dict with {"pattern": "..."} or {"kind": "python_script", "code": "..."}

        Returns:
            EvalResult: Score is F1, artifacts contain precision, recall, pattern
        """
        # Extract pattern
        if submission.get("kind") == "python_script":
            # Execute script and capture pattern from stdout
            tmpdir = tempfile.TemporaryDirectory()
            script_path = os.path.join(tmpdir.name, "candidate.py")
            with open(script_path, "w") as f:
                f.write(submission["code"])
            out = subprocess.check_output([sys.executable, script_path]).decode().strip()
            pattern = out
        else:
            pattern = submission.get("pattern", "")

        # Load labeled text
        text_path = pathlib.Path(os.path.join(self.fixtures_dir, "text.txt"))
        lines = text_path.read_text().splitlines()

        positives = [ln for ln in lines if ln.startswith("OK:")]
        negatives = [ln for ln in lines if ln.startswith("NO:")]

        # Evaluate pattern
        rx = re.compile(pattern)
        tp = sum(1 for ln in positives if rx.search(ln))
        fp = sum(1 for ln in negatives if rx.search(ln))
        fn = sum(1 for ln in positives if not rx.search(ln))

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        # Return detailed result
        return EvalResult(
            score=f1,
            ok=True,
            artifacts={
                "pattern": pattern,
                "precision": precision,
                "recall": recall,
                "f1": f1
            },
            error=None
        )
