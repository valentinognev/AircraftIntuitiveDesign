import pytest

from aid.naca_ordinates import naca4_ordinates, naca5_ordinates


def test_naca2412_thickness_and_closure():
    xy = naca4_ordinates("2412", 51)
    assert xy.shape == (51, 2)
    assert abs(xy[0, 0] - 1.0) < 1e-6
    assert abs(xy[-1, 0] - 1.0) < 1e-6
    # Camber rotates a 12% section; thickness stays within 0.02 of 0.12.
    assert float(xy[:, 1].max() - xy[:, 1].min()) == pytest.approx(0.12, abs=0.02)


def test_naca23012_has_positive_camber():
    xy = naca5_ordinates("23012", 41)
    assert xy.shape == (41, 2)
    assert float(xy[:, 1].max()) > 0.02
