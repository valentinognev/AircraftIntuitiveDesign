# Python/tests/test_tornado_cessna_coeff.py
import json
import numpy as np
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.tornado.boundary import set_boundary
from aid.tornado.solver import solve
from aid.tornado.coeff import coeff_create
from aid.paths import models_dir, results_dir

def test_tornado_cl_matches_matlab_gold():
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "tornado.json").read_text())
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    tres = coeff_create(raw, lattice, state, ref, geo)
    rtol, atol = 1e-4, 1e-5
    assert np.allclose(tres["CL"], gold["CL"], rtol=rtol, atol=atol)
