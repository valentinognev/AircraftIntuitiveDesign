from aid.paths import repo_root


def test_xfoil_sources_and_gpl_license():
    root = repo_root() / "FLOW5"
    lic = (root / "LICENSE").read_text()
    assert "GNU GENERAL PUBLIC LICENSE" in lic
    assert "Version 3" in lic
    xf = root / "XFoil-lib"
    for name in ("xfoil.cpp", "xfoil.h", "xfoil_params.h", "xfoil-lib_global.h"):
        assert (xf / name).is_file(), name
