# Python/tests/test_datcom_parse_gold.py
import json
from pathlib import Path
from aid.datcom_parse import parse_for006
from aid.paths import results_dir

def test_parse_matlab_gold_for006():
    p = results_dir() / "matlab" / "Cessna 172" / "datcom.out"
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "datcom.json").read_text())
    got = parse_for006(p.read_text())
    import numpy as np
    assert np.allclose(got["alpha"], gold["alpha"], atol=1e-6)
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)
