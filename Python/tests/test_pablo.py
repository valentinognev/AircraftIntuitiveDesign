import math

import numpy as np

from aid.tornado.pablo import pablo


def _ellipse_section(n_side: int = 10, half_thickness: float = 0.06) -> np.ndarray:
    """20-point ellipse: x = 0.5*(1-cos), y = ±half_thickness*sin, LE to TE."""
    beta = np.linspace(0.0, np.pi, n_side)
    x = 0.5 * (1.0 - np.cos(beta))
    y = half_thickness * np.sin(beta)
    upper = np.column_stack((x, y))
    lower = np.column_stack((x, -y))
    return np.vstack((upper, lower))


def test_symmetric_section_at_zero_alpha_has_small_cl_and_positive_cd():
    z = _ellipse_section()
    out = pablo(z, alpha_rad=0.0, reynolds=1.0e6)
    assert abs(out["cl"]) < 0.05
    assert out["cd"] > 0.0
    assert math.isfinite(out["cm"])
