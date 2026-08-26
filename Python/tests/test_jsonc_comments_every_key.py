# Python/tests/test_jsonc_comments_every_key.py
from pathlib import Path
from aid.aircraft import load_mat, save_jsonc
from aid.paths import matlab_code

def test_every_key_line_has_comment(tmp_path):
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    out = tmp_path / "c.jsonc"
    save_jsonc(ac, out)
    text = out.read_text()
    for line in text.splitlines():
        s = line.strip()
        if not s or s in "{[]}," or s.startswith("//"):
            continue
        if ":" in s:
            assert "//" in s, line
