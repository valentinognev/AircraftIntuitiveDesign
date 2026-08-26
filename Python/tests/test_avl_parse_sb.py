from aid.avl_parse import parse_sb
from aid.paths import results_dir


def test_parse_sb_does_not_crash_on_gold():
    sb = results_dir() / "matlab" / "Cessna 172" / "geometry.sb"
    if sb.is_file():
        d = parse_sb(sb)
        assert isinstance(d, dict)
    else:
        import pytest

        pytest.skip("geometry.sb not in gold yet")
