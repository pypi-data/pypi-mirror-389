from __future__ import annotations
import argparse
import sys
import json
from .core import evaluate, load_submission
from .problems import REGISTRY


def main(argv=None):
    argv = argv or sys.argv[1:]
    ap = argparse.ArgumentParser(prog="optelier")
    sub = ap.add_subparsers(dest="cmd", required=True)

    runp = sub.add_parser("run", help="Run a problem with a submission")
    runp.add_argument("problem", choices=sorted(REGISTRY.keys()))
    runp.add_argument("--submission", required=True, help="Path to .py or .json")
    runp.add_argument("--fixtures-dir", default="examples/fixtures",
                      help="Directory containing fixture files")
    runp.add_argument("--print-artifacts", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "run":
        # Create problem instance with fixtures directory
        problem = REGISTRY[args.problem](fixtures_dir=args.fixtures_dir)

        # Load submission
        subm = load_submission(args.submission)

        # Evaluate
        res = evaluate(problem, subm)

        # Print results
        print(json.dumps({
            "ok": res.ok,
            "score": res.score,
            "time_ms": res.time_ms
        }, indent=2))

        if args.print_artifacts:
            print("\n# artifacts\n" + json.dumps(res.artifacts, indent=2))

        if not res.ok:
            print("\n# error\n" + (res.error or ""))


if __name__ == "__main__":
    main()
