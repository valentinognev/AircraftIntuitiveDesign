from pathlib import Path


def test_opencascade_headers():
    candidates = [
        Path("/usr/include/opencascade/Standard_Version.hxx"),
        Path("/usr/include/opencascade/Standard.hxx"),
    ]
    assert any(p.is_file() for p in candidates), "install libocct-*-dev"


def test_openblas_so():
    import glob

    hits = glob.glob("/usr/lib/*/libopenblas.so*") + glob.glob(
        "/usr/lib/libopenblas.so*"
    )
    assert hits, "install libopenblas-dev"
