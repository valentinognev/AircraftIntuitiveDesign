from pathlib import Path
from aid.aircraft import load_jsonc
from aid.datcom_io import write_for005
from aid.paths import models_dir

def test_full_for005_cessna(tmp_path):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit="ft")
    text = p.read_text()
    assert "CASEID" in text
    assert "$FLTCON" in text and "$WGPLNF" in text
    assert "NACA-W-4-2412" in text
    assert "PLOT" in text and "NEXT CASE" in text
