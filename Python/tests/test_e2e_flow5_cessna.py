import numpy as np
from aid.aircraft import load_jsonc
from aid.flow5_io import run_flow5, run_flow5_native, write_flow5_deck
from aid.paths import models_dir


def test_e2e_cessna_aid_matches_native_flow5():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    mesh = ("10", "10")
    native = run_flow5_native(write_flow5_deck(ac, mesh))
    aid = run_flow5(ac, mesh)
    for key in ("alpha", "CL", "CD", "Cm"):
        assert np.allclose(native[key], aid[key], rtol=0.0, atol=1e-6), key
    swept = [float(a) for a in ac.AERO["ALSCHD"]]
    assert [float(a) for a in aid["alpha"]] == swept
    assert len(aid["CL"]) == len(swept)
