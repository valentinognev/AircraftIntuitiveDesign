# Python/tests/test_avl_write_geometry.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.avl_io import write_avl_geometry
from aid.paths import models_dir


def test_writes_geometry_avl(tmp_path):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "10"))
    write_avl_geometry(ac, geo, state, tmp_path, 10, 10)
    avl = tmp_path / "geometry.avl"
    assert avl.is_file()
    text = avl.read_text()
    assert "SURFACE" in text or "SECTION" in text
