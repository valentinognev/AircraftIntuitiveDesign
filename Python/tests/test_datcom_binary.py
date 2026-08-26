from aid.paths import matlab_code


def test_datcom_bin_executable():
    p = matlab_code() / "DATCOM" / "datcom.bin"
    assert p.is_file() and p.stat().st_mode & 0o111
