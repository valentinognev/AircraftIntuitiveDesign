# Python/tests/test_matlab_gold_primary.py
import json
import pytest
from aid.paths import results_dir

PRIMARY = ["Navion", "DA20-C1", "Learjet 23"]

EXPECTED = {
    "Navion": {"datcom": "failed", "tornado": "ok", "avl": "ok"},
    "DA20-C1": {"datcom": "ok", "tornado": "ok", "avl": "ok"},
    "Learjet 23": {"datcom": "ok", "tornado": "ok", "avl": "ok"},
}

@pytest.mark.parametrize("name", PRIMARY)
def test_matlab_primary_gold_status(name):
    st = json.loads((results_dir() / "matlab" / name / "status.json").read_text())
    exp = EXPECTED[name]
    assert st["datcom"] == exp["datcom"]
    assert st["tornado"] == exp["tornado"]
    assert st["avl"] == exp["avl"]
