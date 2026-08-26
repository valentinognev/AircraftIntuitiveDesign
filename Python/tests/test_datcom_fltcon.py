from aid.aircraft import load_jsonc
from aid.datcom_io import write_fltcon
from aid.paths import models_dir


def test_fltcon_cessna_mach_alpha():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_fltcon(ac, lines)
    text = "\n".join(lines)
    assert "$FLTCON" in text
    assert "MACH=0.030" in text or "MACH=0.03" in text
    assert "-4.0" in text and "12.0" in text
