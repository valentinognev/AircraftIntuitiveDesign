# Python/scripts/run_all.py
"""Batch-run Python solvers on aircraft models and compare to MATLAB gold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aid.aircraft import load_jsonc
from aid.compare import compare_to_matlab, run_python
from aid.paths import models_dir, results_dir


def write_python_results(work: Path, python: dict) -> None:
    """Write spec §12 dumps under *work* from *run_python* output."""
    work.mkdir(parents=True, exist_ok=True)
    status: dict = {"error": []}
    for solver in ("datcom", "tornado", "avl"):
        result = python[solver]
        status[solver] = result["status"]
        coeff_path = work / f"{solver}.json"
        if result["status"] == "ok":
            coeff_path.write_text(json.dumps(result["coeffs"], indent=2) + "\n")
        elif coeff_path.is_file():
            coeff_path.unlink()
        if result["status"] == "failed" and result.get("error"):
            status["error"].append(f"{solver}: {result['error']}")
    (work / "status.json").write_text(json.dumps(status, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Python solvers on aircraft models")
    parser.add_argument("--aircraft", help="Process only this aircraft (jsonc stem name)")
    args = parser.parse_args()

    jsonc_files = sorted(models_dir().glob("*.jsonc"))
    if args.aircraft:
        jsonc_files = [p for p in jsonc_files if p.stem == args.aircraft]
        if not jsonc_files:
            raise SystemExit(f"no model {args.aircraft!r}")

    for jsonc in jsonc_files:
        name = jsonc.stem
        ac = load_jsonc(jsonc)
        work = results_dir() / "python" / name
        python = run_python(ac, work)
        write_python_results(work, python)

        matlab_status = results_dir() / "matlab" / name / "status.json"
        if matlab_status.is_file():
            compare_to_matlab(name)
        else:
            print(f"skip compare {name}: no MATLAB gold")


if __name__ == "__main__":
    main()
