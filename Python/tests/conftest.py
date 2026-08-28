import pytest
from PySide6.QtCore import QSettings


@pytest.fixture(autouse=True)
def isolate_recent_settings(tmp_path, monkeypatch):
    ini = str(tmp_path / "aid_recent.ini")
    monkeypatch.setattr(
        "aid_gui.recent.default_settings",
        lambda: QSettings(ini, QSettings.Format.IniFormat),
    )
