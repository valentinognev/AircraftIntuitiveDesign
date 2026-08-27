# Python/tests/test_run_all_summary.py
import json
from aid.paths import results_dir


def test_python_results_for_cessna_exist():
    d = results_dir() / "python" / "Cessna 172"
    assert (d / "status.json").is_file()
    st = json.loads((d / "status.json").read_text())
    assert st["datcom"] in ("ok", "failed")
