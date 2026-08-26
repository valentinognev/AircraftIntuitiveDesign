# Python/tests/test_matlab_gold_cessna_datcom.py
import json
from pathlib import Path
from aid.paths import results_dir

def test_cessna_matlab_datcom_gold():
    d = results_dir() / "matlab" / "Cessna 172"
    st = json.loads((d / "status.json").read_text())
    assert st["datcom"] == "ok"
    coef = json.loads((d / "datcom.json").read_text())
    assert "cl" in coef and "alpha" in coef
    assert len(coef["alpha"]) >= 3
