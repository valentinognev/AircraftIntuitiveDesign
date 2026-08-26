from aid.aircraft import load_jsonc
from aid.datcom_io import write_controls
from aid.paths import models_dir


def test_controls_section_present_or_empty():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_controls(ac, lines)
    text = "\n".join(lines)
    # Cessna may have zero deflection; writer must not crash
    assert "PLOT" not in text  # controls only task
