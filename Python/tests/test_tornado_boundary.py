# Python/tests/test_tornado_boundary.py
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.tornado.boundary import set_boundary
from aid.paths import models_dir

def test_boundary_rhs_shape():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lat2 = set_boundary(lattice, geo, state)
    assert "rhs" in lat2 or "RHS" in lat2
