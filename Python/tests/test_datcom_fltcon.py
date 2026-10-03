import re

import pytest

from aid.aircraft import load_jsonc
from aid.alpha_schedule import apply_alpha_default
from aid.datcom_io import write_fltcon
from aid.paths import models_dir


def test_fltcon_cessna_mach_alpha():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_fltcon(ac, lines)
    text = "\n".join(lines)
    assert "$FLTCON" in text
    assert "MACH=0.030" in text or "MACH=0.03" in text
    assert "-4.0" in text and "12.0" in text


def _written_alphas(ac) -> list[float]:
    """``ALSCHD`` as DATCOM's ``%.1f`` cards actually carry it, read back."""
    lines: list = []
    write_fltcon(ac, lines)
    block = re.search(r"ALSCHD=(.*?)NALT=", "\n".join(lines), re.DOTALL).group(1)
    return [float(tok) for tok in block.replace("\n", " ").split(",") if tok.strip()]


def _sparse(alschd):
    """Cessna geometry carrying a deliberately sparse *alschd*."""
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ac.AERO["ALSCHD"] = alschd
    return ac


# Spans whose nearest-count rung was 0.25 before the ladder was restricted:
# DATCOM's %.1f cards cannot carry a grid finer than 0.1, so cla/cma --
# finite differences along the written grid -- would be differenced over a
# spacing the deck does not contain.
WRITABLE_SPANS = [[-2.0, 0.0, 2.0], [-4.0, 0.0, 4.0]]


@pytest.mark.parametrize("alschd", WRITABLE_SPANS, ids=["span4", "span8"])
def test_expanded_schedule_survives_the_datcom_cards(alschd):
    ac = _sparse(alschd)
    apply_alpha_default(ac)
    written = _written_alphas(ac)
    assert written == [float(a) for a in ac.AERO["ALSCHD"]]


def test_span_the_cards_cannot_carry_is_left_stored():
    """An endpoint off the 0.1 grid gets no schedule at all, not a lossy one."""
    ac = _sparse([-0.35, 0.35])
    apply_alpha_default(ac)
    assert ac.AERO["ALSCHD"] == [-0.35, 0.35]


def test_every_shipped_schedule_survives_the_datcom_cards():
    for path in sorted(models_dir().glob("*.jsonc")):
        ac = load_jsonc(path)
        apply_alpha_default(ac)
        written = _written_alphas(ac)
        assert written == [float(a) for a in ac.AERO["ALSCHD"]], path.name