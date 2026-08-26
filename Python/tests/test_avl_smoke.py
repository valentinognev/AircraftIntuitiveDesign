import subprocess

from aid.paths import avl_bin


def test_avl_quits_with_plop_g():
    r = subprocess.run(
        [str(avl_bin())],
        input="PLOP\ng\n\nQuit\n",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0
