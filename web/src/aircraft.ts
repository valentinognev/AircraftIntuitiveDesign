export const AIRCRAFT_KEYS = [
  "WG",
  "HT",
  "VT",
  "F",
  "A",
  "E",
  "R",
  "BD",
  "NP",
  "NB",
  "AERO",
  "plot_cmp",
  "unit",
] as const;

export type AircraftGroup = "WG" | "HT" | "VT" | "F" | "A" | "E" | "R" | "BD" | "AERO";

export type SavedSolverResult = {
  solver: string;
  payload: Record<string, unknown>;
  raw: Record<string, unknown>;
};

export type AircraftDict = {
  WG: Record<string, unknown>;
  HT: Record<string, unknown>;
  VT: Record<string, unknown>;
  F: Record<string, unknown>;
  A: Record<string, unknown>;
  E: Record<string, unknown>;
  R: Record<string, unknown>;
  BD: Record<string, unknown>;
  NP: unknown[];
  NB: unknown[];
  AERO: Record<string, unknown>;
  plot_cmp: unknown[];
  unit: string;
  cg_data?: unknown;
  results?: Record<string, SavedSolverResult>;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value == null || typeof value !== "object" || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

function asDict(value: unknown, key: string): Record<string, unknown> {
  const rec = asRecord(value);
  if (rec == null) throw new Error(`missing ${key}`);
  return { ...rec };
}

function asArray(value: unknown, key: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`missing ${key}`);
  return [...value];
}

function asSolverResults(value: unknown): Record<string, SavedSolverResult> | null {
  const rec = asRecord(value);
  if (rec == null) return null;
  const out: Record<string, SavedSolverResult> = {};
  for (const [name, entry] of Object.entries(rec)) {
    if (name === "__proto__") continue;
    const item = asRecord(entry);
    if (item == null) continue;
    const payload = asRecord(item.payload);
    const raw = asRecord(item.raw);
    if (typeof item.solver !== "string" || payload == null || raw == null) continue;
    out[name] = { solver: item.solver, payload: { ...payload }, raw: { ...raw } };
  }
  return Object.keys(out).length > 0 ? out : null;
}

function padNull(list: unknown[], n: number): unknown[] {
  const out = [...list];
  while (out.length < n) out.push(null);
  return out;
}

function stripLineComment(line: string): string {
  if (!line.includes("//")) return line;
  let inStr = false;
  let out = "";
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"' && (i === 0 || line[i - 1] !== "\\")) {
      inStr = !inStr;
      out += c;
    } else if (!inStr && line.slice(i, i + 2) === "//") {
      break;
    } else {
      out += c;
    }
  }
  return out;
}

export function parseJsonc(text: string): unknown {
  const stripped = text.split(/\r?\n/).map(stripLineComment).join("\n");
  return JSON.parse(stripped) as unknown;
}

export function emptyAircraft(): AircraftDict {
  return {
    WG: {},
    HT: {},
    VT: {},
    F: {},
    A: {},
    E: {},
    R: {},
    BD: {},
    NP: [null, null, null, null],
    NB: [null, null],
    AERO: {},
    plot_cmp: [1, 1, 1, 1],
    unit: "ft",
  };
}

export function aircraftFromJson(raw: unknown): AircraftDict {
  const rec = asRecord(raw);
  if (rec == null) throw new Error("not an aircraft object");
  for (const key of AIRCRAFT_KEYS) {
    if (!(key in rec)) throw new Error(`missing ${key}`);
  }
  const ac: AircraftDict = {
    WG: asDict(rec.WG, "WG"),
    HT: asDict(rec.HT, "HT"),
    VT: asDict(rec.VT, "VT"),
    F: asDict(rec.F, "F"),
    A: asDict(rec.A, "A"),
    E: asDict(rec.E, "E"),
    R: asDict(rec.R, "R"),
    BD: asDict(rec.BD, "BD"),
    NP: padNull(asArray(rec.NP, "NP"), 4),
    NB: padNull(asArray(rec.NB, "NB"), 2),
    AERO: asDict(rec.AERO, "AERO"),
    plot_cmp: asArray(rec.plot_cmp, "plot_cmp"),
    unit: typeof rec.unit === "string" ? rec.unit : String(rec.unit),
  };
  if ("cg_data" in rec) ac.cg_data = rec.cg_data;
  const results = asSolverResults(rec.results);
  if (results != null) ac.results = results;
  return ac;
}

export function aircraftToJson(ac: AircraftDict): AircraftDict {
  const out: AircraftDict = {
    WG: { ...ac.WG },
    HT: { ...ac.HT },
    VT: { ...ac.VT },
    F: { ...ac.F },
    A: { ...ac.A },
    E: { ...ac.E },
    R: { ...ac.R },
    BD: { ...ac.BD },
    NP: [...ac.NP],
    NB: [...ac.NB],
    AERO: { ...ac.AERO },
    plot_cmp: [...ac.plot_cmp],
    unit: ac.unit,
  };
  if ("cg_data" in ac) out.cg_data = ac.cg_data;
  if (ac.results != null && Object.keys(ac.results).length > 0) out.results = { ...ac.results };
  return out;
}

export function patchGroup(
  ac: AircraftDict,
  group: AircraftGroup,
  key: string,
  value: unknown,
): AircraftDict {
  return { ...ac, [group]: { ...ac[group], [key]: value } };
}

export function patchArrayItem(
  ac: AircraftDict,
  group: "BD" | "AERO" | AircraftGroup,
  key: string,
  index: number,
  value: unknown,
): AircraftDict {
  const current = ac[group][key];
  const list = Array.isArray(current) ? [...current] : [];
  while (list.length <= index) list.push(null);
  list[index] = value;
  return { ...ac, [group]: { ...ac[group], [key]: list } };
}

/**
 * The sideslip angle in degrees, 0 when unset. A saved aircraft may carry no BETA
 * key at all, since the writer omits AERO keys that equal their default.
 */
export function aeroBeta(ac: AircraftDict): number {
  const raw = ac.AERO?.BETA;
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : 0;
  if (Array.isArray(raw) && typeof raw[0] === "number") {
    return Number.isFinite(raw[0]) ? (raw[0] as number) : 0;
  }
  return 0;
}
