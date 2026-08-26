from aid.aircraft import load_jsonc
from aid.datcom_io import write_synths, write_optins
from aid.paths import models_dir


def test_synths_xcg_and_wing_position():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_optins(ac, lines)
    write_synths(ac, lines)
    text = "\n".join(lines)
    assert "$OPTINS" in text and "SREF=24" in text
    assert "$SYNTHS" in text and "XCG=2.94" in text
