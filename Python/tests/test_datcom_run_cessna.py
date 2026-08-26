import json
import numpy as np
from pathlib import Path
from aid.aircraft import load_jsonc
from aid.datcom_run import run_datcom
from aid.paths import models_dir, results_dir

def test_run_datcom_matches_matlab_gold(tmp_path):
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "datcom.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    got = run_datcom(ac, tmp_path / "work")
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)
