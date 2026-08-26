# Python/tests/test_tornado_io_cessna.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.paths import models_dir

def test_tornado_io_cessna_mesh_10_5():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    assert geo["nwing"] >= 1
    assert float(geo["c"][0, 0]) == 2.0
    assert state["betha"] == 0.0
    assert state["AS"] > 0
    assert float(geo["nx"][1, 0]) == 3.0
    assert float(geo["ny"][1, 0]) == 5.0
    assert float(geo["nx"][2, 0]) == 3.0
    assert float(geo["nx"][2, 1]) == 3.0
