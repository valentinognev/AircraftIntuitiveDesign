from copy import deepcopy

from aid.aircraft import load_jsonc
from aid.mesh_params import mesh_fields
from aid.paths import models_dir


def test_cessna_tornado_two_fields():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    prompts, defaults = mesh_fields(ac, "tornado")
    assert prompts == ["Spanwise Nodes", "Chordwise Nodes"]
    assert defaults == ["10", "5"]


def test_cessna_avl_chord_ten():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    prompts, defaults = mesh_fields(ac, "avl")
    assert prompts == ["Spanwise Nodes", "Chordwise Nodes"]
    assert defaults == ["10", "10"]


def test_twist_adds_third_field():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ac.WG = deepcopy(ac.WG)
    ac.WG["TWISTA"] = 5.0
    prompts, defaults = mesh_fields(ac, "tornado")
    assert prompts[-1] == "Twist Linearity"
    assert defaults == ["10", "5", "2"]
    _, avl_def = mesh_fields(ac, "avl")
    assert avl_def[-1] == "1"


def test_two_airfoils_adds_interpolation_field():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ac.WG = deepcopy(ac.WG)
    foil = ac.WG["DATA"]
    ac.WG["DATA"] = [foil, foil]
    ac.WG["TWISTA"] = 0
    prompts, defaults = mesh_fields(ac, "tornado")
    assert prompts[-1] == "Airfoil Interpolation Linearity"
    assert defaults[-1] == "3"
    _, avl_def = mesh_fields(ac, "avl")
    assert avl_def[-1] == "1"
