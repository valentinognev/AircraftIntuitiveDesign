from __future__ import annotations

from dataclasses import asdict
from subprocess import CalledProcessError, TimeoutExpired

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from aid.aircraft import Aircraft, load_jsonc
from aid.stability import aircraft_stability

from aid_web.analyze import (
    SOLVERS,
    _jsonable,
    analyze as run_analyze,
    control_derivatives as run_control_derivatives,
)
from aid_web.paths import MODELS_DIR, ModelPathError, resolve_model

CORS_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AircraftBody(BaseModel):
    aircraft: dict


class AnalyzeBody(BaseModel):
    aircraft: dict
    solver: str = "datcom"
    mesh: list[str] | None = None


class ControlDerivativesBody(BaseModel):
    aircraft: dict
    solver: str
    deltas_deg: list[float] | None = None
    mesh: list[str] | None = None


def aircraft_to_json(ac: Aircraft) -> dict:
    data = asdict(ac)
    if data.get("cg_data") is None:
        data.pop("cg_data", None)
    return data


def aircraft_from_json(data: dict) -> Aircraft:
    return Aircraft(
        WG=data["WG"],
        HT=data["HT"],
        VT=data["VT"],
        F=data["F"],
        A=data["A"],
        E=data["E"],
        R=data["R"],
        BD=data["BD"],
        NP=data["NP"],
        NB=data["NB"],
        AERO=data["AERO"],
        plot_cmp=data["plot_cmp"],
        unit=data["unit"],
        cg_data=data.get("cg_data"),
    )


def _bad_path() -> JSONResponse:
    return JSONResponse(status_code=400, content={"ok": False, "error": "invalid path"})


def _load_error(exc: BaseException) -> JSONResponse:
    return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})


@app.get("/models")
def list_models() -> dict:
    names = sorted(p.stem for p in MODELS_DIR().glob("*.jsonc"))
    return {"names": names}


@app.get("/models/{name}")
def get_model(name: str):
    try:
        path = resolve_model(name)
    except ModelPathError:
        return _bad_path()
    if not path.is_file():
        return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
    try:
        ac = load_jsonc(path)
    except Exception as exc:
        return _load_error(exc)
    return {"ok": True, "aircraft": aircraft_to_json(ac)}


@app.post("/models/validate")
def validate_model(body: AircraftBody):
    try:
        aircraft_from_json(body.aircraft)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True}


@app.post("/analyze")
def analyze(body: AnalyzeBody):
    solver = body.solver or "datcom"
    if solver not in SOLVERS:
        return JSONResponse(
            status_code=400, content={"ok": False, "error": f"unknown solver: {solver}"}
        )
    try:
        ac = aircraft_from_json(body.aircraft)
        mesh = tuple(str(x) for x in body.mesh) if body.mesh else None
        return run_analyze(ac, solver=solver, mesh=mesh)
    except (
        FileNotFoundError,
        CalledProcessError,
        TimeoutExpired,
        ValueError,
        OSError,
        KeyError,
    ) as exc:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})


@app.post("/control-derivatives")
def control_derivatives(body: ControlDerivativesBody):
    try:
        ac = aircraft_from_json(body.aircraft)
        mesh = tuple(str(x) for x in body.mesh) if body.mesh else None
        return _jsonable(
            run_control_derivatives(
                ac,
                solver=body.solver,
                deltas_deg=body.deltas_deg,
                mesh=mesh,
            )
        )
    except (
        FileNotFoundError,
        CalledProcessError,
        TimeoutExpired,
        ValueError,
        OSError,
        KeyError,
    ) as exc:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})


@app.post("/stability")
def stability(body: AircraftBody):
    try:
        ac = aircraft_from_json(body.aircraft)
        return _jsonable(aircraft_stability(ac))
    except Exception as exc:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
