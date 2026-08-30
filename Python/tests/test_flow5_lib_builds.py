from pathlib import Path

from aid.paths import repo_root


def test_libflow5_shared_object_exists():
    build = repo_root() / "FLOW5" / "build"
    so = list(build.rglob("libflow5-lib.so*"))
    assert so, "cmake --build FLOW5/build failed or not run"
