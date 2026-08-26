from aid.aircraft import load_jsonc
from aid.datcom_io import write_body, naca_wing_line
from aid.paths import models_dir


def test_body_and_naca_cessna():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_body(ac, lines)
    naca = naca_wing_line(ac)
    assert "$BODY" in "\n".join(lines)
    assert "NACA-W-4-2412" in naca
