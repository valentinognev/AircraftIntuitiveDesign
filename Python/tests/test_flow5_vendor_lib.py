from aid.paths import repo_root


def test_flow5_lib_headers_present():
    api = repo_root() / "FLOW5" / "flow5-lib" / "api"
    for name in ("planexfl.h", "planetask.h", "planepolar.h", "objects2d.h", "wingsection.h"):
        assert (api / name).is_file(), name
    assert (repo_root() / "FLOW5" / "flow5-lib" / "CMakeLists.txt").is_file()
