"""Aerodynamics comparison tabs: DATCOM / Tornado / AVL overlays."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QSizePolicy, QTabWidget

from aid.lifting_line import lifting_line
from aid.solver_overlay import alpha_grid, overlay_derivative, overlay_vs_alpha
from aid.viz import planform_stations

TAB_NAMES = (
    "Forces",
    "Moments",
    "Derivatives",
    "Downwash",
    "Controls",
    "Spanwise",
    "Sections",
)

_STYLE_COLOR = {"g": "g", "c": "c", "m": "m", "b": "b"}


class _TabCanvas(FigureCanvasQTAgg):
    def __init__(self) -> None:
        fig = Figure()
        if hasattr(fig, "set_layout_engine"):
            fig.set_layout_engine("none")
        super().__init__(fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(180)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.sync_figure_size()
        self.draw_idle()

    def sync_figure_size(self) -> None:
        w, h = self.width(), self.height()
        if w < 20 or h < 20:
            return
        dpi = float(self.figure.dpi) or 100.0
        self.figure.set_size_inches(w / dpi, h / dpi, forward=False)
        fill_figure(self.figure)


class CompareTabs(QTabWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._canvases: dict[str, _TabCanvas] = {}
        for name in TAB_NAMES:
            canvas = _TabCanvas()
            self._canvases[name] = canvas
            self.addTab(canvas, name)
        self.hide()

    def figure(self, name: str):
        return self._canvases[name].figure

    def plot(self, st: dict, results: dict, ac=None, *, angle: bool = True) -> None:
        self._plot_forces(st, results)
        self._plot_moments(st, results)
        self._plot_derivatives(st, results)
        self._plot_downwash(results)
        self._plot_controls(results)
        self._plot_spanwise(results, ac, angle=angle)
        self._plot_sections(results)

    def _plot_forces(self, st: dict, results: dict) -> None:
        fig = self._clear("Forces")
        specs = (
            (r"$C_L$", "cl", ("CL", "CL_a"), ("CLtot", "CLa")),
            (r"$C_D$", "cd", ("CD", "CD_a"), ("CDtot", None)),
            (r"$C_Y$", None, ("CY", "CY_a"), ("CYtot", "CYa")),
            (r"$C_N$", "cn", ("CZ", "CZ_a"), ("CZtot", None)),
            (r"$C_A$", "ca", ("CX", "CX_a"), ("CXtot", None)),
        )
        for i, (ylabel, dkey, torn, avl) in enumerate(specs, start=1):
            ax = fig.add_subplot(2, 3, i)
            series = overlay_vs_alpha(results, st, datcom=dkey, tornado=torn, avl=avl)
            _draw(ax, series, xlim=_alpha_xlim(results, st), legend=(i == 1))
            ax.set_ylabel(ylabel)
            ax.set_xlabel(r"$\alpha$ (deg)" if i > 3 else "")
        ax_ex = fig.add_subplot(2, 3, 6)
        _plot_force_extras(ax_ex, results)
        self._finish("Forces")

    def _plot_moments(self, st: dict, results: dict) -> None:
        fig = self._clear("Moments")
        specs = (
            (r"$C_m$", "cm", ("Cm", "Cm_a"), ("Cmtot", "Cma")),
            (r"$C_\ell$", None, ("Cl", "Cl_a"), ("Cltot", "Cla")),
            (r"$C_n$", None, ("Cn", "Cn_a"), ("Cntot", "Cna")),
        )
        for i, (ylabel, dkey, torn, avl) in enumerate(specs, start=1):
            ax = fig.add_subplot(2, 2, i)
            _draw(
                ax,
                overlay_vs_alpha(results, st, datcom=dkey, tornado=torn, avl=avl),
                xlim=_alpha_xlim(results, st),
                legend=(i == 1),
            )
            ax.set_ylabel(ylabel)
            ax.set_xlabel(r"$\alpha$ (deg)" if i > 2 else "")
        ax_xcp = fig.add_subplot(2, 2, 4)
        _draw(ax_xcp, overlay_vs_alpha(results, st, datcom="xcp"), xlim=_alpha_xlim(results, st), legend=False)
        ax_xcp.set_ylabel(r"$X_{CP}$")
        ax_xcp.set_xlabel(r"$\alpha$ (deg)")
        self._finish("Moments")

    def _plot_derivatives(self, st: dict, results: dict) -> None:
        fig = self._clear("Derivatives")
        specs = (
            (r"$C_{L\alpha}$ /deg", "cla", "CL_a", "CLa"),
            (r"$C_{m\alpha}$ /deg", "cma", "Cm_a", "Cma"),
            (r"$C_{Y\beta}$ /deg", "cyb", "CY_b", "CYb"),
            (r"$C_{n\beta}$ /deg", "cnb", "Cn_b", "Cnb"),
            (r"$C_{\ell\beta}$ /deg", "clb", "Cl_b", "Clb"),
        )
        for i, (ylabel, dkey, torn, avl) in enumerate(specs, start=1):
            ax = fig.add_subplot(2, 3, i)
            _draw(
                ax,
                overlay_derivative(results, st, datcom=dkey, tornado=torn, avl=avl),
                xlim=_alpha_xlim(results, st),
                legend=(i == 1),
            )
            ax.set_ylabel(ylabel)
            ax.set_xlabel(r"$\alpha$ (deg)" if i > 3 else "")
        ax_bar = fig.add_subplot(2, 3, 6)
        _plot_rate_bars(ax_bar, results)
        self._finish("Derivatives")

    def _plot_downwash(self, results: dict) -> None:
        fig = self._clear("Downwash")
        dres = results.get("datcom") or {}
        alpha = dres.get("alpha")
        specs = (
            (r"$\varepsilon$ (deg)", "epslon"),
            (r"$d\varepsilon/d\alpha$", "depsda"),
            (r"$q/q_\infty$", "q_qinf"),
        )
        for i, (ylabel, key) in enumerate(specs, start=1):
            ax = fig.add_subplot(1, 3, i)
            if alpha is not None and key in dres:
                ax.plot(alpha, dres[key], "g.-", label="DATCOM")
                if i == 1:
                    ax.legend(fontsize=9, loc="best", framealpha=0.75)
            ax.set_ylabel(ylabel)
            ax.set_xlabel(r"$\alpha$ (deg)")
            _style_ax(ax)
            xlim = _alpha_xlim(results)
            if xlim:
                ax.set_xlim(*xlim)
            ax.grid(True, alpha=0.3)
        self._finish("Downwash")

    def _plot_controls(self, results: dict) -> None:
        fig = self._clear("Controls")
        ax_inc = fig.add_subplot(1, 3, 1)
        ax_dcdi = fig.add_subplot(1, 3, 2)
        ax_extra = fig.add_subplot(1, 3, 3)
        dres = results.get("datcom") or {}
        blocks = dres.get("high_lift") or []
        if blocks:
            xs = np.arange(len(blocks))
            labels = [b.get("config", f"δ={b.get('delta', 0)}")[:24] for b in blocks]
            ax_inc.bar(xs - 0.15, [b["dcl"] for b in blocks], 0.3, label=r"DATCOM $\Delta C_L$")
            ax_inc.bar(xs + 0.15, [b["dcm"] for b in blocks], 0.3, label=r"DATCOM $\Delta C_m$")
            ax_inc.set_xticks(list(xs))
            ax_inc.set_xticklabels(labels, rotation=15, ha="right", fontsize=8)
            for b in blocks:
                if len(b.get("dcdi_alpha", [])):
                    ax_dcdi.plot(
                        b["dcdi_alpha"],
                        b["dcdi"],
                        "g.-",
                        label=f"DATCOM ΔCDi δ={b.get('delta', 0):.1f}",
                    )
        tres = results.get("tornado") or {}
        offset = float(len(blocks))
        for key in ("CL_d", "Cm_d", "CD_d", "Cl_d", "Cn_d", "CY_d", "CZ_d", "CX_d", "CC_d"):
            if key not in tres:
                continue
            vals = np.asarray(tres[key], dtype=float).reshape(-1)
            ax_inc.plot(offset + np.arange(vals.size), vals, "c.", markersize=10, label=f"Tornado {key}")
        ares = results.get("avl") or {}
        surfs = ares.get("surface") or []
        if surfs:
            xs = np.arange(len(surfs))
            ax_extra.plot(xs, [float(s.get("angle", 0)) for s in surfs], "m^", markersize=8, label="AVL")
            ax_extra.set_xticks(list(xs))
            ax_extra.set_xticklabels([str(s.get("name", "surf"))[:12] for s in surfs], rotation=20, ha="right", fontsize=8)
            ax_extra.set_ylabel("δ (deg)")
            ax_extra.set_title("AVL control deflection")
            ax_extra.legend(fontsize=8, loc="best", framealpha=0.75)
        elif blocks:
            xs = np.arange(len(blocks))
            ax_extra.bar(xs - 0.2, [b.get("cha", np.nan) for b in blocks], 0.2, color="g", label=r"DATCOM $(C_h)_a$")
            ax_extra.bar(xs, [b.get("chd", np.nan) for b in blocks], 0.2, color="g", alpha=0.5, label=r"DATCOM $(C_h)_d$")
            ax_extra.bar(xs + 0.2, [b.get("dcl_max", np.nan) for b in blocks], 0.2, color="0.5", label=r"DATCOM $\Delta C_{L,\mathrm{max}}$")
            ax_extra.set_xticks(list(xs))
            ax_extra.set_xticklabels(
                [b.get("config", f"δ={b.get('delta', 0)}")[:16] for b in blocks],
                rotation=15,
                ha="right",
                fontsize=8,
            )
            ax_extra.set_ylabel("per deg / increment")
            ax_extra.set_title("DATCOM hinge / max-lift")
            ax_extra.legend(fontsize=8, loc="best", framealpha=0.75)
        else:
            ax_extra.text(0.5, 0.5, "No control-surface output", ha="center", va="center", transform=ax_extra.transAxes)
            ax_extra.set_title("Control extras")
        ax_inc.set_ylabel("increment")
        ax_inc.set_title("Control increments")
        if ax_inc.get_legend_handles_labels()[0]:
            ax_inc.legend(fontsize=8, loc="best", framealpha=0.75)
        ax_dcdi.set_xlabel(r"$\alpha$ (deg)")
        ax_dcdi.set_ylabel(r"$\Delta C_{Di}$")
        ax_dcdi.set_title("Induced-drag increment")
        if ax_dcdi.get_legend_handles_labels()[0]:
            ax_dcdi.legend(fontsize=8, loc="best", framealpha=0.75)
        _style_ax(ax_inc)
        _style_ax(ax_dcdi)
        _style_ax(ax_extra)
        self._finish("Controls")

    def _plot_spanwise(self, results: dict, ac, *, angle: bool) -> None:
        fig = self._clear("Spanwise")
        ax = fig.add_subplot(111)
        if ac is not None:
            nj = 12
            y, c, _, _, theta = planform_stations(ac.WG, nj, angle, "wing")
            ll = lifting_line(ac, y, c, theta)
            ax.plot(ll["y"], ll["Cl"], "b", label="Prandtl")
        tres = results.get("tornado") or {}
        sw = tres.get("spanwise")
        if sw:
            items = sw if isinstance(sw, (list, tuple)) else [sw]
            for i, wing in enumerate(items):
                lab = "Tornado" if i == 0 else f"Tornado {i + 1}"
                ax.plot(wing["y"], wing["Cl"], "c-", label=lab)
        ax.set_xlabel("y (ft)")
        ax.set_ylabel(r"$C_\ell$")
        ax.set_title("Spanwise lift")
        ax.grid(True, alpha=0.3)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=9, loc="best", framealpha=0.75)
        _style_ax(ax)
        self._finish("Spanwise")

    def _plot_sections(self, results: dict) -> None:
        fig = self._clear("Sections")
        leftover = _leftover_rows(results)
        dres = results.get("datcom") or {}
        sections = dres.get("sections") or {}
        n_axes = 2 if sections and leftover else 1
        ax0 = fig.add_subplot(n_axes, 1, 1)
        ax0.axis("off")
        if sections:
            fields = (
                "alpha_ideal",
                "alpha_zl",
                "cl_ideal",
                "cm0",
                "cla",
                "cla_mach0",
                "xac",
                "t_c",
                "le_radius",
                "delta_y",
            )
            cols = ["wing", "ht", "vt"]
            col_labels = ["", "Wing", "HT", "VT"]
            cell = []
            for field in fields:
                row = [field]
                for col in cols:
                    val = (sections.get(col) or {}).get(field)
                    row.append("" if val is None else f"{val:.5g}")
                cell.append(row)
            table = ax0.table(cellText=cell, colLabels=col_labels, loc="center")
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            ax0.set_title("DATCOM section definitions")
            ax_left = fig.add_subplot(n_axes, 1, 2) if leftover else None
        else:
            ax0.set_title("Other solver outputs")
            ax_left = ax0
        if leftover:
            if ax_left is None:
                ax_left = ax0
            ax_left.axis("off")
            table = ax_left.table(cellText=leftover, colLabels=["quantity", "value"], loc="center")
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1.0, 1.2)
            if ax_left is not ax0:
                ax_left.set_title("Other solver outputs")
        elif not sections:
            ax0.text(0.5, 0.5, "Analyze DATCOM / Tornado / AVL", ha="center", va="center", transform=ax0.transAxes)
        self._finish("Sections")

    def _clear(self, name: str) -> Figure:
        fig = self._canvases[name].figure
        fig.clear()
        return fig

    def _finish(self, name: str) -> None:
        canvas = self._canvases[name]
        fill_figure(canvas.figure)
        canvas.sync_figure_size()
        canvas.draw()


def fill_figure(fig: Figure) -> None:
    if not fig.axes:
        return
    fig.subplots_adjust(left=0.08, right=0.99, top=0.96, bottom=0.14, hspace=0.40, wspace=0.28)


def _alpha_xlim(results: dict, st: dict | None = None) -> tuple[float, float] | None:
    dres = results.get("datcom") or {}
    alpha = dres.get("alpha")
    if alpha is not None:
        a = np.asarray(alpha, dtype=float).reshape(-1)
        if a.size:
            return float(np.nanmin(a)), float(np.nanmax(a))
    if st is not None:
        grid = alpha_grid(results, st)
        if grid.size:
            return float(grid[0]), float(grid[-1])
    return None


def _style_ax(ax) -> None:
    ax.tick_params(labelsize=9)
    ax.xaxis.label.set_size(10)
    ax.yaxis.label.set_size(11)
    ax.title.set_size(11)
    ax.grid(True, alpha=0.3)


def _draw(ax, series: list[dict], *, xlim=None, legend: bool = True) -> None:
    for s in series:
        color = _STYLE_COLOR.get(s["style"][:1], "k")
        if s["kind"] == "hline":
            ax.axhline(s["y"], color=color, linestyle="-", label=s["label"])
        else:
            ax.plot(s["x"], s["y"], s["style"], label=s["label"], markersize=6)
    if legend and series:
        ax.legend(fontsize=9, loc="best", framealpha=0.75)
    if xlim is not None:
        ax.set_xlim(*xlim)
    _style_ax(ax)


def _plot_force_extras(ax, results: dict) -> None:
    labels: list[str] = []
    torn_v: list[float] = []
    avl_v: list[float] = []
    tres = results.get("tornado") or {}
    ares = results.get("avl") or {}
    for tkey, lab in (
        ("CLwing", r"$C_{{Lw}}$"),
        ("CDwing", r"$C_{{Dw}}$"),
        ("CYwing", r"$C_{{Yw}}$"),
        ("CC", r"$C_C$"),
    ):
        if tkey not in tres:
            continue
        wings = np.asarray(tres[tkey], dtype=float).reshape(-1)
        for i, val in enumerate(wings[:4], start=1):
            suffix = str(i) if wings.size > 1 else ""
            labels.append(lab.replace("w}", f"w{suffix}}}") if "w}" in lab else lab)
            torn_v.append(float(val))
            avl_v.append(np.nan)
    for key, lab in (("CDind", r"$C_{Dind}$"), ("CDvis", r"$C_{Dvis}$"), ("e", r"$e$"), ("NP", r"$X_{np}$")):
        if key in ares:
            labels.append(lab)
            torn_v.append(np.nan)
            avl_v.append(float(ares[key]))
    x = np.arange(len(labels))
    width = 0.35
    if any(np.isfinite(torn_v)):
        ax.bar(x - width / 2, torn_v, width, color="c", label="Tornado")
    if any(np.isfinite(avl_v)):
        ax.bar(x + width / 2, avl_v, width, color="m", label="AVL")
    if labels:
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=8, rotation=20, ha="right")
        ax.legend(fontsize=8, loc="best", framealpha=0.75)
    else:
        ax.set_xticks([])
        ax.text(0.5, 0.5, "Analyze Tornado/AVL", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Per-wing / AVL extras")
    _style_ax(ax)


_SKIP_LEFTOVER = frozenset(
    {
        "cp",
        "sonicpanels",
        "sonicWarning",
        "sonicCP",
        "sonicFraction",
        "F",
        "M",
        "FORCE",
        "MOMENTS",
        "gamma",
        "dwcond",
        "spanwise",
        "vlm_mode",
        "surface",
        "alpha",
        "cl",
        "cd",
        "cm",
        "cn",
        "ca",
        "xcp",
        "cla",
        "cma",
        "cyb",
        "cnb",
        "clb",
        "q_qinf",
        "epslon",
        "depsda",
        "high_lift",
        "sections",
        "mach",
        "alt",
        "CL",
        "CD",
        "CY",
        "CZ",
        "CX",
        "Cl",
        "Cm",
        "Cn",
        "CL_a",
        "CD_a",
        "CY_a",
        "CZ_a",
        "CX_a",
        "Cl_a",
        "Cm_a",
        "Cn_a",
        "CY_b",
        "Cn_b",
        "Cl_b",
        "Cl_P",
        "Cm_Q",
        "Cn_R",
        "CL_P",
        "CL_Q",
        "CL_R",
        "CLwing",
        "CL_d",
        "Cm_d",
        "CD_d",
        "CLtot",
        "CDtot",
        "CYtot",
        "CZtot",
        "CXtot",
        "Cltot",
        "Cmtot",
        "Cntot",
        "CLa",
        "Cma",
        "CYb",
        "Cnb",
        "Clb",
        "Clp",
        "Cmq",
        "Cnr",
        "CLp",
        "CLq",
        "CLr",
        "CDind",
        "CDvis",
        "e",
        "NP",
        "CL0",
        "Cm0",
    }
)


def _fmt_scalar(val) -> str:
    arr = np.asarray(val, dtype=float).reshape(-1)
    return " ".join(f"{v:.5g}" for v in arr[:6])


def _leftover_rows(results: dict) -> list[list[str]]:
    rows: list[list[str]] = []
    dres = results.get("datcom") or {}
    for i, block in enumerate(dres.get("high_lift") or []):
        for key in ("delta", "dcl_max", "dcd_min", "clad", "cha", "chd"):
            if key in block:
                rows.append([f"DATCOM HL{i} {key}", _fmt_scalar(block[key])])
    for prefix, src in (("Tornado", results.get("tornado") or {}), ("AVL", results.get("avl") or {})):
        for key in sorted(src):
            if key in _SKIP_LEFTOVER:
                continue
            val = src[key]
            try:
                arr = np.asarray(val)
                arr_ok = arr.dtype.kind in "iufc" and arr.ndim <= 1 and 0 < arr.size <= 8
            except (TypeError, ValueError):
                arr_ok = False
            if not arr_ok:
                continue
            rows.append([f"{prefix} {key}", _fmt_scalar(val)])
    return rows


def _plot_rate_bars(ax, results: dict) -> None:
    groups = (
        (r"$C_{\ell p}$", "Cl_P", "Clp"),
        (r"$C_{mq}$", "Cm_Q", "Cmq"),
        (r"$C_{nr}$", "Cn_R", "Cnr"),
        (r"$C_{Lp}$", "CL_P", "CLp"),
        (r"$C_{Lq}$", "CL_Q", "CLq"),
        (r"$C_{Lr}$", "CL_R", "CLr"),
    )
    tres = results.get("tornado") or {}
    ares = results.get("avl") or {}
    x = np.arange(len(groups))
    tvals = [float(tres[tk]) if tk in tres else np.nan for _, tk, _ in groups]
    avals = [float(ares[ak]) if ak in ares else np.nan for _, _, ak in groups]
    width = 0.35
    if any(np.isfinite(tvals)):
        ax.bar(x - width / 2, tvals, width, color="c", label="Tornado")
    if any(np.isfinite(avals)):
        ax.bar(x + width / 2, avals, width, color="m", label="AVL")
    ax.set_xticks(list(x))
    ax.set_xticklabels([lab for lab, _, _ in groups], fontsize=8)
    ax.set_title(r"$p,q,r$ (per rad)")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=8, loc="best", framealpha=0.75)
    _style_ax(ax)
