from aid.paths import datcom_wrapper


def test_datcom_wrapper_is_executable_script():
    p = datcom_wrapper()
    assert p.is_file()
    text = p.read_text()
    assert "for005.dat" in text
    assert "datcom.out" in text
    assert p.stat().st_mode & 0o111
