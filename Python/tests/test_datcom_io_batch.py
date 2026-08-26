from aid.paths import matlab_code


def test_datcom_io_batch_skips_questdlg():
    t = (matlab_code() / "DATCOM_IO.m").read_text()
    assert "strcmp(choice,'batch')" in t or "strcmp(choice, 'batch')" in t
