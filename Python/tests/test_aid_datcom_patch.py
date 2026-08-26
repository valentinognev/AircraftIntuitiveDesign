from aid.paths import matlab_code


def test_aid_uses_linux_datcom_wrapper():
    text = (matlab_code() / "AID.m").read_text()
    assert "system('./datcom')" in text or 'system("./datcom")' in text
    assert "./datcom.osx" not in text.split("else")[-1]  # crude: linux branch
