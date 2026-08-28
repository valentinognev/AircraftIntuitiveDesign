# Python/tests/test_tornado_box_erau.py
import numpy as np
import pytest
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import lattice_setup
from aid.tornado.boundary import set_boundary
from aid.tornado.solver import solve
from aid.tornado.coeff import coeff_create
from aid.paths import models_dir

BOX_LIKE = ["Box.jsonc", "ERAU DBF Plane.jsonc"]


@pytest.mark.parametrize("name", BOX_LIKE)
def test_box_like_tornado_finite_coeffs(name):
    ac = load_jsonc(models_dir() / name)
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    tres = coeff_create(raw, lattice, state, ref, geo)
    for key in ("CL", "CD", "Cm"):
        assert np.isfinite(tres[key]), f"{name} {key}={tres[key]!r} is not finite"
