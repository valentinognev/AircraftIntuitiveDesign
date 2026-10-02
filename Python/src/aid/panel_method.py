"""Headless 2-D vortex panel method. Port of Panel_Method.m and Coefficients.m."""

import numpy as np


def panel_method(data: np.ndarray, alpha_deg: np.ndarray) -> dict:
    """data is (M, 2) airfoil nodes, M-1 panels. alpha_deg length >= 2.
    Returns {'a0': float per rad, 'alpha0': float deg, 'Cm_ac': float, 'Cl': np.ndarray}.
    Port Panel_Method.m + Coefficients.m with plot_option forced off."""
    data = np.asarray(data, dtype=np.float64)
    alpha_deg = np.asarray(alpha_deg, dtype=np.float64).reshape(-1)
    if alpha_deg.shape[0] < 2:
        raise ValueError("alpha_deg length must be >= 2")
    alpha = np.deg2rad(alpha_deg)
    n_alpha = alpha.shape[0]
    cl_array = np.zeros(n_alpha, dtype=np.float64)
    cm_array = np.zeros(n_alpha, dtype=np.float64)
    # MATLAB `loop` is 1-based and kept after the for-loop (or a stall break).
    matlab_loop = 0
    for i, alpha_i in enumerate(alpha):
        cl, cm_c4, cp_min = _one_alpha(data, float(alpha_i))
        cl_array[i] = cl
        cm_array[i] = cm_c4
        matlab_loop = i + 1
        if cp_min < -11.0:
            break

    # Panel_Method.m: polyfit / interp1 use Alpha(1:loop-1); Cm_ac = mean(Cm_array).
    used = slice(0, matlab_loop - 1)
    a0 = float(np.polyfit(alpha[used], cl_array[used], 1)[0])
    alpha0 = float(
        _interp_linear_extrap(cl_array[used], alpha[used], 0.0) * 180.0 / np.pi
    )
    cm_ac = float(np.mean(cm_array))
    return {"a0": a0, "alpha0": alpha0, "Cm_ac": cm_ac, "Cl": cl_array}


def _one_alpha(data: np.ndarray, alpha: float) -> tuple[float, float, float]:
    A, B, theta, vels, X = _coefficients(data, alpha)
    u_source, v_source, u_vortex, v_vortex = vels
    results = np.linalg.solve(A, B)
    n = theta.shape[0]
    source = results[:n]
    vortex = results[n]
    dtheta = theta[:, None] - theta[None, :]
    s = np.sin(dtheta)
    c = np.cos(dtheta)
    C = s * v_source + c * u_source
    D = s * v_vortex + c * u_vortex
    V = np.cos(theta - alpha) + C @ source + D.sum(axis=1) * vortex
    cp = 1.0 - V**2

    # MATLAB LE = ceil(N/2)+1 (1-based) → 0-based index ceil(N/2).
    le = int(np.ceil(n / 2.0))
    cp_u = np.concatenate([np.array([1.0]), cp[le:]])
    cp_l = np.concatenate([np.array([1.0]), cp[:le][::-1]])
    x = np.concatenate([np.array([0.0]), X[le:]])
    section = np.linspace(x[0], x[-1], 1000)
    dx = section[1] - section[0]
    line1 = np.interp(section, x, cp_l)
    line2 = np.interp(section, x, cp_u)
    area = line1 - line2
    cl = float(np.trapezoid(area, dx=dx))
    cm_c4 = float(-np.trapezoid(area * (section - 0.25), dx=dx))
    return cl, cm_c4, float(np.min(cp))


def _coefficients(data: np.ndarray, alpha: float):
    x = data[:, 0]
    y = data[:, 1]
    n = x.shape[0] - 1
    x1 = x[:-1]
    y1 = y[:-1]
    x2 = x[1:]
    y2 = y[1:]
    X = 0.5 * (x1 + x2)
    Y = 0.5 * (y1 + y2)
    theta = np.arctan2(y2 - y1, x2 - x1)

    dx_n = X[:, None] - x[None, :]
    dy_n = Y[:, None] - y[None, :]
    r = np.hypot(dx_n, dy_n)

    Xi = X[:, None]
    Yi = Y[:, None]
    cross = (Yi - y2[None, :]) * (Xi - x1[None, :]) - (Xi - x2[None, :]) * (Yi - y1[None, :])
    dot = (Xi - x2[None, :]) * (Xi - x1[None, :]) + (Yi - y2[None, :]) * (Yi - y1[None, :])
    beta = np.arctan2(cross, dot)
    np.fill_diagonal(beta, np.pi)

    u_source = -np.log(r[:, 1:] / r[:, :-1]) / (2.0 * np.pi)
    v_source = beta / (2.0 * np.pi)
    u_vortex = v_source
    v_vortex = -u_source

    dtheta = theta[:, None] - theta[None, :]
    s = np.sin(dtheta)
    c = np.cos(dtheta)
    A_ij = -s * u_source + c * v_source
    A_iN1 = (c * v_vortex - s * u_vortex).sum(axis=1)
    # Kutta row uses panels i = 1 and i = N only (MATLAB i==1 || i==N).
    kutta_s = np.sin(dtheta[[0, -1], :])
    kutta_c = np.cos(dtheta[[0, -1], :])
    A_N1j = (kutta_s * v_source[[0, -1], :] + kutta_c * u_source[[0, -1], :]).sum(axis=0)
    A_N1N1 = (kutta_s * v_vortex[[0, -1], :] + kutta_c * u_vortex[[0, -1], :]).sum()

    A = np.empty((n + 1, n + 1), dtype=np.float64)
    A[:n, :n] = A_ij
    A[:n, n] = A_iN1
    A[n, :n] = A_N1j
    A[n, n] = A_N1N1

    b_i = np.sin(theta - alpha)
    b_n1 = -(np.cos(theta[0] - alpha) + np.cos(theta[-1] - alpha))
    B = np.concatenate([b_i, np.array([b_n1])])
    return A, B, theta, (u_source, v_source, u_vortex, v_vortex), X


def _interp_linear_extrap(xp: np.ndarray, fp: np.ndarray, xq: float) -> float:
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
    if xq <= xp[0]:
        slope = (fp[1] - fp[0]) / (xp[1] - xp[0])
        return float(fp[0] + slope * (xq - xp[0]))
    if xq >= xp[-1]:
        slope = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2])
        return float(fp[-1] + slope * (xq - xp[-1]))
    return float(np.interp(xq, xp, fp))
