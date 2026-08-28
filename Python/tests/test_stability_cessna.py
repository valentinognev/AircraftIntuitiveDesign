from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.stability import aircraft_stability, stability_lines


def test_cessna_cg_and_static_margin():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    st = aircraft_stability(ac)
    assert round(st["x_cg"] * 100) == 37
    assert st["Cm_CL"] < 0
    assert round(-st["Cm_CL"] * 100) == 13
    assert "CG at 37% MAC" in st["summary"][0]
    assert "13% stable" in st["summary"][1]


def test_cessna_stability_lines_have_slopes():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    st = aircraft_stability(ac)
    lines = stability_lines(st)
    assert lines["alpha"].size > 10
    assert lines["CL"].size == lines["alpha"].size
    assert lines["Cm"].size == lines["alpha"].size
