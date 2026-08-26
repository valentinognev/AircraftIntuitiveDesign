from pathlib import Path

ROOT = Path("/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign")

def test_readme_and_updates_exist():
    readme = (ROOT / "README.md").read_text()
    updates = (ROOT / "UPDATES.md").read_text()
    assert "Aircraft Intuitive Design" in readme
    assert "UPDATES.md" in readme
    assert updates.startswith("# Updates")
    assert "0.1.0" in updates
