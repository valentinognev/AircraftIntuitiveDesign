"""Camber lines and thickness/camber combination from naca456 nacax.f90."""

import math

import numpy as np

from aid.naca456.spline import fmm_spline, pc_lookup, spline_zero, table_lookup

_PI = 3.141592654
_TWOPI = 2.0 * _PI
_EPS = 1e-7


def polynomial(c, x):
    ff = float(c[-1])
    for coef in c[-2::-1]:
        ff = ff * x + float(coef)
    return ff


def get_rk1(x):
    m = np.array([0.05, 0.1, 0.15, 0.2, 0.25], dtype=np.float64)
    rtab = np.array([0.0580, 0.126, 0.2025, 0.29, 0.391], dtype=np.float64)
    ktab = np.array([361.4, 51.64, 15.957, 6.643, 3.23], dtype=np.float64)
    return table_lookup(m, rtab, 1, x), table_lookup(m, ktab, 1, x)


def get_rk1k2(x):
    m = np.array([0.1, 0.15, 0.2, 0.25], dtype=np.float64)
    rtab = np.array([0.13, 0.217, 0.318, 0.441], dtype=np.float64)
    ktab = np.array([51.99, 15.793, 6.52, 3.191], dtype=np.float64)
    r = table_lookup(m, rtab, 1, x)
    k1 = table_lookup(m, ktab, 1, x)
    k2 = (3.0 * (r - x) ** 2 - r**3) / (1.0 - r) ** 3
    return r, k1, k2


def mean_line2(cmax, xmaxc, x):
    x = np.asarray(x, dtype=np.float64)
    slope1 = 2.0 * cmax / xmaxc
    slope2 = -2.0 * cmax / (1.0 - xmaxc)
    ym = np.empty_like(x)
    ymp = np.empty_like(x)
    for k, xx in enumerate(x):
        if xx < xmaxc:
            theta = xx / xmaxc
            slope = slope1
        else:
            theta = (1.0 - xx) / (1.0 - xmaxc)
            slope = slope2
        ym[k] = theta * (2.0 - theta)
        ymp[k] = slope * (1.0 - theta)
    ym *= cmax
    return ym, ymp


def mean_line3(cl, xmaxc, x):
    x = np.asarray(x, dtype=np.float64)
    r, k1 = get_rk1(xmaxc)
    ym = np.empty_like(x)
    ymp = np.empty_like(x)
    for k, xx in enumerate(x):
        if xx < r:
            ym[k] = xx * (xx * (xx - 3.0 * r) + r * r * (3.0 - r))
            ymp[k] = 3.0 * xx * (xx - r - r) + r * r * (3.0 - r)
        else:
            ym[k] = r * r * r * (1.0 - xx)
            ymp[k] = -(r * r * r)
    scale = k1 * cl / 1.8
    return ym * scale, ymp * scale


def mean_line3_reflex(cl, xmaxc, x):
    x = np.asarray(x, dtype=np.float64)
    r, k1, k21 = get_rk1k2(xmaxc)
    r3 = r**3
    mr3 = (1.0 - r) ** 3
    ym = np.empty_like(x)
    ymp = np.empty_like(x)
    for k, xx in enumerate(x):
        if xx < r:
            ym[k] = (xx - r) ** 3 - k21 * mr3 * xx - xx * r3 + r3
            ymp[k] = 3.0 * (xx - r) ** 2 - k21 * mr3 - r3
        else:
            ym[k] = k21 * (xx - r) ** 3 - k21 * mr3 * xx - xx * r3 + r3
            ymp[k] = 3.0 * k21 * (xx - r) ** 2 - k21 * mr3 - r3
    scale = k1 * cl / 1.8
    return ym * scale, ymp * scale


def mean_line6(a, cl, x):
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    ym = np.zeros(n, dtype=np.float64)
    ymp = np.zeros(n, dtype=np.float64)
    oma = 1.0 - a
    if abs(oma) < _EPS:
        for k, xx in enumerate(x):
            omx = 1.0 - xx
            if xx < _EPS or omx < _EPS:
                continue
            ym[k] = omx * math.log(omx) + xx * math.log(xx)
            ymp[k] = math.log(omx) - math.log(xx)
        ym *= -cl * (0.25 / _PI)
        ymp *= cl * (0.25 / _PI)
        return ym, ymp

    for k, xx in enumerate(x):
        omx = 1.0 - xx
        if xx < _EPS or abs(omx) < _EPS:
            continue
        if abs(a) < _EPS:
            g = -0.25
            h = -0.5
        else:
            g = -(a * a * (0.5 * math.log(a) - 0.25) + 0.25) / oma
            h = g + (0.5 * oma * oma * math.log(oma) - 0.25 * oma * oma) / oma
        amx = a - xx
        if abs(amx) < _EPS:
            term1 = 0.0
            term1p = 0.0
        else:
            term1 = amx * amx * (2.0 * math.log(abs(amx)) - 1.0)
            term1p = -amx * math.log(abs(amx))
        term2 = omx * omx * (1.0 - 2.0 * math.log(omx))
        term2p = omx * math.log(omx)
        ym[k] = 0.25 * (term1 + term2) / oma - xx * math.log(xx) + g - h * xx
        ymp[k] = (term1p + term2p) / oma - 1.0 - math.log(xx) - h
    scale = cl / (_TWOPI * (a + 1.0))
    return ym * scale, ymp * scale


