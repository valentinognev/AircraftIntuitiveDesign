from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class ResultsPanel(FigureCanvasQTAgg):
    def __init__(self) -> None:
        self._figure = Figure(figsize=(4, 3))
        super().__init__(self._figure)
        self._ax = self._figure.add_subplot(111)
        self._ax.set_xlabel("alpha (deg)")
        self._ax.set_ylabel("CL")

    def plot_datcom(self, coeffs: dict) -> None:
        self._ax.clear()
        self._ax.plot(coeffs["alpha"], coeffs["cl"], "o-", color="C0")
        self._ax.set_xlabel("alpha (deg)")
        self._ax.set_ylabel("CL")
        self._ax.grid(True, alpha=0.3)
        self.draw()
