"""Overlay DATCOM / Tornado / AVL series for comparison plots."""

from __future__ import annotations

import math

import numpy as np

from aid.stability import stability_lines

_DATCOM_STYLE = "g.-"
_TORNADO_STYLE = "c-"
_FLOW5_STYLE = "y.-"
_FLOW5_DERIV_STYLE = "y-"
_ND = 99998.0

# Appended to a series whose numbers were produced at zero sideslip while the
# flight condition carried one. Whether a series is one of those is a property of
# the *channel*, not of the solver that wrote it.
BETA_ZERO_SUFFIX = " (beta=0)"

# flow5's twelve StabDerivatives, and nothing else in its output, are flat in
# sideslip: computeStabilityDerivatives fixes the stability axes at
# windDirection(alphaeq, 0.0) (FLOW5/flow5-lib/analysis3d/panelanalysis.cpp:614
# and :660), so these twelve are byte-identical at beta = 0, +5 and -5. The two
# slopes are NOT in this set: CLa and Cma are ordinary least squares over the
# polar's own alpha sweep (FLOW5/run/flow5_run.cpp:526-527), and the polar is
# flown at the deck's beta, so they move (Cessna 172: 5.5402334 at beta 0,
# 5.5003748 at both +5 and -5; the +5/-5 equality is the polar's own symmetry).
FLOW5_BETA_FLAT = frozenset(
    {
        "CXa",
        "CZa",
        "CYb",
        "CYp",
        "CYr",
        "Clb",
        "Clp",
        "Clr",
        "Cnb",
        "Cnp",
        "Cnr",
        "XNP",
    }
)

# Control-derivative paths, keyed by the solver name aid.control_report prints.
# tornado and flow5 reach the model's sideslip (tornado/control_deriv.py:54 goes
# through tornado_io, flow5_controls.py:93,100 call write_flow5_deck with
# beta=None, and both resolve AERO["BETA"]); datcom, avl and the handbook have no
# sideslip capability at all.
BETA_CAPABLE_CONTROL_SOLVERS = frozenset({"tornado", "flow5"})


def beta_zero_label(name: str, beta: float) -> str:
    """``name``, marked when the flight had a sideslip that ``name`` did not fly.

    Byte-identical to ``name`` at ``beta == 0``, so every existing label and
    every existing legend is unchanged for symmetric flight.
    """
    return f"{name}{BETA_ZERO_SUFFIX}" if beta != 0.0 else name


def control_probe_label(solver: str, surface: str, coeff: str, beta: float) -> str:
    """``"<solver> <surface> <coeff>"``, marked for the paths that cannot fly beta."""
    text = f"{solver} {surface} {coeff}"
    if solver in BETA_CAPABLE_CONTROL_SOLVERS:
        return text
    return beta_zero_label(text, beta)


def _label(name: str, beta: float, *, at_zero_sideslip: bool) -> str:
    """The series name, marked when a non-zero flight sideslip did not reach it."""
    return beta_zero_label(name, beta) if at_zero_sideslip else name


def _flow5_label(key: str, beta: float) -> str:
    """flow5 is beta-flat per channel, so the key decides, not the solver name."""
    return _label("flow5", beta, at_zero_sideslip=key in FLOW5_BETA_FLAT)


def alpha_grid(results: dict, st: dict, n: int = 80) -> np.ndarray:
    datcom = results.get("datcom") or {}
    alpha = datcom.get("alpha")
    if alpha is not None:
        a = np.asarray(alpha, dtype=float).reshape(-1)
        if a.size:
            return np.linspace(float(np.nanmin(a)), float(np.nanmax(a)), n)
    return np.asarray(stability_lines(st)["alpha"], dtype=float)


