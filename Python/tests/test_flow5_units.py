from aid.aircraft import load_jsonc
from aid.flow5_units import FT_M, ft_to_m, ft2_to_m2, lb_to_kg, polar_state
from aid.paths import models_dir


def test_ft_factor_matches_tornado():
    assert abs(FT_M - 1.0 / 3.28084) < 1e-15
    assert abs(ft_to_m(3.28084) - 1.0) < 1e-9
    assert abs(ft2_to_m2(1.0) - FT_M ** 2) < 1e-15
    assert abs(lb_to_kg(1.0) - 0.45359237) < 1e-12


def test_cessna_polar_state_positive_qinf():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    st = polar_state(ac)
    assert st["qinf_mps"] > 0
    assert st["density"] > 1.0
    assert st["viscosity"] > 0
