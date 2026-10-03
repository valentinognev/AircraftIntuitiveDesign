import shutil

import pytest
from PySide6.QtCore import QSettings

from aid.paths import results_dir


@pytest.fixture(autouse=True)
def isolate_recent_settings(tmp_path, monkeypatch):
    ini = str(tmp_path / "aid_recent.ini")
    monkeypatch.setattr(
        "aid_gui.recent.default_settings",
        lambda: QSettings(ini, QSettings.Format.IniFormat),
    )


@pytest.fixture
def isolated_results(tmp_path, monkeypatch):
    """A ``Results/`` root carrying a copy of the MATLAB gold.

    ``compare_to_matlab`` writes ``Results/compare/<name>.json`` unconditionally,
    so every test that calls it must be pointed at a copy: otherwise it leaves the
    real gold-parity artifact holding whatever the test stubbed, and whichever
    test collected last decides whether it passes.
    """
    root = tmp_path / "Results"
    gold = results_dir() / "matlab"
    if gold.is_dir():
        shutil.copytree(gold, root / "matlab")
    monkeypatch.setattr("aid.compare.results_dir", lambda: root)
    return root
