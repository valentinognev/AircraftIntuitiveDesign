import numpy as np
import pytest

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


def test_f16_multhopp_falls_back_when_body_skips_wing_chord():
    ac = load_jsonc(models_dir() / "F-16.jsonc")
    with np.errstate(divide="raise"):
        mul = body_stability(ac, "Multhopp")
    gil = body_stability(ac, "Gilruth_White")
    assert mul["Cma"] == pytest.approx(gil["Cma"])
    assert mul["Cm0"] == pytest.approx(gil["Cm0"])
