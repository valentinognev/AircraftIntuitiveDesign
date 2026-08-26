from aid.paths import matlab_code


def test_aid_batch_np_default_no():
    t = (matlab_code() / "AID.m").read_text()
    assert "strcmp(choice,'batch')" in t
    assert "Estimate Neutral Point" in t
