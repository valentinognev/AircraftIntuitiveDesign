from aid.paths import matlab_code


def test_avl_io_calls_avl352():
    t = (matlab_code() / "AVL_IO.m").read_text()
    assert "./avl'" in t or "'./avl'" in t
    assert "avl3.35" not in t
