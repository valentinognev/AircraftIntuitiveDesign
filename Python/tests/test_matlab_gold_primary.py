# Python/tests/test_matlab_gold_primary.py
import json
import pytest
from aid.paths import results_dir

PRIMARY = ["Navion", "DA20-C1", "Learjet 23"]

@pytest.mark.parametrize("name", PRIMARY)
def test_matlab_primary_three_ok(name):
    st = json.loads((results_dir() / "matlab" / name / "status.json").read_text())
    assert st["datcom"] == "ok"
    assert st["tornado"] == "ok"
    assert st["avl"] == "ok"
