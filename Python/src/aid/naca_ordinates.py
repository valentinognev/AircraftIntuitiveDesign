"""4- and 5-digit NACA ordinates from NACA_Panel_Maker.m (not 6-series)."""

import numpy as np

# NACA_Panel_Maker.m cases 210, 220, 230, 240, 250: (m/c, k1).
_NACA5 = {
    210: (0.058, 361.4),
    220: (0.126, 51.64),
    230: (0.2025, 15.957),
    240: (0.29, 6.643),
    250: (0.391, 3.23),
}


def naca4_ordinates(code: str, n_pts: int) -> np.ndarray:
    """Cosine spacing, shape (n_pts, 2). Closed loop: lower TE→LE then upper LE→TE, matching NACA_Panel_Maker.m lines 149-158. code length 4."""
    if len(code) != 4:
        raise ValueError(f"4-digit NACA code required, got {code!r}")
    return _digit_ordinates(code, n_pts, five=False)


def naca5_ordinates(code: str, n_pts: int) -> np.ndarray:
    """Same layout. code length 5. Families 210, 220, 230, 240, 250 only."""
    if len(code) != 5:
        raise ValueError(f"5-digit NACA code required, got {code!r}")
    return _digit_ordinates(code, n_pts, five=True)


def _digit_ordinates(code: str, n_pts: int, five: bool) -> np.ndarray:
    n = 1000
    c = 1.0
    if five:
        family = int(code[0:3])
        if family not in _NACA5:
            raise ValueError(
                f"5-digit family {family} is not one of {tuple(_NACA5)}"
            )
        m_c, k = _NACA5[family]
        m = m_c * c
        p = c * int(code[1:3]) / 200.0
        t = c * int(code[3:5]) / 100.0
        x1 = np.linspace(0.0, p, n)
        y1 = (k / 6.0) * (x1**3 - 3 * m * x1**2 + m**2 * (3 - m) * x1)
        dy1 = (k / 6.0) * (3 * x1**2 - 6 * m * x1 + m**2 * (3 - m))
        theta1 = np.arctan(dy1)
        x2 = np.linspace(m + 0.1 / n, c, n)
        y2 = (k / 6.0) * m**3 * (1.0 - x2)
        theta2 = np.arctan(-(k / 6.0) * m**3)
        x = np.concatenate([x1, x2])
        le_slope = (k / 6.0) * m**2 * (3 - m)
    else:
        m = int(code[0]) * c / 100.0
        p = int(code[1]) * c / 10.0
        t = int(code[2:4]) * c / 100.0
        if p == 0.0:
            le_slope = 0.0
            p = 0.25
        else:
            le_slope = 2.0 * m / p
        x1 = np.linspace(0.0, p, n)
        y1 = (m / p**2) * (2 * p * x1 - x1**2)
        theta1 = np.arctan((m / p**2) * (2 * p - 2 * x1))
        x2 = np.linspace(p + 0.1 / n, c, n)
        y2 = (m / (1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x2 - x2**2)
        theta2 = np.arctan((m / (1 - p) ** 2) * (2 * p - 2 * x2))
        x = np.concatenate([x1, x2])

    y_t = (t / 0.2) * (
        0.29690 * np.sqrt(x)
        - 0.126 * x
        - 0.35160 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )
    if le_slope == 0.0:
        x_upper = x
        y_upper = y_t
        x_lower = x
        y_lower = -y_t
    else:
        x_upper = np.concatenate(
            [
                x[:n] - y_t[:n] * np.sin(theta1),
                x[n:] - y_t[n:] * np.sin(theta2),
            ]
        )
        y_upper = np.concatenate(
            [
                y1 + y_t[:n] * np.cos(theta1),
                y2 + y_t[n:] * np.cos(theta2),
            ]
        )
        x_lower = np.concatenate(
            [
                x[:n] + y_t[:n] * np.sin(theta1),
                x[n:] + y_t[n:] * np.sin(theta2),
            ]
        )
        y_lower = np.concatenate(
            [
                y1 - y_t[:n] * np.cos(theta1),
                y2 - y_t[n:] * np.cos(theta2),
            ]
        )

    angle = np.linspace(0.0, np.pi, n_pts // 2 + 1)
    x_new = 0.5 - np.cos(angle) / 2.0
    y_upper_i = _interp_linear_extrap(x_upper, y_upper, x_new)
    y_lower_i = _interp_linear_extrap(x_lower, y_lower, x_new)
    # NACA_Panel_Maker.m lines 156-158: lower TE→LE, then upper LE→TE.
    x_out = np.concatenate([x_new[::-1], x_new[1:]])
    y_out = np.concatenate([y_lower_i[::-1], y_upper_i[1:]])
    return np.column_stack([x_out, y_out])


def _interp_linear_extrap(xp: np.ndarray, fp: np.ndarray, xq: np.ndarray) -> np.ndarray:
    """Linear interp with extrapolation. Sorts xp so a local reversal still interpolates."""
    xp = np.asarray(xp, dtype=np.float64)
    fp = np.asarray(fp, dtype=np.float64)
    order = np.argsort(xp, kind="mergesort")
    xp = xp[order]
    fp = fp[order]
    uniq = np.empty(xp.shape[0], dtype=bool)
    uniq[0] = True
    uniq[1:] = np.diff(xp) > 0.0
    xp = xp[uniq]
    fp = fp[uniq]
    y = np.interp(xq, xp, fp)
    if xp.shape[0] >= 2:
        left = xq < xp[0]
        right = xq > xp[-1]
        if np.any(left):
            slope = (fp[1] - fp[0]) / (xp[1] - xp[0])
            y = np.where(left, fp[0] + slope * (xq - xp[0]), y)
        if np.any(right):
            slope = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2])
            y = np.where(right, fp[-1] + slope * (xq - xp[-1]), y)
    return y
