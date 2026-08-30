from aid.paths import repo_root


def test_xfoil_cmake_declares_shared_lib():
    text = (repo_root() / "FLOW5" / "XFoil-lib" / "CMakeLists.txt").read_text()
    assert "add_library(XFoil SHARED" in text
    assert "xfoil.cpp" in text
    assert "XFOIL_LIBRARY" in text
