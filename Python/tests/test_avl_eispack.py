from aid.paths import matlab_code


def test_avl_eispack_built():
    d = matlab_code() / "AVL/AVL3.52rel09032025/eispack"
    libs = list(d.glob("*.a"))
    assert libs, "no eispack archive"
