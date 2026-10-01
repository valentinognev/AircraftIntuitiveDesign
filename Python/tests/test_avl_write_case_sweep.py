from pathlib import Path

from aid.avl_io import write_case


def test_write_case_commands_each_alpha(tmp_path: Path):
    write_case("geometry", {"AS": 100.0}, tmp_path, [-4.0, 0.0, 8.0])
    text = (tmp_path / "geometry.run").read_text()
    assert "a a -4.0000" in text
    assert "a a 0.0000" in text
    assert "a a 8.0000" in text
    assert text.count("\nx\n") == 3
    assert "geometry_0.st" in text
    assert "geometry_1.st" in text
    assert "geometry_2.st" in text
    # sb once, on the zero-angle case, before the next alpha command
    zero = text.index("a a 0.0000")
    sb = text.index("geometry.sb")
    eight = text.index("a a 8.0000")
    assert zero < sb < eight
    assert text.count("geometry.sb") == 1


def test_write_case_sb_on_first_when_zero_absent(tmp_path: Path):
    write_case("geometry", {"AS": 50.0}, tmp_path, [2.0, 4.0])
    text = (tmp_path / "geometry.run").read_text()
    assert text.index("geometry.sb") < text.index("a a 4.0000")
    assert text.count("geometry.sb") == 1


def test_write_case_rejects_empty_alphas(tmp_path: Path):
    try:
        write_case("geometry", {"AS": 1.0}, tmp_path, [])
    except ValueError as exc:
        assert "ALSCHD" in str(exc)
    else:
        raise AssertionError("expected ValueError")
