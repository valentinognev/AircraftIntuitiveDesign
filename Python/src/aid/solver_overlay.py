"""Overlay DATCOM / Tornado / AVL series for comparison plots."""

from __future__ import annotations

import math
import re
import warnings
from functools import lru_cache

import numpy as np

from aid import paths
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
# sideslip. Measured, not inferred: on Cessna 172, Learjet 23 and F-16 every one of
# the twelve is byte-identical at beta = 0, +5 and -5, max |delta| exactly 0.0 across
# all 17 alphas of the sweep. The mechanism agrees: neither differentiation ever sees
# the sideslip. computeStabilityDerivatives (panelanalysis.cpp:614) and
# computeAngularDerivatives (:887) each declare their own `double beta(0.0);` (:636
# and :897) and each pin the stability axes at windDirection(alphaeq, 0.0) (:660 and
# :922); panelanalysis.cpp contains no betaSpec at all. The angular-rate keys (CYp,
# CYr, Clp, Clr, Cnp, Cnr) were first listed here by inference from that code and only
# later measured. They are kept, and now on the measurement.
#
# The two slopes are NOT in this set: CLa and Cma are ordinary least squares over the
# polar's own alpha sweep (FLOW5/run/flow5_run.cpp:556-557), and the polar is flown at
# the deck's beta, so they move (Cessna 172: 5.5402333786223235 at beta 0,
# 5.500374829746751 at +5, 5.500374817599451 at -5; the +5/-5 equality is the polar's
# own symmetry).
#
# Note on names: Clq, Cmp and Cmr are AVL spellings (aid/avl_parse.py). flow5 has no
# such channels -- its rate derivatives are CYp, CYr, Clp, Clr, Cnp and Cnr -- so a
# mirror listing Clq/Cmp/Cmr is reading the wrong solver's namespace.
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

# The twelve names, read from the C++ that emits them rather than copied from the set
# above: FLOW5/run/flow5_run.cpp's stab_derivative_fields() holds one
# {"NAME", &StabDerivatives::NAME} literal per channel (:283-297). Parsing that is what
# makes FLOW5_BETA_FLAT verifiable instead of merely asserted -- a 13th derivative added
# there shows up as a gap instead of silently claiming it flew at beta.
_FLOW5_STAB_DERIVATIVE_FIELDS = re.compile(
    r'\{"(\w+)",\s*&StabDerivatives::\w+\}'
)
_FLOW5_RUN_CPP = "FLOW5/run/flow5_run.cpp"


class Flow5BetaFlatGap(UserWarning):
    """A flow5 StabDerivative is emitted but missing from FLOW5_BETA_FLAT."""


@lru_cache(maxsize=1)
def flow5_emitted_stab_derivatives() -> frozenset[str]:
    """The StabDerivative names ``flow5_run.cpp`` emits, or empty if unreadable.

    The C++ is the single source of truth for this list; nothing here duplicates it.
    Empty rather than raising when the source is not in the tree, so an installed
    ``aid`` without the FLOW5 checkout keeps working -- it just cannot run the guard.
    """
    try:
        source = (paths.repo_root() / _FLOW5_RUN_CPP).read_text(encoding="utf-8")
    except OSError:
        return frozenset()
    return frozenset(_FLOW5_STAB_DERIVATIVE_FIELDS.findall(source))


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
    """flow5 is beta-flat per channel, so the key decides, not the solver name.

    An unknown channel stays unmarked, which is the panel's default and is wrong
    only for a channel that is beta-flat -- so exactly that case is checked against
    the C++ and made loud. A new StabDerivative must be added to
    :data:`FLOW5_BETA_FLAT` or it will plot as if it flew the flight condition.
    """
    if key in FLOW5_BETA_FLAT:
        return _label("flow5", beta, at_zero_sideslip=True)
    emitted = flow5_emitted_stab_derivatives()
    if key in emitted:
        warnings.warn(
            f"flow5 emits {key!r} as a StabDerivative but it is missing from "
            "FLOW5_BETA_FLAT, so its series is labelled as if it flew the model's "
            "sideslip. Add it if computeStabilityDerivatives still pins beta = 0.",
            Flow5BetaFlatGap,
            stacklevel=3,
        )
    return _label("flow5", beta, at_zero_sideslip=False)


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
    if flow5 and flow5 in fres and "alpha" in fres:
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
