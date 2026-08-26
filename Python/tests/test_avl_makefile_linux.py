from aid.paths import matlab_code


def test_avl_makefile_uses_linux_x11():
    mf = (matlab_code() / "AVL/AVL3.52rel09032025/bin/Makefile.gfortranDP").read_text()
    assert "/opt/X11" not in mf
    assert "-lX11" in mf
