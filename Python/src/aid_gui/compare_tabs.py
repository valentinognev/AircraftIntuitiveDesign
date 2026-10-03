"""Aerodynamics comparison tabs: DATCOM / Tornado / AVL overlays."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

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

_STYLE_COLOR = {"g": "g", "c": "c", "m": "m", "b": "b", "y": "y"}
_PROBE_COEFFS = ("CL", "Cm", "Cl", "Cn", "CY")
_TORNADO_SPANWISE_LS = ("-", "--", "-.", ":")
_TORNADO_SPANWISE_LW = (2.2, 1.7, 1.4, 1.1)
_HEADER_BG = QColor("#3d444c")
_HEADER_FG = QColor("#f4f6f8")
_HEADER_STYLE = (
    "QHeaderView::section {"
    " background-color: #3d444c;"
    " color: #f4f6f8;"
    " font-weight: 600;"
    " font-size: 11pt;"
    " padding: 6px 8px;"
    " border: none;"
    " border-right: 1px solid #5c646e;"
    "}"
)


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


class _SectionsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.empty = QLabel("Analyze DATCOM / Tornado / AVL")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.defs = QTableWidget(0, 4)
        self.leftover = QTableWidget(0, 2)
        for table in (self.defs, self.leftover):
            _style_table(table)
        _apply_column_headers(self.defs, ["Quantity", "Wing", "HT", "VT"])
        _apply_column_headers(self.leftover, ["Quantity", "Value"])
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.defs)
        self.splitter.addWidget(self.leftover)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        layout.addWidget(self.empty, 1)
        layout.addWidget(self.splitter, 1)
        self.defs.hide()
        self.leftover.hide()
        self.splitter.hide()


class CompareTabs(QTabWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._canvases: dict[str, _TabCanvas] = {}
        self._sections = _SectionsPage()
        for name in TAB_NAMES:
            if name == "Sections":
                self.addTab(self._sections, name)
            else:
                canvas = _TabCanvas()
                self._canvases[name] = canvas
                self.addTab(canvas, name)
        self.hide()

    @property
    def leftover_table(self) -> QTableWidget:
        return self._sections.leftover

    @property
    def section_defs_table(self) -> QTableWidget:
        return self._sections.defs

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
            (r"$C_L$", "cl", ("CL", "CL_a"), "CLtot", "CL"),
            (r"$C_D$", "cd", ("CD", "CD_a"), "CDtot", "CD"),
            (r"$C_Y$", None, ("CY", "CY_a"), "CYtot", None),
            (r"$C_N$", "cn", ("CZ", "CZ_a"), "CZtot", None),
            (r"$C_A$", "ca", ("CX", "CX_a"), "CXtot", None),
        )
        for i, (ylabel, dkey, torn, avl, flow5) in enumerate(specs, start=1):
            ax = fig.add_subplot(2, 3, i)
            kwargs: dict = {"datcom": dkey, "tornado": torn, "avl": avl}
            if flow5 is not None:
                kwargs["flow5"] = flow5
            series = overlay_vs_alpha(results, st, **kwargs)
            _draw(ax, series, xlim=_alpha_xlim(results, st), legend=(i == 1))
            ax.set_ylabel(ylabel)
            ax.set_xlabel(r"$\alpha$ (deg)" if i > 3 else "")
        ax_ex = fig.add_subplot(2, 3, 6)
        _plot_force_extras(ax_ex, results)
        self._finish("Forces")

    def _plot_moments(self, st: dict, results: dict) -> None:
        fig = self._clear("Moments")
        specs = (
            (r"$C_m$", "cm", ("Cm", "Cm_a"), "Cmtot", "Cm"),
            (r"$C_\ell$", None, ("Cl", "Cl_a"), "Cltot", "Cl"),
            (r"$C_n$", None, ("Cn", "Cn_a"), "Cntot", "Cn"),
        )
        for i, (ylabel, dkey, torn, avl, flow5) in enumerate(specs, start=1):
            ax = fig.add_subplot(2, 2, i)
            kwargs: dict = {"datcom": dkey, "tornado": torn, "avl": avl}
            if flow5 is not None:
                kwargs["flow5"] = flow5
            _draw(
                ax,
                overlay_vs_alpha(results, st, **kwargs),
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
            (r"$C_{L\alpha}$ /deg", "cla", "CL_a", "CLa", "CLa"),
            (r"$C_{m\alpha}$ /deg", "cma", "Cm_a", "Cma", "Cma"),
            (r"$C_{Y\beta}$ /deg", "cyb", "CY_b", "CYb", "CYb"),
            (r"$C_{n\beta}$ /deg", "cnb", "Cn_b", "Cnb", "Cnb"),
            (r"$C_{\ell\beta}$ /deg", "clb", "Cl_b", "Clb", "Clb"),
        )
        for i, (ylabel, dkey, torn, avl, flow5) in enumerate(specs, start=1):
            ax = fig.add_subplot(2, 3, i)
            kwargs: dict = {"datcom": dkey, "tornado": torn, "avl": avl}
            if flow5 is not None:
                kwargs["flow5"] = flow5
            _draw(
                ax,
                overlay_derivative(results, st, **kwargs),
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
        curves = _control_probe_curves(results.get("control_derivatives"))
        n_extra = sum(1 for coeff in _PROBE_COEFFS if curves.get(coeff))
        if n_extra:
            cols = max(3, n_extra)
            ax_inc = fig.add_subplot(2, cols, 1)
            ax_dcdi = fig.add_subplot(2, cols, 2)
            ax_extra = fig.add_subplot(2, cols, 3)
        else:
            cols = 0
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
        if n_extra:
            slot = cols + 1
            for coeff in _PROBE_COEFFS:
                items = curves.get(coeff) or []
                if not items:
                    continue
                ax = fig.add_subplot(2, cols, slot)
                slot += 1
                for label, xs, ys in items:
                    ax.plot(xs, ys, ".-", label=label)
                ax.set_xlabel(r"$\delta$ (deg)")
                ax.set_ylabel(coeff)
                ax.legend(fontsize=7, loc="best", framealpha=0.75)
                _style_ax(ax)
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
                surface = wing.get("name") or ("Wing" if i == 0 else f"Wing {i + 1}")
                lab = f"Tornado {surface}"
                ls = _TORNADO_SPANWISE_LS[i % len(_TORNADO_SPANWISE_LS)]
                lw = _TORNADO_SPANWISE_LW[i % len(_TORNADO_SPANWISE_LW)]
                ax.plot(
                    wing["y"],
                    wing["Cl"],
                    color="c",
                    linestyle=ls,
                    linewidth=lw,
                    label=lab,
                )
        ax.set_xlabel("y (ft)")
        ax.set_ylabel(r"$C_\ell$")
        ax.set_title("Spanwise lift")
        ax.grid(True, alpha=0.3)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=9, loc="best", framealpha=0.75)
        _style_ax(ax)
        self._finish("Spanwise")

    def _plot_sections(self, results: dict) -> None:
        page = self._sections
        sections = (results.get("datcom") or {}).get("sections") or {}
        groups = _leftover_groups(results)
        if sections:
            _fill_section_defs(page.defs, sections)
            page.defs.show()
        else:
            page.defs.setRowCount(0)
            page.defs.hide()
        if groups:
            _fill_leftover(page.leftover, groups)
            page.leftover.show()
        else:
            page.leftover.setRowCount(0)
            page.leftover.hide()
        page.splitter.setVisible(bool(sections or groups))
        if sections and groups:
            page.splitter.setStretchFactor(0, 1)
            page.splitter.setStretchFactor(1, 2)
        elif sections:
            page.splitter.setStretchFactor(0, 1)
            page.splitter.setStretchFactor(1, 0)
        elif groups:
            page.splitter.setStretchFactor(0, 0)
            page.splitter.setStretchFactor(1, 1)
        page.empty.setVisible(not sections and not groups)

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


def _control_probe_curves(payload) -> dict[str, list[tuple[str, list[float], list[float]]]]:
    curves: dict[str, list[tuple[str, list[float], list[float]]]] = {coeff: [] for coeff in _PROBE_COEFFS}
    if not isinstance(payload, dict):
        return curves
    solver = str(payload.get("solver") or "")
    grouped: dict[str, list] = {}
    for row in payload.get("rows") or []:
        if not isinstance(row, dict) or not row.get("available"):
            continue
        surface = row.get("surface")
        if surface is None or row.get("delta_deg") is None:
            continue
        grouped.setdefault(str(surface), []).append(row)
    for surface, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: float(row["delta_deg"]))
        for coeff in _PROBE_COEFFS:
            xs: list[float] = []
            ys: list[float] = []
            for row in ordered:
                val = row.get(coeff)
                if val is None:
                    continue
                xs.append(float(row["delta_deg"]))
                ys.append(float(val))
            if xs:
                curves[coeff].append((f"{solver} {surface} {coeff}", xs, ys))
    return curves


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
        if key not in ares:
            continue
        arr = np.asarray(ares[key], dtype=float).reshape(-1)
        if arr.size != 1:
            continue
        labels.append(lab)
        torn_v.append(np.nan)
        avl_v.append(float(arr[0]))
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
        # flow5 returns exactly these and nothing else (aid/flow5_io.py), so the
        # whole key set is named here. The eight scalars would otherwise surface
        # as raw leftovers; the 17-sample arrays (beta, Cx, Cz) are already
        # excluded by the 0 < size <= 8 filter in _leftover_groups, but naming
        # them keeps that filter from being load-bearing for correctness.
        "beta",
        "Cx",
        "Cz",
        "CXa",
        "CZa",
        "CYp",
        "CYr",
        "Clr",
        "Cnp",
        "Cnr",
        "XNP",
    }
)


def _fmt_number(val) -> str:
    x = float(val)
    if not np.isfinite(x):
        return ""
    if abs(x) < 1e-10:
        return "0"
    if 1e-5 <= abs(x) < 1e4:
        return f"{x:.6f}".rstrip("0").rstrip(".")
    return f"{x:.4e}"


def _leftover_groups(results: dict) -> list[tuple[str, list[tuple[str, list[float]]]]]:
    groups: list[tuple[str, list[tuple[str, list[float]]]]] = []
    hl_rows: list[tuple[str, list[float]]] = []
    for i, block in enumerate((results.get("datcom") or {}).get("high_lift") or []):
        for key in ("delta", "dcl_max", "dcd_min", "clad", "cha", "chd"):
            if key not in block:
                continue
            arr = np.asarray(block[key], dtype=float).reshape(-1)
            hl_rows.append((f"HL{i} {key}", [float(v) for v in arr[:8]]))
    if hl_rows:
        groups.append(("DATCOM high-lift", hl_rows))
    for prefix, src in (("Tornado", results.get("tornado") or {}), ("AVL", results.get("avl") or {})):
        rows: list[tuple[str, list[float]]] = []
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
            rows.append((str(key), [float(v) for v in np.asarray(val, dtype=float).reshape(-1)[:8]]))
        if rows:
            groups.append((prefix, rows))
    return groups


def _style_table(table: QTableWidget) -> None:
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(True)
    header = table.horizontalHeader()
    header.setHighlightSections(False)
    header.setStyleSheet(_HEADER_STYLE)
    header.setMinimumHeight(32)
    table.verticalHeader().setDefaultSectionSize(26)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


def _header_font(base: QFont | None = None) -> QFont:
    font = QFont(base) if base is not None else QFont()
    font.setBold(True)
    font.setPointSize(11)
    return font


def _apply_column_headers(table: QTableWidget, labels: list[str]) -> None:
    table.setHorizontalHeaderLabels(labels)
    for col, text in enumerate(labels):
        item = table.horizontalHeaderItem(col)
        if item is None:
            item = QTableWidgetItem(text)
            table.setHorizontalHeaderItem(col, item)
        item.setFont(_header_font(item.font()))
        item.setForeground(QBrush(_HEADER_FG))
        item.setBackground(QBrush(_HEADER_BG))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)


def _resize_table_columns(table: QTableWidget) -> None:
    header = table.horizontalHeader()
    n = table.columnCount()
    if n <= 1:
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        return
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    for col in range(1, n):
        header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)


def _item(text: str, *, header: bool = False, numeric: bool = False) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    if header:
        item.setFont(_header_font(item.font()))
        item.setBackground(QBrush(_HEADER_BG))
        item.setForeground(QBrush(_HEADER_FG))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
    if numeric:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return item


def _fill_section_defs(table: QTableWidget, sections: dict) -> None:
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
    cols = ("wing", "ht", "vt")
    table.clearSpans()
    table.setColumnCount(4)
    _apply_column_headers(table, ["Quantity", "Wing", "HT", "VT"])
    table.setRowCount(len(fields))
    for row, field in enumerate(fields):
        table.setItem(row, 0, _item(field))
        for col, name in enumerate(cols, start=1):
            val = (sections.get(name) or {}).get(field)
            text = "" if val is None else _fmt_number(val)
            table.setItem(row, col, _item(text, numeric=True))
    _resize_table_columns(table)


def _fill_leftover(table: QTableWidget, groups: list[tuple[str, list[tuple[str, list[float]]]]]) -> None:
    max_n = 1
    for _, rows in groups:
        for _, vals in rows:
            max_n = max(max_n, len(vals))
    ncols = 1 + max_n
    headers = ["Quantity"] + (["Value"] if max_n == 1 else [str(i) for i in range(1, max_n + 1)])
    table.clearSpans()
    table.setColumnCount(ncols)
    _apply_column_headers(table, headers)
    table.setRowCount(sum(1 + len(rows) for _, rows in groups))
    row = 0
    for title, rows in groups:
        for col in range(ncols):
            table.setItem(row, col, _item(title if col == 0 else "", header=True))
        if ncols > 1:
            table.setSpan(row, 0, 1, ncols)
        row += 1
        for qty, vals in rows:
            table.setItem(row, 0, _item(qty))
            for i, val in enumerate(vals):
                table.setItem(row, 1 + i, _item(_fmt_number(val), numeric=True))
            row += 1
    _resize_table_columns(table)


def _finite_scalar(val) -> float:
    arr = np.asarray(val, dtype=float).reshape(-1)
    if arr.size != 1 or not np.isfinite(arr[0]):
        return np.nan
    return float(arr[0])


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
    tvals = [_finite_scalar(tres[tk]) if tk in tres else np.nan for _, tk, _ in groups]
    avals = [_finite_scalar(ares[ak]) if ak in ares else np.nan for _, _, ak in groups]
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
