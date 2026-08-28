from copy import deepcopy

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


def test_zero_deflection_has_no_control_meshes():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    names = {s.name for s in aircraft_surfaces(ac)}
    assert "F" not in names
    assert "A" not in names
    assert "E" not in names
    assert "R" not in names


def test_flap_deflection_adds_f_mesh_and_drops_te():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    undeflected = aircraft_surfaces(ac)
    ac.F = deepcopy(ac.F)
    ac.F["DELTA"] = 20
    deflected = aircraft_surfaces(ac)
    names = [s.name for s in deflected]
    assert names.count("F") >= 2
    flap = next(s for s in deflected if s.name == "F")
    wg0 = next(s for s in undeflected if s.name == "WG")
    # Positive flap: trailing edge down (Plot_Planform.m Zf = Zf - dZ)
    assert flap.z.mean() < wg0.z.mean()


def test_elevator_deflection_adds_e_mesh():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ac.E = deepcopy(ac.E)
    ac.E["DELTA"] = 15
    names = [s.name for s in aircraft_surfaces(ac)]
    assert "E" in names


def test_da20_loaded_deflections_show_controls():
    ac = load_jsonc(models_dir() / "DA20-C1.jsonc")
    names = {s.name for s in aircraft_surfaces(ac)}
    assert "F" in names
    assert "A" in names
    assert "E" in names
    assert "R" in names
