import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from aid.stability import drag_vs_speed, stability_lines


class ResultsPanel(FigureCanvasQTAgg):
    def __init__(self) -> None:
        self._figure = Figure(figsize=(4, 3))
        super().__init__(self._figure)
        self.setMinimumHeight(160)
        self._ax = self._figure.add_subplot(111)
        self._ax.set_xlabel("alpha (deg)")
        self._ax.set_ylabel("CL")
        self.hide()

    def plot_datcom(self, coeffs: dict) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.plot(coeffs["alpha"], coeffs["cl"], "o-", color="C0")
        ax.set_xlabel("alpha (deg)")
        ax.set_ylabel("CL")
        ax.grid(True, alpha=0.3)
        cl = np.asarray(coeffs["cl"], dtype=float)
        ax.set_ylim(-0.5, max(2.0, 1.1 * float(np.nanmax(cl))))
        self._safe_tight_layout()
        self.draw()

    def plot_stability(self, st: dict, results: dict) -> None:
        lines = stability_lines(st)
        self._figure.clear()
        ax_cl = self._figure.add_subplot(211)
        ax_cm = self._figure.add_subplot(212)
        marker = "r" if st["Cm_CL"] > 0 else "g"
        ax_cl.plot(st["alpha"], lines["CL_trim"], marker + ".", markersize=14, label="Cruise")
        ax_cl.plot(lines["alpha"], lines["CL"], "b", label="Approximated")
        ax_cm.plot(st["alpha"], lines["Cm_trim"], marker + ".", markersize=14, label="Cruise")
        ax_cm.plot(lines["alpha"], lines["Cm"], "b", label="Approximated")
        datcom = results.get("datcom")
        if datcom and "cl" in datcom:
            ax_cl.plot(datcom["alpha"], datcom["cl"], "g.-", label="DATCOM")
            if "cm" in datcom:
                ax_cm.plot(datcom["alpha"], datcom["cm"], "g.-", label="DATCOM")
        tornado = results.get("tornado")
        if tornado and "CL_a" in tornado:
            alpha_rad = tornado.get("alpha")
            if alpha_rad is None:
                alpha_rad = np.deg2rad(st["alpha"])
            cl0 = tornado.get("CL0")
            if cl0 is None and "CL" in tornado:
                cl0 = tornado["CL"] - tornado["CL_a"] * alpha_rad
            if cl0 is not None:
                ax_cl.plot(
                    lines["alpha"],
                    cl0 + tornado["CL_a"] * lines["alpha"] * np.pi / 180,
                    "c-",
                    label="Tornado",
                )
            if "Cm_a" in tornado:
                cm0 = tornado.get("Cm0")
                if cm0 is None and "Cm" in tornado:
                    cm0 = tornado["Cm"] - tornado["Cm_a"] * alpha_rad
                if cm0 is None:
                    cm0 = 0.0
                ax_cm.plot(
                    lines["alpha"],
                    cm0 + tornado["Cm_a"] * lines["alpha"] * np.pi / 180,
                    "c-",
                    label="Tornado",
                )
        avl = results.get("avl") or {}
        if "alpha" in avl:
            alpha_avl = np.asarray(avl["alpha"], dtype=float).reshape(-1)
            if "CLtot" in avl:
                cl_avl = np.asarray(avl["CLtot"], dtype=float).reshape(-1)
                if cl_avl.size == alpha_avl.size and alpha_avl.size > 0:
                    ax_cl.plot(alpha_avl, cl_avl, "m.-", label="AVL")
            if "Cmtot" in avl:
                cm_avl = np.asarray(avl["Cmtot"], dtype=float).reshape(-1)
                if cm_avl.size == alpha_avl.size and alpha_avl.size > 0:
                    ax_cm.plot(alpha_avl, cm_avl, "m.-", label="AVL")
        flow5 = results.get("flow5")
        if flow5 and "alpha" in flow5:
            alpha_f5 = np.asarray(flow5["alpha"], dtype=float)
            if "CL" in flow5:
                ax_cl.plot(alpha_f5, np.asarray(flow5["CL"], dtype=float), "y.-", label="flow5")
            if "Cm" in flow5:
                ax_cm.plot(alpha_f5, np.asarray(flow5["Cm"], dtype=float), "y.-", label="flow5")
        ax_cl.plot([-100, 100], [0, 0], "k", linewidth=0.8)
        ax_cl.plot([0, 0], [-100, 100], "k", linewidth=0.8)
        ax_cm.plot([-100, 100], [0, 0], "k", linewidth=0.8)
        ax_cm.plot([0, 0], [-100, 100], "k", linewidth=0.8)
        alim = (float(lines["alpha"][0]), float(lines["alpha"][-1]))
        cl_hi = max(2.0, 1.1 * float(st["CL"]))
        cmval = 1.1 * (float(st["Cm0"]) + float(st["Cma"]) * float(st["alpha"]))
        cm_lo, cm_hi = min(-0.2, cmval), max(0.4, cmval)
        ax_cl.set_xlim(*alim)
        ax_cl.set_ylim(-0.5, cl_hi)
        ax_cm.set_xlim(*alim)
        ax_cm.set_ylim(cm_lo, cm_hi)
        ax_cl.set_title(r"$C_L$ vs. $\alpha$")
        ax_cl.set_xlabel(r"Angle of Attack, $\alpha$ (deg)")
        ax_cl.set_ylabel(r"Lift Coefficient, $C_L$")
        ax_cm.set_title(r"$C_m$ vs. $\alpha$")
        ax_cm.set_xlabel(r"Angle of Attack, $\alpha$ (deg)")
        ax_cm.set_ylabel(r"Moment Coefficient, $C_m$")
        ax_cl.legend()
        ax_cm.legend()
        ax_cl.grid(True, alpha=0.3)
        ax_cm.grid(True, alpha=0.3)
        self._safe_tight_layout()
        self.draw()

    def plot_drag(self, st: dict) -> None:
        drag = drag_vs_speed(st)
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.plot(drag["v"], drag["D_i"], label="Induced")
        ax.plot(drag["v"], drag["D_0"], label="Profile")
        ax.plot(drag["v"], drag["D"], label="Total")
        d_tr = np.interp(drag["v_tr"], drag["v"], drag["D"])
        ax.plot(drag["v_tr"], d_tr, "g*")
        ax.legend()
        ax.set_title(rf"Drag: $(C_D = {drag['cd_eq']}C_L^2)$")
        ax.set_xlabel(drag["xlabel"])
        ax.set_ylabel("Drag (lb)")
        ax.set_xlim(float(drag["v"][0]), float(drag["v"][-1]))
        ax.set_ylim(0, float(st["WT"]) / 3)
        ax.grid(True, alpha=0.3)
        self._safe_tight_layout()
        self.draw()

    def _safe_tight_layout(self) -> None:
        if self.width() < 20 or self.height() < 20:
            return
        try:
            self._figure.tight_layout()
        except (ValueError, np.linalg.LinAlgError):
            pass
