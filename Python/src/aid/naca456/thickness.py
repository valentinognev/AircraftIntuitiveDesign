"""Thickness distributions and x-stations from naca456 nacax.f90."""

import numpy as np

from aid.naca456.camber import parametrize_airfoil, polynomial
from aid.naca456.epspsi import EPS, PSI
from aid.naca456.spline import fmm_spline, pc_lookup, spline_zero

_COARSE = np.array(
    [
        0.0, 0.005, 0.0075, 0.0125, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25,
        0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9,
        0.95, 1.0,
    ],
    dtype=np.float64,
)
_MEDIUM = np.array(
    [
        0.0, 0.0002, 0.0005, 0.001, 0.0015, 0.002, 0.005, 0.01, 0.015, 0.02,
        0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22,
        0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.42, 0.44, 0.46,
        0.48, 0.50, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70,
        0.72, 0.74, 0.76, 0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94,
        0.96, 0.97, 0.98, 0.99, 0.995, 1.0,
    ],
    dtype=np.float64,
)
_FINE = np.array(
    [
        0.0, 0.00005, 0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0008,
        0.0010, 0.0012, 0.0014, 0.0016, 0.0018, 0.002, 0.0025, 0.003, 0.0035,
        0.004, 0.0045, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01, 0.011, 0.012,
        0.013, 0.014, 0.015, 0.016, 0.018, 0.02, 0.025, 0.03, 0.035, 0.04,
        0.045, 0.05, 0.055, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12, 0.14, 0.16,
        0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40,
        0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64,
        0.66, 0.68, 0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.82, 0.84, 0.86, 0.88,
        0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.975, 0.98, 0.985, 0.99, 0.995,
        0.999, 1.0,
    ],
    dtype=np.float64,
)

# Column-major RESHAPE in ScaleFactor, one column per family.
_SCALE_COEFF = np.array(
    [
        [0.0, 8.1827699, 1.3776209, -0.092851684, 7.5942563],
        [0.0, 4.6535511, 1.038063, -1.5041794, 4.7882784],
        [0.0, 6.5718716, 0.49376292, 0.7319794, 1.9491474],
        [0.0, 6.7581414, 0.19253769, 0.81282621, 0.85202897],
        [0.0, 6.627289, 0.098965859, 0.96759774, 0.90537584],
        [0.0, 8.1845925, 1.0492569, 1.31150930, 4.4515579],
        [0.0, 8.2125018, 0.76855961, 1.4922345, 3.6130133],
        [0.0, 8.2514822, 0.46569361, 1.50113018, 2.0908904],
    ],
    dtype=np.float64,
).T

_D1_COEFF = np.array(
    [3.48e-5, 2.3076628, -10.127712, 19.961478, -10.420597],
    dtype=np.float64,
)


def load_x(den_code):
    if den_code == 2:
        return _MEDIUM.copy()
    if den_code == 3:
        return _FINE.copy()
    return _COARSE.copy()


def _thickness_closed(toc, x, a4):
    a0 = 0.2969
    a1 = -0.1260
    a2 = -0.3516
    a3 = 0.2843
    a22 = a2 + a2
    a33 = a3 + a3 + a3
    a42 = a4 + a4
    a44 = a42 + a42
    x = np.asarray(x, dtype=np.float64)
    y = np.empty_like(x)
    yp = np.empty_like(x)
    for k, xx in enumerate(x):
        if xx == 0.0:
            y[k] = 0.0
            yp[k] = 1e22
        else:
            srx = float(np.sqrt(xx))
            y[k] = a0 * srx + xx * (a1 + xx * (a2 + xx * (a3 + xx * a4)))
            yp[k] = 0.5 * a0 / srx + a1 + xx * (a22 + xx * (a33 + xx * a44))
    scale = 5.0 * toc
    return y * scale, yp * scale


def thickness4(toc, x):
    return _thickness_closed(toc, x, -0.1015)


def thickness4_sharp_te(toc, x):
    return _thickness_closed(toc, x, -0.1036)


def _cal_a1(a0, a2, a3, xmt):
    return -(0.5 * a0 / np.sqrt(xmt)) - 2.0 * a2 * xmt - 3.0 * a3 * xmt * xmt


