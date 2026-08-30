from pathlib import Path

from aid.paths import repo_root


def test_readme_mentions_flow5_and_updates_115():
    readme = (repo_root() / "README.md").read_text()
    updates = (repo_root() / "UPDATES.md").read_text()
    assert "flow5" in readme
    assert "FLOW5/" in readme
    assert updates.startswith("# Updates")
    assert "## 1.15.0" in updates
