from aid.aircraft import load_jsonc
from aid.flow5_sections import planform_sections
from aid.flow5_units import FT_M
from aid.paths import models_dir


def test_cessna_wing_two_sections():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w = planform_sections(ac.WG, nx=10, ny=10, vertical=False)
    assert w["rx_deg"] == 0.0
    assert len(w["sections"]) == 2
    root, tip = w["sections"]
    assert abs(root["chord_m"] - 2 * FT_M) < 1e-9
    assert abs(tip["chord_m"] - 2 * FT_M) < 1e-9
    assert abs(tip["y_m"] - 6 * FT_M) < 1e-6
    assert abs(root["dihedral_deg"] - 3.0) < 1e-9
    assert root["foil"].startswith("NACA")
    assert w["nx"] == 10


def test_cessna_vt_three_sections_vertical():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    v = planform_sections(ac.VT, nx=10, ny=10, vertical=True)
    assert v["rx_deg"] == -90.0
    assert v["closed_inner"] is True
    assert len(v["sections"]) == 3
    root, brk, tip = v["sections"]
    assert abs(root["y_m"]) < 1e-9
    assert abs(brk["y_m"] - 0.7 * FT_M) < 1e-6
    assert abs(tip["y_m"] - 2 * FT_M) < 1e-6