def mean_line6m(cl, x):
    x = np.asarray(x, dtype=np.float64)
    a = 0.8
    n = x.size
    ym = np.zeros(n, dtype=np.float64)
    ymp = np.zeros(n, dtype=np.float64)
    oma = 1.0 - a
    te_slope = -0.24521 * cl
    for k, xx in enumerate(x):
        if xx < _EPS:
            continue
        omx = 1.0 - xx
        if omx < _EPS:
            ymp[k] = te_slope
            continue
        g = -(a * a * (0.5 * math.log(a) - 0.25) + 0.25) / oma
        h = g + (0.5 * oma * oma * math.log(oma) - 0.25 * oma * oma) / oma
        amx = a - xx
        if abs(amx) < _EPS:
            term1 = 0.0
            term1p = 0.0
        else:
            term1 = amx * amx * (2.0 * math.log(abs(amx)) - 1.0)
            term1p = -amx * math.log(abs(amx))
        term2 = omx * omx * (1.0 - 2.0 * math.log(omx))
        term2p = omx * math.log(omx)
        ym[k] = 0.25 * (term1 + term2) / oma - xx * math.log(xx) + g - h * xx
        ymp[k] = (term1p + term2p) / oma - 1.0 - math.log(xx) - h
    scale = cl * 0.97948 / (_TWOPI * (a + 1.0))
    ym *= scale
    ymp *= scale
    for k, xx in enumerate(x):
        if xx > 0.86:
            ym[k] = te_slope * (xx - 1.0)
            ymp[k] = te_slope
    return ym, ymp


def combine_thickness_and_camber(x, thick, y, yp):
    x = np.asarray(x, dtype=np.float64)
    thick = np.asarray(thick, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    yp = np.asarray(yp, dtype=np.float64)
    s = np.sin(np.arctan(yp))
    c = np.cos(np.arctan(yp))
    return x - thick * s, y + thick * c, x + thick * s, y - thick * c


def add_trailing_edge_point_if_needed(x, y):
    x = np.array(x, dtype=np.float64, copy=True)
    y = np.array(y, dtype=np.float64, copy=True)
    if x[-1] >= 1.0:
        return x, y
    xn = float(x[-1])
    yn = float(y[-1])
    slope = (yn - float(y[-2])) / (xn - float(x[-2]))
    return (
        np.append(x, 1.0),
        np.append(y, yn + slope * (1.0 - xn)),
    )


def parametrize_airfoil(xupper, yupper, xlower, ylower):
    nupper = len(xupper)
    nn = nupper + len(xlower) - 1
    x = np.empty(nn, dtype=np.float64)
    y = np.empty(nn, dtype=np.float64)
    x[:nupper] = np.asarray(xupper, dtype=np.float64)[::-1]
    y[:nupper] = np.asarray(yupper, dtype=np.float64)[::-1]
    x[nupper:] = np.asarray(xlower, dtype=np.float64)[1:]
    y[nupper:] = np.asarray(ylower, dtype=np.float64)[1:]
    s = np.empty(nn, dtype=np.float64)
    s[0] = 0.0
    ds = np.hypot(np.diff(x), np.diff(y))
    s[1:] = np.cumsum(ds)
    return s, x, y


def interpolate_upper_and_lower(xupper, yupper, xlower, ylower, x):
    xu, yu = add_trailing_edge_point_if_needed(xupper, yupper)
    xl, yl = add_trailing_edge_point_if_needed(xlower, ylower)
    nupper = len(xu)
    s, xs, ys = parametrize_airfoil(xu, yu, xl, yl)
    xp = fmm_spline(s, xs)
    yp = fmm_spline(s, ys)
    x = np.asarray(x, dtype=np.float64)
    yu_out = np.empty(x.size, dtype=np.float64)
    yl_out = np.empty(x.size, dtype=np.float64)
    tol = 1e-6
    s_u = s[:nupper]
    x_u = xs[:nupper]
    y_u = ys[:nupper]
    xp_u = xp[:nupper]
    yp_u = yp[:nupper]
    s_l = s[nupper - 1 :]
    x_l = xs[nupper - 1 :]
    y_l = ys[nupper - 1 :]
    xp_l = xp[nupper - 1 :]
    yp_l = yp[nupper - 1 :]
    for k, xk in enumerate(x):
        sbar, _err = spline_zero(s_u, x_u, xp_u, float(xk), tol)
        yu_out[k] = pc_lookup(s_u, y_u, yp_u, sbar)[0]
        sbar, _err = spline_zero(s_l, x_l, xp_l, float(xk), tol)
        yl_out[k] = pc_lookup(s_l, y_l, yp_l, sbar)[0]
    return yu_out, yl_out
