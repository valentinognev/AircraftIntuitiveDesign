import json
import numpy as np
import pytest
from aid.aircraft import load_jsonc
from aid.datcom_io import with_aid_exposed_spans
from aid.datcom_run import run_datcom
from aid.paths import models_dir, results_dir

def test_run_datcom_matches_matlab_gold(tmp_path):
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "datcom.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    # DATCOM's output depends on the alpha grid it was asked for -- cla and cma
    # are finite differences along it -- so the gold is reproducible only on the
    # sweep it was flown on, not on the model's current default.
    ac.AERO["ALSCHD"] = list(gold["alpha"])
    got = run_datcom(ac, tmp_path / "work")
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)


def test_cessna_aid_exposed_span_matches_gui_sspne():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    assert ac.WG["SSPNE"] == pytest.approx(5.51, abs=0.02)
    gui = with_aid_exposed_spans(ac)
    assert gui.WG["SSPNE"] == pytest.approx(5.223, abs=0.02)
    assert gui.HT["SSPNE"] == pytest.approx(2.338, abs=0.02)
    assert gui.VT["SSPNE"] == pytest.approx(1.575, abs=0.02)
    assert ac.WG["SSPNE"] == pytest.approx(5.51, abs=0.02)


def test_cessna_gui_datcom_cm_matches_aid_sspne(tmp_path):
    ac = with_aid_exposed_spans(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    got = run_datcom(ac, tmp_path / "gui")
    assert got["alpha"][-1] == pytest.approx(12.0)
    assert got["cm"][-1] == pytest.approx(-0.1286, abs=0.01)
