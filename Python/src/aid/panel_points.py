"""Airfoil coordinate file read from Panel_Points.m (no GUI)."""

from pathlib import Path

import numpy as np


def read_airfoil_file(path: Path) -> np.ndarray:
    """Port Panel_Points.m file read: two columns x,y. No GUI."""
    xy = np.loadtxt(path, dtype=np.float64)
    xy = np.reshape(np.asarray(xy, dtype=np.float64), (-1, 2))
    return xy
