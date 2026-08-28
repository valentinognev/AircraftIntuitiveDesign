# Python/tests/test_tornado_spanwise.py
import math

import numpy as np

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.stability import aircraft_stability
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.spanwise import tornado_spanwise
from aid.tornado.solver import solve
from aid.tornado_io import tornado_io


def test_cessna_tornado_spanwise_covers_span():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    st = aircraft_stability(ac)
    geo, state = tornado_io(ac, ("10", "5"))
    state = dict(state)
    state["alpha"] = float(st["alpha"]) * math.pi / 180.0
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    coeffs = coeff_create(raw, lattice, state, ref, geo)
    sw = tornado_spanwise(coeffs, lattice, geo, state, ac)
    assert len(sw) >= 1
    y = np.asarray(sw[0]["y"], dtype=float)
    cl = np.asarray(sw[0]["Cl"], dtype=float)
    assert y.size == cl.size
    assert y.min() < 0 < y.max()
    assert np.isfinite(cl).all()
    assert cl.max() > 0


def test_cessna_tornado_spanwise_names_surfaces():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    assert list(geo["name"]) == ["Wing", "HT", "VT", "Wing 2"]
    st = aircraft_stability(ac)
    state = dict(state)
    state["alpha"] = float(st["alpha"]) * math.pi / 180.0
    lattice, ref = lattice_setup(geo, state, 0)
    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    coeffs = coeff_create(raw, lattice, state, ref, geo)
    sw = tornado_spanwise(coeffs, lattice, geo, state, ac)
    assert [item["name"] for item in sw] == ["Wing", "HT", "VT", "Wing 2"]
