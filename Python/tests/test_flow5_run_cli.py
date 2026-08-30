import json
import subprocess
import tempfile
from pathlib import Path

from aid.paths import flow5_bin


def test_flow5_run_usage_exit_2():
    exe = flow5_bin()
    assert exe.is_file(), "build FLOW5/run/flow5_run"
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    assert r.returncode == 2
    assert "usage" in r.stderr.lower()


def test_flow5_run_deck_skeleton_json_shape():
    exe = flow5_bin()
    assert exe.is_file(), "build FLOW5/run/flow5_run"
    deck = {"polar": {"alpha_deg": [-2.0, 0.0, 2.0]}}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(deck, f)
        deck_path = f.name
    try:
        r = subprocess.run(
            [str(exe), "--deck", deck_path],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert len(out["alpha"]) == 3
        assert len(out["CL"]) == 3
        assert len(out["CD"]) == 3
        assert len(out["Cm"]) == 3
        assert out["CLa"] == 0
        assert out["Cma"] == 0
    finally:
        Path(deck_path).unlink(missing_ok=True)
