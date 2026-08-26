# Python/tests/test_matlab_gold_cessna_tornado.py
import json
from aid.paths import results_dir

def test_cessna_matlab_tornado_gold():
    d = results_dir() / "matlab" / "Cessna 172"
    st = json.loads((d / "status.json").read_text())
    assert st["tornado"] == "ok"
    t = json.loads((d / "tornado.json").read_text())
    assert "CL" in t and "CD" in t and "Cm" in t
