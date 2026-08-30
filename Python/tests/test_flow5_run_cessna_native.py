import json
import subprocess
import tempfile
from pathlib import Path

from aid.aircraft import load_jsonc
from aid.flow5_io import write_flow5_deck
from aid.paths import flow5_bin, models_dir


def test_native_cessna_cl_not_identically_zero():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    deck = write_flow5_deck(ac, ("10", "10"))
    exe = flow5_bin()
    assert exe.is_file()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "deck.json"
        path.write_text(json.dumps(deck))
        r = subprocess.run(
            [str(exe), "--deck", str(path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
    assert out["alpha"][0] == -4 or abs(out["alpha"][0] + 4) < 1e-6
    assert any(abs(float(c)) > 1e-6 for c in out["CL"])
    assert abs(float(out["CLa"])) > 1e-6
