# Python/tests/test_tornado_solver_gamma.py
import numpy as np
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.tornado.boundary import set_boundary
from aid.tornado.solver import solve
from aid.paths import models_dir

def test_solver_returns_gamma():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    res = solve(state, geo, lattice)
    g = np.asarray(res["gamma"]).reshape(-1)
    assert g.size > 0
    assert np.isfinite(g).all()
