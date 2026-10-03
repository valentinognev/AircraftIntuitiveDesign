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
# flight condition carried one. Only two things on this panel really fly at the
# sideslip angle: Tornado, whose state["betha"] comes from AERO["BETA"], and
# flow5's force channels, whose polar is the one place flow5 takes a beta. DATCOM
# and AVL have no sideslip capability in their interfaces at all, so they are at
# zero whatever the model says -- and so is flow5's stability-derivative block,
# which ``computeStabilityDerivatives`` builds from windDirection(alpha, 0.0).
_BETA_ZERO = " (beta=0)"


def _label(name: str, beta: float, *, at_zero_sideslip: bool) -> str:
    """The series name, marked when a non-zero flight sideslip did not reach it."""
    if at_zero_sideslip and beta != 0.0:
        return f"{name}{_BETA_ZERO}"
    return name


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

    ``beta`` is the flight condition's sideslip angle in degrees. Only DATCOM and
    AVL are relabelled from it; Tornado and flow5 both actually fly it.
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
    if flow5 and flow5 in fres and "alpha" in fres:
        series.append(
            {
                "label": "flow5",
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

    Every series here but Tornado's was differentiated at zero sideslip: DATCOM
    and AVL cannot be flown at one, and flow5's StabDerivatives are built from
    windDirection(alpha, 0.0) whatever the polar's beta. So flow5 gets the same
    "(beta=0)" mark as they do, unlike in :func:`overlay_vs_alpha`.
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
                "label": _label("flow5", beta, at_zero_sideslip=True),
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
