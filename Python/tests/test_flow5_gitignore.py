from pathlib import Path
from aid.paths import repo_root


def test_gitignore_flow5_build_and_binary():
    text = (repo_root() / ".gitignore").read_text()
    assert "FLOW5/build/" in text
    assert "FLOW5/run/flow5_run" in text
