from aid.aircraft import load_jsonc
from aid.body_stability import body_stability
from aid.paths import models_dir


def test_cessna_multhopp_finite():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    out = body_stability(ac, "Multhopp")
    assert out["Cma"] == out["Cma"]  # not NaN
    assert abs(out["Cma"]) > 0


def test_gilruth_positive_cma():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    out = body_stability(ac, "Gilruth_White")
    assert out["Cma"] > 0
