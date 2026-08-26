from aid.paths import matlab_code


def test_avl_makefile_uses_linux_x11():
    mf = (matlab_code() / "AVL/AVL3.52rel09032025/bin/Makefile.gfortranDP").read_text()
    assert "/opt/X11" not in mf
    assert "-lX11" in mf


def test_avl_plotlib_gfortranDP_config_uses_linux_x11():
    cfg = (
        matlab_code() / "AVL/AVL3.52rel09032025/plotlib/config.make.gfortranDP"
    ).read_text()
    assert "/opt/X11" not in cfg
    assert "/usr/X11R6" not in cfg
    assert "-L/usr/lib/x86_64-linux-gnu -lX11" in cfg
    assert "-I/usr/include" in cfg
