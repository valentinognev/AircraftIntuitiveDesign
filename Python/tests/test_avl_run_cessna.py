# Python/tests/test_avl_run_cessna.py
import json
from pathlib import Path
from aid.aircraft import load_jsonc
from aid.avl_io import run_avl_full
from aid.paths import models_dir, results_dir

def test_avl_cla_matches_matlab(tmp_path):
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "avl.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    schedule = [float(a) for a in ac.AERO["ALSCHD"]]
    got = run_avl_full(ac, ("10", "10"), tmp_path)
    assert got["alpha"] == schedule or _solved_matches(got["alpha"], schedule)
    assert len(got["CLtot"]) == len(schedule)
    assert len(got["CDtot"]) == len(schedule)
    assert len(got["CZtot"]) == len(schedule)
    assert len(got["CXtot"]) == len(schedule)
    assert max(got["CLtot"]) - min(got["CLtot"]) > 1e-3
    assert max(got["CDtot"]) - min(got["CDtot"]) > 1e-6
    assert got["alpha"].index(0.0) >= 0
    assert abs(got["ref"]["CLa"] - gold["CLa"]) < 1e-6


def _solved_matches(solved, schedule) -> bool:
    if len(solved) != len(schedule):
        return False
    return all(abs(a - b) < 1e-2 for a, b in zip(solved, schedule))
