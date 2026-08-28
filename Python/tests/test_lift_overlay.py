import numpy as np
import pytest
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.viz import lift_overlay


def test_cessna_lift_overlay_at_quarter_mac():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ov = lift_overlay(ac, 25, angle=True)
    x_expect = (
        float(ac.WG["X"])
        + float(np.asarray(ac.WG["xmac"]).reshape(-1)[-1])
        + float(np.asarray(ac.WG["cbar"]).reshape(-1)[-1]) / 4
    )
    assert np.allclose(ov["X"], x_expect)
    assert ov["Y"][0] < 0 < ov["Y"][-1]
    assert np.allclose(ov["Z0"], float(ac.WG["Z"]))
    assert np.max(np.abs(ov["Cl_ideal"])) == pytest.approx(float(ac.WG["CHRDR"]))
    assert ov["Cl_ideal"].shape == ov["Y"].shape
