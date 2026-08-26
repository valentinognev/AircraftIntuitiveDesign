from aid.field_docs import DOCS


def test_cessna_wing_keys_documented():
    assert "WG.CHRDR" in DOCS
    assert "Root Chord" in DOCS["WG.CHRDR"]
    assert "WG.SSPN" in DOCS
    assert "AERO.ALSCHD" in DOCS
    assert "AERO.XCG" in DOCS
