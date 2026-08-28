from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.viz import aircraft_surfaces


def test_cessna_surfaces_include_airframe():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    surfs = aircraft_surfaces(ac)
    names = [s.name for s in surfs]
    assert "WG" in names
    assert "HT" in names
    assert "VT" in names
    assert "BD" in names
    assert "NP{1}" in names
    assert "prop" in names

    wg = next(s for s in surfs if s.name == "WG")
    assert wg.x.shape[0] >= 2 and wg.x.shape[1] >= 2
    assert wg.z.mean() > 0.5
    assert wg.y.max() > 4

    bd = next(s for s in surfs if s.name == "BD")
    assert bd.x.max() >= 9
    assert bd.y.max() > 0.5