def _cal_a2(a0, a3, xmt):
    return -0.1 / (xmt * xmt) + 0.5 * a0 / np.sqrt(xmt * xmt * xmt) - 2.0 * a3 * xmt


def _cal_a3(a0, d1, xmt):
    omxmt = 1.0 - xmt
    return (
        0.1 / (xmt * xmt * xmt)
        + (d1 * omxmt - 0.294) / (xmt * omxmt * omxmt)
        - (3.0 / 8.0) * a0 / (xmt**2.5)
    )


def thickness4m(toc, le_index, xmaxt, x):
    x = np.asarray(x, dtype=np.float64)
    d1 = polynomial(_D1_COEFF, xmaxt)
    rle = (1.1019 / 36.0) * (toc * le_index) ** 2
    a0 = (0.2 / toc) * np.sqrt(rle + rle)
    a3 = _cal_a3(a0, d1, xmaxt)
    a2 = _cal_a2(a0, a3, xmaxt)
    a1 = _cal_a1(a0, a2, a3, xmaxt)
    a22 = a2 + a2
    a33 = a3 + a3 + a3
    omxmt = 1.0 - xmaxt
    omxmsq = omxmt * omxmt
    d3 = ((3.0 * d1) - (0.588 / omxmt)) / (3.0 * omxmsq)
    d2 = (-1.5 * omxmt * d3) - ((0.5 * d1) / omxmt)
    d0 = 0.002
    d22 = d2 + d2
    d33 = d3 + d3 + d3
    y = np.empty_like(x)
    yp = np.empty_like(x)
    for k, xx in enumerate(x):
        if xx == 0.0:
            y[k] = 0.0
            yp[k] = 1e20
            continue
        if xx < xmaxt:
            srx = float(np.sqrt(xx))
            y[k] = a0 * srx + xx * (a1 + xx * (a2 + xx * a3))
            yp[k] = 0.5 * a0 / srx + a1 + xx * (a22 + xx * a33)
        else:
            xx = 1.0 - xx
            y[k] = d0 + xx * (d1 + xx * (d2 + xx * d3))
            yp[k] = d1 + xx * (d22 + xx * d33)
    scale = 5.0 * toc
    return y * scale, yp * scale


def scale_factor(family, tc):
    if family < 1 or family > 8 or tc <= 0.0:
        return 0.0
    return polynomial(_SCALE_COEFF[:, family - 1], tc)


def set_six_digit_points(family, tc):
    eps = np.array(EPS[family - 1], dtype=np.float64, copy=True)
    psi = np.array(PSI[family - 1], dtype=np.float64, copy=True)
    sf = scale_factor(family, tc)
    eps *= sf
    psi *= sf
    phi = np.arange(201, dtype=np.float64) * (3.14159265 / 200.0)
    a = 1.0
    z = a * np.exp(psi[0] + 1j * phi)
    zprime = z * np.exp((psi - psi[0]) - 1j * eps)
    zeta = zprime + (a * a) / zprime
    zfinal = (zeta[0] - zeta) / np.abs(zeta[-1] - zeta[0])
    return np.real(zfinal), -np.imag(zfinal)


def thickness6(family, toc, x):
    xt, yt = set_six_digit_points(family, toc)
    s, xs, ys = parametrize_airfoil(xt, yt, xt, -yt)
    xp = fmm_spline(s, xs)
    yp_s = fmm_spline(s, ys)
    s_lower = s[200:]
    x_lower = xs[200:]
    y_lower = -ys[200:]
    xp_lower = xp[200:]
    yp_lower = -yp_s[200:]
    x = np.asarray(x, dtype=np.float64)
    y = np.empty(x.size, dtype=np.float64)
    dxds = np.empty(x.size, dtype=np.float64)
    dyds = np.empty(x.size, dtype=np.float64)
    tol = 1e-6
    for k, xk in enumerate(x):
        sx, _err = spline_zero(s_lower, x_lower, xp_lower, float(xk), tol)
        _f, dxds[k], _fpp, _fppp = pc_lookup(s_lower, x_lower, xp_lower, sx)
        y[k], dyds[k], _fpp, _fppp = pc_lookup(s_lower, y_lower, yp_lower, sx)
    yp = np.zeros(x.size, dtype=np.float64)
    nonzero = dxds != 0.0
    yp[nonzero] = dyds[nonzero] / dxds[nonzero]
    return y, yp
