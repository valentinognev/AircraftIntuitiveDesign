import os
import stat
import subprocess
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _write_exe(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _fake_pigeon(tmp_path: Path, aid_gui_src: str | None, qt_plugins: str | None = None) -> Path:
    if qt_plugins is None:
        qt_plugins = str(tmp_path / "Qt" / "plugins")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    src_line = ""
    if aid_gui_src is not None:
        src_line = f'printf "%s\\n" {aid_gui_src!r}\nexit 0\n'
    qt_line = ""
    if qt_plugins is not None:
        qt_line = f'printf "%s\\n" {qt_plugins!r}\nexit 0\n'
    _write_exe(
        bin_dir / "python",
        "#!/bin/sh\n"
        'case "$*" in\n'
        "*aid_gui*)\n"
        f"{src_line}"
        "exit 1\n"
        ";;\n"
        "*PySide6*)\n"
        f"{qt_line}"
        "exit 1\n"
        ";;\n"
        "esac\n"
        'echo "unexpected python: $*" >&2\n'
        "exit 1\n",
    )
    _write_exe(
        bin_dir / "pip",
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> {str(tmp_path / "pip.log")!r}\n',
    )
    log = str(tmp_path / "aid.log")
    _write_exe(
        bin_dir / "aid",
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> {log!r}\n'
        f'printf "%s\\n" "QT_PLUGIN_PATH=${{QT_PLUGIN_PATH-}}" >> {log!r}\n'
        f'printf "%s\\n" "QT_QPA_PLATFORM_PLUGIN_PATH=${{QT_QPA_PLATFORM_PLUGIN_PATH-}}" >> {log!r}\n',
    )
    return tmp_path


def _start_web_sh() -> Path:
    return _root() / "start-web.sh"


def test_start_web_sh_ports():
    text = _start_web_sh().read_text(encoding="utf-8")
    assert "8002" in text
    assert "5175" in text


def test_start_web_sh_puts_aid_src_on_pythonpath():
    text = _start_web_sh().read_text(encoding="utf-8")
    assert "Python/src" in text
    assert text.index("Python/src") < text.index("uvicorn")


def test_start_web_sh_kills_before_starting():
    text = _start_web_sh().read_text(encoding="utf-8")
    body = "\n".join(
        ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")
    )
    kill_at = body.index("kill-web.sh")
    assert kill_at < body.index("start_api")
    assert "already running" not in body


def test_start_sh_still_launches_pyside():
    text = (_root() / "start.sh").read_text(encoding="utf-8")
    assert "exec aid" in text
    assert "8002" not in text


def _run_start(pigeon: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PIGEON_ENV"] = str(pigeon)
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [str(_root() / "start.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_start_sh_reinstalls_when_editable_path_is_stale(tmp_path: Path):
    pigeon = _fake_pigeon(tmp_path, "/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Python/src")
    result = _run_start(pigeon)
    assert result.returncode == 0, result.stderr
    pip_log = (tmp_path / "pip.log").read_text(encoding="utf-8")
    assert "install -e" in pip_log
    assert str(_root() / "Python") in pip_log
    assert (tmp_path / "aid.log").is_file()


def test_start_sh_points_qt_plugins_at_pyside6(tmp_path: Path):
    plugins = tmp_path / "pyside" / "Qt" / "plugins"
    pigeon = _fake_pigeon(
        tmp_path,
        str(_root() / "Python" / "src"),
        qt_plugins=str(plugins),
    )
    result = _run_start(pigeon)
    assert result.returncode == 0, result.stderr
    log = (tmp_path / "aid.log").read_text(encoding="utf-8")
    assert f"QT_PLUGIN_PATH={plugins}" in log
    assert f"QT_QPA_PLATFORM_PLUGIN_PATH={plugins}/platforms" in log


def test_start_sh_skips_install_when_editable_path_matches(tmp_path: Path):
    pigeon = _fake_pigeon(tmp_path, str(_root() / "Python" / "src"))
    result = _run_start(pigeon)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "pip.log").exists()
    assert (tmp_path / "aid.log").is_file()
