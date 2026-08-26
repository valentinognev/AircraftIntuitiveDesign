# Python/tests/test_geometry_break_span.py
from aid.geometry import geometry


def test_break_span_weighted_cbar():
    pt = {
        "CHRDR": 4.0, "CHRDBP": 3.0, "CHRDTP": 2.0,
        "SSPN": 10.0, "SSPNOP": 4.0,
        "SAVSI": 0.0, "SAVSO": 0.0, "CHSTAT": 0.25,
        "DHDADI": 0.0, "DHDADO": 0.0,
        "X": 0.0, "Y": 0.0, "Z": 0.0,
    }
    out = geometry(pt, angl=False)
    assert out["S"][-1] == out["S"][0] + out["S"][1]
    assert out["cbar"][-1] > 0
