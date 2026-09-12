from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _start_web_sh() -> Path:
    return _root() / "start-web.sh"


def test_start_web_sh_ports():
    text = _start_web_sh().read_text(encoding="utf-8")
    assert "8002" in text
    assert "5175" in text


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
