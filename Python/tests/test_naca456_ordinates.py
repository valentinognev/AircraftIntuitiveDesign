import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest

from aid.naca456 import NacaSpec, ordinates

BINARY = Path("/home/valentin/Projects/FlightSimulation/USAF_DATCOM/naca456/naca456")


def _fortran_env() -> dict:
    env = os.environ.copy()
    for lib in (
        Path("/home/valentin/anaconda/envs/pigeon/lib"),
        Path("/home/valentin/anaconda/pkgs/libgfortran-3.0.0-1/lib"),
    ):
        if (lib / "libgfortran.so.3").is_file():
            prev = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = str(lib) + ((":" + prev) if prev else "")
            break
    return env


def _gnu(spec: NacaSpec) -> np.ndarray:
    namelist = (
        "&NACA\n"
        f"NAME='{spec.name}',\n"
        f"PROFILE='{spec.profile}',\n"
        f"CAMBER='{spec.camber}',\n"
        f"TOC={spec.toc:.4f},\n"
        f"CL={spec.cl:.4f},\n"
        f"A={spec.a:.4f},\n"
        f"CMAX={spec.cmax:.4f},\n"
        f"XMAXC={spec.xmaxc:.4f},\n"
        f"CHORD={spec.chord:.4f},\n"
        f"DENCODE={spec.dencode},\n"
        "/\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "naca.in"
        path.write_text(namelist)
        subprocess.run(
            [str(BINARY), str(path)],
            cwd=tmp,
            check=True,
            capture_output=True,
            env=_fortran_env(),
        )
        # This binary writes <input-path>.gnu (Welcome appends '.gnu'), not naca.gnu.
        return np.loadtxt(path.with_name(path.name + ".gnu"))


@pytest.mark.skipif(not BINARY.is_file() or not os.access(BINARY, os.X_OK), reason="naca456 binary missing")
@pytest.mark.parametrize("spec", [
    NacaSpec(name="NACA 2412", profile="4", camber="2", toc=0.12, cmax=0.02, xmaxc=0.4),
    # Binary rejects PROFILE='6' ("Not a valid profile"). NACA 64-210 is profile '64'.
    NacaSpec(name="NACA 64-210", profile="64", camber="6", toc=0.10, cl=0.2, a=0.4),
])
def test_ordinates_match_fortran_gnu(spec):
    got = ordinates(spec)
    ref = _gnu(spec)
    assert got.shape == ref.shape
    assert np.allclose(got, ref, atol=1e-4)
