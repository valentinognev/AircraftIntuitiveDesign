# Python/tests/test_datcom_parse_gold.py
import json

import pytest

from aid.datcom_parse import datcom_method_warnings, datcom_user_warning, parse_for006
from aid.paths import results_dir


def test_parse_matlab_gold_for006():
    p = results_dir() / "matlab" / "Cessna 172" / "datcom.out"
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "datcom.json").read_text())
    got = parse_for006(p.read_text())
    import numpy as np
    assert np.allclose(got["alpha"], gold["alpha"], atol=1e-6)
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6)
    assert np.allclose(got["cm"], gold["cm"], atol=1e-6)
    assert got.get("high_lift"), "MATLAB gold for006 should include HIGH LIFT when SYMFLP is written"
    assert "epslon" in got
    assert got.get("sections")


def test_parse_f16_ndm_table_is_honest_fail():
    p = results_dir() / "matlab" / "F-16" / "datcom.out"
    with pytest.raises(ValueError, match="no finite coefficients"):
        parse_for006(p.read_text())


def test_f16_method_warnings_include_crest_critical():
    text = (results_dir() / "matlab" / "F-16" / "datcom.out").read_text()
    notes = datcom_method_warnings(text)
    assert notes
    blob = " ".join(notes).lower()
    assert "crest critical" in blob
    assert "0.73" in blob


def test_similar_fatal_banner_is_a_method_warning():
    notes = datcom_method_warnings("*** INPUT ERROR ***\n")
    assert any("INPUT ERROR" in n.upper() for n in notes)


def test_cessna_has_no_method_warnings():
    text = (results_dir() / "matlab" / "Cessna 172" / "datcom.out").read_text()
    assert datcom_method_warnings(text) == []


_TRANSONIC_FAIRING = """
0 ALPHA     CD       CL       CM       CN       CA       XCP
   -4.0    0.028    NDM       NDM     NDM      NDM        NaN
                                                   *** WING-BODY DATA FAIRING ***
            CLB/CL =        NaN     (CLB/CL)MFB =-0.3972E-02     (CNA)M=1.4 =        NaN
"""


def test_transonic_wing_body_nan_warns_stmach():
    notes = datcom_method_warnings(_TRANSONIC_FAIRING)
    blob = " ".join(notes).lower()
    assert "transonic" in blob
    assert "0.6" in blob
    msg = datcom_user_warning(_TRANSONIC_FAIRING, error=ValueError("no finite coefficients"))
    assert msg is not None
    assert "transonic" in msg.lower()
    assert "no finite coefficients" not in msg.lower()
