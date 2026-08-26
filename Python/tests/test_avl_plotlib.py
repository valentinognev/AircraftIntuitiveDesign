from aid.paths import matlab_code


def test_avl_plotlib_built():
    d = matlab_code() / "AVL/AVL3.52rel09032025/plotlib"
    assert (d / "libPlt_gDP.a").is_file() or (d / "libPlt.a").is_file()
