# Python/tests/test_avl_run_cessna.py
import json
from pathlib import Path
from aid.aircraft import load_jsonc
from aid.avl_io import run_avl_full
from aid.paths import models_dir, results_dir

def test_avl_cla_matches_matlab(tmp_path):
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "avl.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    got = run_avl_full(ac, ("10", "10"), tmp_path)
    assert abs(got["CLa"] - gold["CLa"]) < 1e-6
