from aid.paths import repo_root


def test_root_cmake_adds_subdirs():
    text = (repo_root() / "FLOW5" / "CMakeLists.txt").read_text()
    assert "add_subdirectory(XFoil-lib)" in text
    assert "add_subdirectory(flow5-lib)" in text


def test_flow5_lib_cmake_uses_vendored_xfoil_and_openblas():
    text = (repo_root() / "FLOW5" / "flow5-lib" / "CMakeLists.txt").read_text()
    assert "/usr/local/include/XFoil/" not in text
    assert "USE_INTEL_MKL" in text
    assert "OFF" in text  # default off appears in option()
    assert "openblas" in text
