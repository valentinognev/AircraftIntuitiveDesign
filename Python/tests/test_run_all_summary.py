import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

from aid import compare
from aid.paths import results_dir

CESSNA = "Cessna 172"
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _run_all():
    spec = importlib.util.spec_from_file_location(
        "run_all", SCRIPTS / "run_all.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_python_results_for_cessna_exist():
    d = results_dir() / "python" / "Cessna 172"
    assert (d / "status.json").is_file()
    st = json.loads((d / "status.json").read_text())
    assert st["datcom"] in ("ok", "failed")


def _stub_solvers(monkeypatch) -> dict:
    """Replace the three solver leaves with counting stubs carrying the gold's keys."""
    counts: dict = {}

    def leaf(name):
        gold = json.loads(
            (results_dir() / "matlab" / CESSNA / f"{name}.json").read_text()
        )
        stub = {key: 0.0 for key in gold}

        def run(ac, *args, **kwargs):
            counts[name] = counts.get(name, 0) + 1
            return {"status": "ok", "coeffs": stub, "error": None}

        return run

    for attr, name in (
        ("_run_datcom_safe", "datcom"),
        ("_run_tornado", "tornado"),
        ("_run_avl", "avl"),
    ):
        monkeypatch.setattr(compare, attr, leaf(name))
    return counts


@pytest.fixture
def batch_root(monkeypatch, tmp_path):
    """A ``Results/`` root holding a copy of the gold, for the batch to run in."""
    root = tmp_path / "Results"
    shutil.copytree(results_dir() / "matlab", root / "matlab")
    run_all = _run_all()
    monkeypatch.setattr(run_all, "results_dir", lambda: root)
    monkeypatch.setattr(compare, "results_dir", lambda: root)
    monkeypatch.setattr(sys, "argv", ["run_all.py", "--aircraft", CESSNA])
    return root, run_all, _stub_solvers(monkeypatch)


def test_batch_runs_each_solver_once_and_dumps_that_run(batch_root):
    """The batch dump and the compare verdict must be the same run, not two."""
    root, run_all, counts = batch_root

    run_all.main()

    assert counts == {"datcom": 1, "tornado": 1, "avl": 1}
    status = json.loads((root / "python" / CESSNA / "status.json").read_text())
    report = json.loads((root / "compare" / f"{CESSNA}.json").read_text())
    for solver in ("datcom", "tornado", "avl"):
        assert status["sweeps"][solver] == {
            "alpha": report[solver]["alpha"],
            "alpha_source": report[solver]["alpha_source"],
        }


def test_batch_dump_records_the_sweep_each_leg_flew(batch_root):
    root, run_all, _ = batch_root

    run_all.main()

    status = json.loads((root / "python" / CESSNA / "status.json").read_text())
    gold = json.loads(
        (results_dir() / "matlab" / CESSNA / "datcom.json").read_text()
    )["alpha"]
    model = compare._flown_alpha(
        compare.load_jsonc(compare.models_dir() / f"{CESSNA}.jsonc")
    )
    assert status["sweeps"]["datcom"] == {
        "alpha": [float(a) for a in gold],
        "alpha_source": "gold",
    }
    assert status["sweeps"]["tornado"] == {"alpha": model, "alpha_source": "model"}
    assert status["sweeps"]["avl"] == {"alpha": model, "alpha_source": "model"}