# Python/tests/test_matlab_gold_cessna_avl.py
import json
from aid.paths import results_dir

def test_cessna_matlab_avl_gold():
    d = results_dir() / "matlab" / "Cessna 172"
    st = json.loads((d / "status.json").read_text())
    assert st["avl"] == "ok"
    a = json.loads((d / "avl.json").read_text())
    assert "CLa" in a
    assert (d / "geometry.st").is_file()
