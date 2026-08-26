# Python/tests/test_tornado_lattice.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.paths import models_dir

def test_lattice_nonzero_panels():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    assert lattice["npan"] > 0
    assert "X" in lattice and "Y" in lattice
