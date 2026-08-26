# Python/tests/test_tornado_lattice.py
import math

import numpy as np
from aid.aircraft import load_jsonc
from aid.tornado_io import tornado_io
from aid.tornado.lattice import _slope2, lattice_setup
from aid.paths import models_dir

def test_lattice_nonzero_panels():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, state = tornado_io(ac, ("10", "5"))
    lattice, ref = lattice_setup(geo, state, 0)
    assert lattice["npan"] > 0
    assert "X" in lattice and "Y" in lattice


def test_slope2_odd_pad_cessna_zu():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo, _ = tornado_io(ac, ("10", "5"))
    foil = np.asarray(geo["foil"][0][0][0], dtype=float)
    assert foil.shape[0] == 101
    nx = int(math.ceil(foil.shape[0] / 2))
    data = np.insert(foil, nx, foil[nx - 1], axis=0)
    zu_matlab = data[-nx:, 1]
    x = np.flip(data[:nx, 0])
    zl = np.flip(data[:nx, 1])
    c = 0.5 * (zl + zu_matlab)
    expected_angle = np.array(
        [math.atan((c[i + 1] - c[i]) / (x[i + 1] - x[i])) for i in range(nx - 1)]
    )
    xa, angle = _slope2(foil)
    assert xa.shape == expected_angle.shape
    np.testing.assert_allclose(angle, expected_angle)
