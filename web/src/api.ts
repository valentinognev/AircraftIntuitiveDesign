import { aircraftToJson, type AircraftDict, type SavedSolverResult } from "./aircraft";
import { cadacCallbackUrl } from "./cadacSession";
import type { HandshakePayload } from "./payload";

export type ValidateResult = { ok: true } | { ok: false; error: string };

export function aircraftForRequest(aircraft: AircraftDict): AircraftDict {
  const geometry = aircraftToJson(aircraft);
  delete geometry.results;
  return geometry;
}

export async function fetchModels(): Promise<string[]> {
  const res = await fetch("/models");
  if (!res.ok) throw new Error(`models ${res.status}`);
  const body = (await res.json()) as { names?: unknown };
  if (!Array.isArray(body.names)) return [];
  return body.names.filter((n): n is string => typeof n === "string");
}

export async function fetchModel(name: string): Promise<unknown> {
  const res = await fetch(`/models/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`model ${res.status}`);
  const body = (await res.json()) as { ok?: boolean; aircraft?: unknown; error?: unknown };
  if (body.ok !== true) throw new Error(String(body.error ?? "load failed"));
  return body.aircraft;
}

export async function validateAircraft(aircraft: AircraftDict): Promise<ValidateResult> {
  try {
    const res = await fetch("/models/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aircraft: aircraftForRequest(aircraft) }),
    });
    const data = (await res.json()) as { ok?: boolean; error?: unknown };
    if (data.ok === true) return { ok: true };
    return { ok: false, error: String(data.error ?? "invalid aircraft") };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export type AnalyzeOk = {
  ok: true;
  solver: string;
  raw: unknown;
  payload: HandshakePayload;
  handbook: unknown | null;
  handshakeError: string | null;
};

export type AnalyzeFail = { ok: false; error: string };

export type AnalyzeResult = AnalyzeOk | AnalyzeFail;

function objectHandbook(value: unknown): unknown | null {
  if (value != null && typeof value === "object" && !Array.isArray(value)) return value;
  return null;
}

export async function postAnalyze(
  aircraft: AircraftDict,
  solver: string,
): Promise<AnalyzeResult> {
  let data: {
    ok?: boolean;
    error?: unknown;
    solver?: unknown;
    raw?: unknown;
    payload?: unknown;
    handbook?: unknown;
  };
  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aircraft: aircraftForRequest(aircraft), solver }),
    });
    data = (await res.json()) as typeof data;
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
  if (data.ok === true && data.payload != null && typeof data.payload === "object") {
    const payload = data.payload as HandshakePayload;
    const callback = cadacCallbackUrl();
    let handshakeError: string | null = null;
    if (callback) {
      try {
        const complete = await fetch(callback, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(payload),
        });
        if (!complete.ok) {
          handshakeError = `CADAC complete HTTP ${complete.status}`;
        }
      } catch (err) {
        handshakeError = err instanceof Error ? err.message : String(err);
      }
    }
    return {
      ok: true,
      solver: typeof data.solver === "string" ? data.solver : solver,
      raw: data.raw,
      payload,
      handbook: objectHandbook(data.handbook),
      handshakeError,
    };
  }
  return { ok: false, error: String(data.error ?? "analyze failed") };
}

export async function fetchStability(
  aircraft: AircraftDict,
): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch("/stability", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aircraft: aircraftForRequest(aircraft) }),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as Record<string, unknown>;
    return data;
  } catch {
    return null;
  }
}

export function downloadAircraft(
  aircraft: AircraftDict,
  stem: string,
  results?: Record<string, SavedSolverResult>,
): void {
  const name = stem.toLowerCase().endsWith(".jsonc") || stem.toLowerCase().endsWith(".json")
    ? stem
    : `${stem || "aircraft"}.jsonc`;
  const geometry = aircraftForRequest(aircraft);
  const saved: AircraftDict =
    results != null && Object.keys(results).length > 0 ? { ...geometry, results } : geometry;
  const blob = new Blob([JSON.stringify(saved, null, 4)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export type AircraftSaveSource = {
  aircraft: AircraftDict | null;
  stem: string | null;
  resultsForSave: () => Record<string, SavedSolverResult> | undefined;
};

export function saveAircraftFromStore(source: AircraftSaveSource): void {
  const { aircraft } = source;
  if (aircraft == null) return;
  downloadAircraft(aircraft, source.stem ?? "aircraft", source.resultsForSave());
}
