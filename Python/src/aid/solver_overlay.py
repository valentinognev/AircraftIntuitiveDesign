"""Overlay DATCOM / Tornado / AVL series for comparison plots."""

from __future__ import annotations

import math

import numpy as np

from aid.stability import stability_lines

_DATCOM_STYLE = "g.-"
_TORNADO_STYLE = "c-"
_AVL_STYLE = "m-"
_FLOW5_STYLE = "y.-"
_FLOW5_DERIV_STYLE = "y-"
_ND = 99998.0


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
    avl: tuple[str, str | None] | None = None,
    flow5: str | None = None,
) -> list[dict]:
    """Same quantity vs α from each solver that has been run."""
    grid = alpha_grid(results, st)
    series: list[dict] = []
    dres = results.get("datcom") or {}
    if datcom and datcom in dres and "alpha" in dres:
        x, y = _mask_nd(dres["alpha"], dres[datcom])
        series.append(
            {
                "label": "DATCOM",
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
                    "label": "Tornado",
                    "x": grid,
                    "y": line,
                    "style": _TORNADO_STYLE,
                    "kind": "line",
                }
            )
    ares = results.get("avl") or {}
    if avl:
        val_key, slope_key = avl
        line = _vlm_line(ares, val_key, slope_key, grid, alpha_is_rad=False)
        if line is not None:
            kind = "line" if slope_key and slope_key in ares else "marker"
            series.append(
                {
                    "label": "AVL",
                    "x": grid if kind == "line" else np.array([_avl_alpha_deg(ares, st)]),
                    "y": line if kind == "line" else np.array([float(ares[val_key])]),
                    "style": _AVL_STYLE if kind == "line" else "m.",
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
) -> list[dict]:
    """DATCOM derivative vs α (per deg) with Tornado/AVL as per-deg horizontals."""
    grid = alpha_grid(results, st)
    series: list[dict] = []
    dres = results.get("datcom") or {}
    if datcom and datcom in dres and "alpha" in dres:
        x, y = _mask_nd(dres["alpha"], dres[datcom])
        series.append(
            {
                "label": "DATCOM",
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
                "label": "Tornado",
                "x": grid,
                "y": float(tres[tornado]) * math.pi / 180.0,
                "style": _TORNADO_STYLE,
                "kind": "hline",
            }
        )
    ares = results.get("avl") or {}
    if avl and avl in ares:
        series.append(
            {
                "label": "AVL",
                "x": grid,
                "y": float(ares[avl]) * math.pi / 180.0,
                "style": _AVL_STYLE,
                "kind": "hline",
            }
        )
    fres = results.get("flow5") or {}
    if flow5 and flow5 in fres:
        series.append(
            {
                "label": "flow5",
                "x": grid,
                "y": float(fres[flow5]) * math.pi / 180.0,
                "style": _FLOW5_DERIV_STYLE,
                "kind": "hline",
            }
        )
    return series


def _avl_alpha_deg(avl: dict, st: dict) -> float:
    if "alpha" in avl:
        return float(avl["alpha"])
    return float(st["alpha"])


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