def overlay_vs_alpha(
    results: dict,
    st: dict,
    *,
    datcom: str | None = None,
    tornado: tuple[str, str | None] | None = None,
    avl: str | None = None,
    flow5: str | None = None,
    beta: float = 0.0,
) -> list[dict]:
    """Same quantity vs α from each solver that has been run.

    ``beta`` is the flight condition's sideslip angle in degrees. DATCOM and AVL
    have no sideslip capability and are always marked; Tornado flies the field,
    and so does every flow5 channel this overlay plots, since they are all read
    off the polar the deck was written at.
    """
    grid = alpha_grid(results, st)
    series: list[dict] = []
    dres = results.get("datcom") or {}
    if datcom and datcom in dres and "alpha" in dres:
        x, y = _mask_nd(dres["alpha"], dres[datcom])
        series.append(
            {
                "label": _label("DATCOM", beta, at_zero_sideslip=True),
                "x": x,
                "y": y,
                "style": _DATCOM_STYLE,
                "kind": "line",
            }
        )
    tres = results.get("tornado") or {}
    if tornado:
        val_key, slope_key = tornado
        line = _vlm_line(tres, val_key, slope_key, grid, alpha_is_rad=True)
        if line is not None:
            series.append(
                {
                    "label": _label("Tornado", beta, at_zero_sideslip=False),
                    "x": grid,
                    "y": line,
                    "style": _TORNADO_STYLE,
                    "kind": "line",
                }
            )
    ares = results.get("avl") or {}
    if avl and avl in ares and "alpha" in ares:
        xs = np.asarray(ares["alpha"], dtype=float).reshape(-1)
        ys = np.asarray(ares[avl], dtype=float).reshape(-1)
        if xs.size == ys.size and xs.size > 0:
            kind = "line" if xs.size > 1 else "marker"
            series.append(
                {
                    "label": _label("AVL", beta, at_zero_sideslip=True),
                    "x": xs,
                    "y": ys,
                    "style": "m.-" if kind == "line" else "m.",
                    "kind": kind,
                }
            )
    fres = results.get("flow5") or {}
    if flow5 and flow5 in fres:
        series.append(
            {
                "label": _flow5_label(flow5, beta),
                "x": np.asarray(fres["alpha"], dtype=float),
                "y": np.asarray(fres[flow5], dtype=float),
                "style": _FLOW5_STYLE,
                "kind": "line",
            }
        )
    return series


def overlay_derivative(
    results: dict,
    st: dict,
    *,
    datcom: str | None = None,
    tornado: str | None = None,
    avl: str | None = None,
    flow5: str | None = None,
    beta: float = 0.0,
) -> list[dict]:
    """DATCOM derivative vs α (per deg). Tornado and flow5 stay horizontal; AVL is solved samples only.

    DATCOM and AVL cannot be flown at a sideslip, so they are always marked. For
    flow5 the mark depends on the channel: the twelve :data:`FLOW5_BETA_FLAT`
    scalars were differentiated at zero sideslip whatever the polar's beta, while
    CLa and Cma are slopes over that same polar and do move with it.
    """
    grid = alpha_grid(results, st)
    series: list[dict] = []
    dres = results.get("datcom") or {}
    if datcom and datcom in dres and "alpha" in dres:
        x, y = _mask_nd(dres["alpha"], dres[datcom])
        series.append(
            {
                "label": _label("DATCOM", beta, at_zero_sideslip=True),
                "x": x,
                "y": y,
                "style": _DATCOM_STYLE,
                "kind": "line",
            }
        )
    tres = results.get("tornado") or {}
    if tornado and tornado in tres:
        series.append(
            {
                "label": _label("Tornado", beta, at_zero_sideslip=False),
                "x": grid,
                "y": float(tres[tornado]) * math.pi / 180.0,
                "style": _TORNADO_STYLE,
                "kind": "hline",
            }
        )
    ares = results.get("avl") or {}
    if avl and avl in ares and "alpha" in ares:
        xs = np.asarray(ares["alpha"], dtype=float).reshape(-1)
        ys = np.asarray(ares[avl], dtype=float).reshape(-1)
        if xs.size == ys.size and xs.size > 0:
            kind = "line" if xs.size > 1 else "marker"
            series.append(
                {
                    "label": _label("AVL", beta, at_zero_sideslip=True),
                    "x": xs,
                    "y": ys * math.pi / 180.0,
                    "style": "m.-" if kind == "line" else "m.",
                    "kind": kind,
                }
            )
    fres = results.get("flow5") or {}
    if flow5 and flow5 in fres:
        series.append(
            {
                "label": _flow5_label(flow5, beta),
                "x": grid,
                "y": float(fres[flow5]) * math.pi / 180.0,
                "style": _FLOW5_DERIV_STYLE,
                "kind": "hline",
            }
        )
    return series


def _vlm_line(
    src: dict,
    val_key: str,
    slope_key: str | None,
    grid_deg: np.ndarray,
    *,
    alpha_is_rad: bool,
) -> np.ndarray | None:
    if val_key not in src:
        return None
    val = float(src[val_key])
    if not slope_key or slope_key not in src:
        return None if alpha_is_rad else np.array([val])
    slope = float(src[slope_key])
    if alpha_is_rad:
        a0 = float(src.get("alpha", 0.0))
        intercept = val - slope * a0
        return intercept + slope * np.deg2rad(grid_deg)
    a0 = float(src.get("alpha", 0.0))
    return val + slope * np.deg2rad(grid_deg - a0)


def _mask_nd(x, y) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    y = np.where(np.abs(y) >= _ND, np.nan, y)
    return x, y
