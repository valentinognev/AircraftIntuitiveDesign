import json
from dataclasses import fields, replace

import pytest

from aid import field_docs, jsonc
from aid.aircraft import Aircraft, load_jsonc, load_mat, save_jsonc
from aid.jsonc import loads_jsonc
from aid.paths import matlab_code, models_dir

CESSNA = models_dir() / "Cessna 172.jsonc"
CESSNA_MAT = matlab_code() / "Models" / "Cessna 172.mat"
RESULTS_DOC = "Analysis results, keyed by solver"

RESULTS = {
    "avl": {
        "solver": "avl",
        "payload": {
            "source": "avl",
            "solver": "avl",
            "axes": {"alpha": [0.0, 5.0, 10.0], "beta": [0.0, 1.0]},
            "ref": {"S": 174.0, "b": 36.5, "cbar": 2.0},
            "tables": {"CL": [0.31, 0.77, 1.19], "CD": [0.0121, 0.0204, 0.0398]},
        },
        "raw": {
            "solution": {
                "alpha": 0.0,
                "coefs": {"CL": 0.3112, "CDi": 0.0118, "Cm": -0.0483},
                "controls": [
                    {"name": "Elevator", "value": -0.4, "limited": False},
                    {"name": "Rudder", "value": 0.0, "limited": False},
                ],
                "flags": {"trimmed": True, "converged": True},
                "notes": [],
            },
            "versions": {"avl": "6.3", "eispack": "none", "user": None},
        },
    },
    "tornado": {
        "solver": "tornado",
        "payload": {"source": "tornado", "solver": "tornado", "axes": {"alpha": [0.0, 10.0]}},
        "raw": {"lattice": {"nodes": 41, "panels": 320, "sections": [0.0, 0.25, 0.5, 1.0]}},
    },
}

SLASH_RESULTS = {
    "avl": {
        "solver": "avl",
        "payload": {"source": "avl", "note": "see http://example.invalid/avl // trailing"},
        "raw": {
            "path": "results//avl",
            "quoted": "\" // still a string",
            "backslash": "a\\//b",
        },
    }
}


def fixture_with_results(tmp_path, results, name="with_results.jsonc"):
    text = CESSNA.read_text()
    assert text.startswith("{\n")
    body = text[1:].lstrip("\n")
    block = json.dumps(results, indent=2)
    path = tmp_path / name
    path.write_text('{\n  "results": ' + block + ",\n" + body)
    return path


def test_results_survive_save_and_reload(tmp_path):
    ac = load_jsonc(fixture_with_results(tmp_path, RESULTS))
    assert ac.results == RESULTS

    out = tmp_path / "saved.jsonc"
    save_jsonc(ac, out)
    reloaded = load_jsonc(out)

    assert reloaded.results == RESULTS
    assert reloaded.results["avl"]["raw"]["solution"]["controls"][0] == {
        "name": "Elevator",
        "value": -0.4,
        "limited": False,
    }
    base = load_jsonc(CESSNA)
    assert reloaded.WG == base.WG
    assert reloaded.AERO == base.AERO
    assert reloaded.plot_cmp == base.plot_cmp
    assert reloaded.unit == base.unit


def test_geometry_only_save_is_byte_identical(tmp_path):
    ac = load_jsonc(CESSNA)
    assert ac.results is None

    out = tmp_path / "cessna.jsonc"
    save_jsonc(ac, out)
    text = out.read_text()

    assert text == CESSNA.read_text()
    assert '"results"' not in text


@pytest.mark.parametrize("empty", [None, {}])
def test_empty_results_are_omitted(tmp_path, empty):
    ac = load_jsonc(CESSNA)
    plain = tmp_path / "plain.jsonc"
    save_jsonc(ac, plain)

    ac.results = empty
    with_empty = tmp_path / "with_empty.jsonc"
    save_jsonc(ac, with_empty)

    assert with_empty.read_text() == plain.read_text()
    assert '"results"' not in with_empty.read_text()


def test_results_keys_with_slashes_reload_intact(tmp_path):
    ac = load_jsonc(fixture_with_results(tmp_path, SLASH_RESULTS, name="slashes.jsonc"))
    assert ac.results == SLASH_RESULTS

    out = tmp_path / "slashes_saved.jsonc"
    save_jsonc(ac, out)
    assert load_jsonc(out).results == SLASH_RESULTS


@pytest.mark.parametrize("raw", ["null", "[]", '"x"', "{}", "0"])
def test_malformed_results_load_as_none(tmp_path, raw):
    path = tmp_path / "malformed.jsonc"
    path.write_text('{\n  "results": ' + raw + ",\n" + CESSNA.read_text()[1:].lstrip("\n"))

    ac = load_jsonc(path)

    assert ac.results is None
    assert ac.unit == "ft"
    out = tmp_path / "malformed_saved.jsonc"
    save_jsonc(ac, out)
    assert '"results"' not in out.read_text()


def test_results_block_is_emitted_opaquely(tmp_path):
    ac = load_jsonc(fixture_with_results(tmp_path, RESULTS))
    out = tmp_path / "opaque.jsonc"
    save_jsonc(ac, out)
    text = out.read_text()

    assert f'"results": {{ // {RESULTS_DOC}' in text
    assert text.count(RESULTS_DOC) == 1
    after = text.split(RESULTS_DOC, 1)[1]
    assert "//" not in after
    assert list(loads_jsonc(text)["results"]) == list(RESULTS)


def test_results_emit_never_consults_docs(tmp_path, monkeypatch):
    ac = load_jsonc(fixture_with_results(tmp_path, RESULTS))
    original = jsonc._lookup_doc

    def guarded(path_parts, docs):
        assert path_parts[0] != "results", path_parts
        return original(path_parts, docs)

    monkeypatch.setattr(jsonc, "_lookup_doc", guarded)
    out = tmp_path / "guarded.jsonc"
    save_jsonc(ac, out)

    assert load_jsonc(out).results == RESULTS


def test_field_docs_has_no_results_entry():
    assert "results" not in field_docs.DOCS
    assert [key for key in field_docs.DOCS if key.split(".")[0] == "results"] == []


def test_results_is_the_last_optional_dataclass_field():
    assert [f.name for f in fields(Aircraft)][-1] == "results"
    assert Aircraft.__dataclass_fields__["results"].default is None


def test_results_key_is_emitted_after_unit(tmp_path):
    ac = load_jsonc(fixture_with_results(tmp_path, RESULTS))
    out = tmp_path / "order.jsonc"
    save_jsonc(ac, out)
    text = out.read_text()
    assert text.index('"results":') > text.index('"unit":')


def test_load_mat_has_no_results():
    assert load_mat(CESSNA_MAT).results is None


def test_replace_keeps_results(tmp_path):
    ac = load_jsonc(fixture_with_results(tmp_path, RESULTS))
    assert replace(ac, unit="in").results == RESULTS
    assert replace(ac, unit="in").unit == "in"