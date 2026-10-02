"""Cubic spline procedures translated from naca456 splprocs.f90."""

import math

import numpy as np

# Fortran RESHAPE of MAGIC is column-major.
_MAGIC = np.array(
    [
        [2.0, -2.0, 1.0, 1.0],
        [-3.0, 3.0, -2.0, -1.0],
        [0.0, 0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
    ],
    dtype=np.float64,
)


def lookup(xtab, x):
    """1-based LookUp from splprocs.f90."""
    n = len(xtab)
    if n <= 0:
        return -1
    if x < xtab[0]:
        return 0
    if x > xtab[n - 1]:
        return n
    i = 1
    j = n
    while True:
        if j <= i + 1:
            break
        k = (i + j) // 2
        if x < xtab[k - 1]:
            j = k
        else:
            i = k
    return i


def _evaluate_cubic(u, a, fa, fpa, b, fb, fpb):
    d = (fb - fa) / (b - a)
    t = (u - a) / (b - a)
    p = 1.0 - t
    return p * fa + t * fb - p * t * (b - a) * (p * (d - fpa) - t * (d - fpb))


def evaluate_cubic_and_derivs(a, fa, fpa, b, fb, fpb, u):
    rhs = np.array([fa, fb, fpa * (b - a), fpb * (b - a)], dtype=np.float64)
    coef = _MAGIC @ rhs
    h = 1.0 / (b - a)
    t = (u - a) * h
    c1, c2, c3, c4 = coef
    f = c4 + t * (c3 + t * (c2 + t * c1))
    fp = h * (c3 + t * (2.0 * c2 + t * 3.0 * c1))
    fpp = h * h * (2.0 * c2 + t * 6.0 * c1)
    fppp = h * h * h * 6.0 * c1
    return f, fp, fpp, fppp


def fmm_spline(x_in, y_in):
    """FMM cubic spline slopes. Returns yp with the same length as x_in."""
    x_in = np.asarray(x_in, dtype=np.float64)
    y_in = np.asarray(y_in, dtype=np.float64)
    n = int(x_in.size)
    yp = np.zeros(n, dtype=np.float64)
    if n < 2:
        return yp
    x = np.empty(n + 1, dtype=np.float64)
    y = np.empty(n + 1, dtype=np.float64)
    x[1:] = x_in
    y[1:] = y_in
    dx = np.empty(n, dtype=np.float64)
    delta = np.empty(n, dtype=np.float64)
    for i in range(1, n):
        dx[i] = x[i + 1] - x[i]
        delta[i] = (y[i + 1] - y[i]) / dx[i]
    if n == 2:
        yp[0] = delta[1]
        yp[1] = delta[1]
        return yp
    dd = np.empty(n, dtype=np.float64)
    for i in range(1, n - 1):
        dd[i] = delta[i + 1] - delta[i]
    if n == 3:
        deriv2 = dd[1] / (x[3] - x[1])
        deriv1 = delta[1] - deriv2 * dx[1]
        yp[0] = deriv1
        yp[1] = deriv1 + deriv2 * dx[1]
        yp[2] = deriv1 + deriv2 * (x[3] - x[1])
        return yp

    alpha = np.empty(n + 1, dtype=np.float64)
    beta = np.empty(n + 1, dtype=np.float64)
    sigma = np.empty(n + 1, dtype=np.float64)
    alpha[1] = -dx[1]
    for i in range(2, n):
        alpha[i] = 2.0 * (dx[i - 1] + dx[i])
    for i in range(2, n):
        alpha[i] = alpha[i] - dx[i - 1] * dx[i - 1] / alpha[i - 1]
    alpha[n] = -dx[n - 1] - dx[n - 1] * dx[n - 1] / alpha[n - 1]

    beta[1] = dd[2] / (x[4] - x[2]) - dd[1] / (x[3] - x[1])
    beta[1] = beta[1] * dx[1] * dx[1] / (x[4] - x[1])
    for i in range(2, n):
        beta[i] = dd[i - 1]
    beta[n] = dd[n - 2] / (x[n] - x[n - 2]) - dd[n - 3] / (x[n - 1] - x[n - 3])
    beta[n] = -beta[n] * dx[n - 1] * dx[n - 1] / (x[n] - x[n - 3])
    for i in range(2, n + 1):
        beta[i] = beta[i] - dx[i - 1] * beta[i - 1] / alpha[i - 1]

    sigma[n] = beta[n] / alpha[n]
    for i in range(n - 1, 0, -1):
        sigma[i] = (beta[i] - dx[i] * sigma[i + 1]) / alpha[i]

    for i in range(1, n):
        yp[i - 1] = delta[i] - dx[i] * (sigma[i] + sigma[i] + sigma[i + 1])
    yp[n - 1] = yp[n - 2] + dx[n - 1] * 3.0 * (sigma[n] + sigma[n - 1])
    return yp


def pc_lookup(x, y, yp, u):
    """Interpolate a cubic spline. Returns f, fp, fpp, fppp."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    yp = np.asarray(yp, dtype=np.float64)
    k = lookup(x, u)
    k = max(1, min(x.size - 1, k))
    return evaluate_cubic_and_derivs(
        x[k - 1], y[k - 1], yp[k - 1], x[k], y[k], yp[k], u
    )


def _zeroin(ax, bx, func, tol):
    zero = 0.0
    one = 1.0
    two = 2.0
    three = 3.0
    eps = float(np.finfo(np.float64).eps)
    a = ax
    b = bx
    fa = func(a)
    fb = func(b)
    c = b
    fc = fb
    d = b - a
    e = d
    for _ in range(500):
        if (fb > zero and fc > zero) or (fb < zero and fc < zero):
            c = a
            fc = fa
            d = b - a
            e = d
        # Fortran assigns these one at a time, so c and fc receive the new a and fa.
        if abs(fc) < abs(fb):
            a, b, c = b, c, b
            fa, fb, fc = fb, fc, fb
        tol1 = two * eps * abs(b) + 0.5 * tol
        xm = 0.5 * (c - b)
        if abs(xm) <= tol1 or fb == 0.0:
            return b
        # Condition copied from splprocs.f90 Zeroin.
        if abs(e) <= tol1 and abs(fa) > abs(fb):
            if a == c:
                s = fb / fa
                p = two * xm * s
                q = one - s
            else:
                q = fa / fc
                r = fb / fc
                s = fb / fa
                p = s * (two * xm * q * (q - r) - (b - a) * (r - one))
                q = (q - one) * (r - one) * (s - one)
            if p > zero:
                q = -q
            p = abs(p)
            if p + p < min(three * xm * q - abs(tol1 * q), abs(e * q)):
                e = d
                d = p / q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d
        a = b
        fa = fb
        if abs(d) > tol1:
            b = b + d
        else:
            b = b + math.copysign(tol1, xm)
        fb = func(b)
    return b


def spline_zero(x, f, fp, fbar, tol):
    """Return (xbar, err_code) solving spline(x) = fbar."""
    x = np.asarray(x, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)
    fp = np.asarray(fp, dtype=np.float64)
    n = int(x.size)
    for k in range(n):
        if abs(f[k] - fbar) < tol:
            return float(x[k]), 0
    f_local = f - fbar
    right = None
    for k in range(1, n):
        if f_local[k - 1] * f_local[k] < 0.0:
            right = k
            break
    if right is None:
        return float(x[-1]), 1
    a_c = float(x[right - 1])
    fa = float(f_local[right - 1])
    fpa = float(fp[right - 1])
    b_c = float(x[right])
    fb = float(f_local[right])
    fpb = float(fp[right])

    def cubic(u, a_c=a_c, fa=fa, fpa=fpa, b_c=b_c, fb=fb, fpb=fpb):
        return _evaluate_cubic(u, a_c, fa, fpa, b_c, fb, fpb)

    return float(_zeroin(a_c, b_c, cubic, tol)), 0


def interpolate_polynomial(x, y, u):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    du = u - x
    total = 0.0
    n = x.size
    for j in range(n):
        fact = 1.0
        for i in range(n):
            if i != j:
                fact *= du[i] / (x[j] - x[i])
        total += y[j] * fact
    return total


def table_lookup(x, y, order, u):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    m = min(order + 1, x.size)
    j = lookup(x, u)
    j = j - (m // 2 - 1)
    j = min(1 + x.size - m, j)
    j = max(1, j)
    sl = slice(j - 1, j - 1 + m)
    return interpolate_polynomial(x[sl], y[sl], u)
