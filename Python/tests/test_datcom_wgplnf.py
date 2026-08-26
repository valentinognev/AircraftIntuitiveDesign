from aid.aircraft import load_jsonc
from aid.datcom_io import write_wgplnf
from aid.paths import models_dir


def test_wgplnf_chrdr_sspn():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_wgplnf(ac.WG, lines)
    text = "\n".join(lines)
    assert "$WGPLNF" in text
    assert "CHRDR=2" in text.replace(" ", "")
    assert "SSPN=6" in text.replace(" ", "")
