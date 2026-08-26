# Python/tests/test_jsonc_loads.py
from aid.jsonc import loads_jsonc

SAMPLE = """{
  "WG": {
    "CHRDR": 2.0, // Root Chord ft
    "SSPN": 6.0 // Semi-Span ft
  },
  "unit": "ft" // length unit
}"""

def test_loads_jsonc_strips_comments():
    d = loads_jsonc(SAMPLE)
    assert d["WG"]["CHRDR"] == 2.0
    assert d["unit"] == "ft"
