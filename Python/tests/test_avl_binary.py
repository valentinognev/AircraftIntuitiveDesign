from aid.paths import avl_bin


def test_avl_installed():
    p = avl_bin()
    assert p.is_file() and p.stat().st_mode & 0o111
