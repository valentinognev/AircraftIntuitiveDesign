# Python/tests/test_matlab_batch_all.py
import json
from pathlib import Path
from aid.paths import results_dir, matlab_code

def test_all_23_models_attempted():
    summary = results_dir() / "matlab" / "_summary.json"
    assert summary.is_file()
    rows = json.loads(summary.read_text())
    assert len(rows) == 23
    mats = list((matlab_code() / "Models").glob("*.mat"))
    assert len(mats) == 23
    for row in rows:
        assert (results_dir() / "matlab" / row["name"] / "status.json").is_file()
