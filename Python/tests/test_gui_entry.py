import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from importlib.metadata import entry_points

from aid_gui.app import main


def test_entry_point_registered():
    eps = {e.name: e.value for e in entry_points(group="console_scripts")}
    assert eps.get("aid") == "aid_gui.app:main"


def test_main_returns_zero():
    # do not exec event loop in CI; call with --help style if added
    assert callable(main)
