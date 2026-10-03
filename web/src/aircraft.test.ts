import { afterEach, expect, it, vi } from "vitest";
import {
  aeroBeta,
  aircraftFromJson,
  aircraftToJson,
  emptyAircraft,
  parseJsonc,
} from "./aircraft";
import { commitString } from "./Field";
import {
  AERO_FIELDS,
  AERO_NACA_FIELDS,
  BODY_STATION_ROWS,
  CONTROL_BLOCKS,
  PLANFORM_RP,
} from "./fields";
import { rememberRecent } from "./recent";
import { createStore } from "./store";
import { THEME_STORAGE_KEY } from "./theme";

afterEach(() => {
  vi.unstubAllGlobals();
});

/** Cessna 172 JSONC subset — keys match `aid.aircraft` / models/Cessna 172.jsonc. */
const CESSNA_SUBSET_JSONC = `{
    "WG": { // wing planform
        "CHRDR": 2 // Root Chord, ft
    },
    "HT": { "CHRDR": 1.3 },
    "VT": { "CHRDR": 5 },
    "F": { "SPANFI": 0.83333 },
    "A": { "SPANFI": 2.5 },
    "E": { "SPANFI": 0.83333 },
    "R": { "SPANFI": 0.1 },
    "BD": { "NX": 16 },
    "NP": [null, null, null, null],
    "NB": [null, null],
    "AERO": { "MACH": 0.03 },
    "plot_cmp": [1, 1, 1, 1],
    "unit": "ft"
}`;

it("aircraftFromJson round-trips Cessna WG.CHRDR", () => {
  const ac = aircraftFromJson(parseJsonc(CESSNA_SUBSET_JSONC));
  expect(ac.WG.CHRDR).toBe(2);
  expect(aircraftToJson(ac).WG.CHRDR).toBe(2);
});

it("a valid results block survives aircraftFromJson to aircraftToJson", () => {
  const results = { datcom: solverResult("datcom"), tornado: solverResult("tornado") };
  const out = aircraftToJson(aircraftFromJson(withResults(results)));
  expect(out.results).toEqual(results);
});

it("absent results in gives absent results out", () => {
  const ac = aircraftFromJson(baseAircraftJson());
  expect("results" in ac).toBe(false);
  expect("results" in aircraftToJson(ac)).toBe(false);
  expect("results" in emptyAircraft()).toBe(false);
});

it("empty results block is omitted", () => {
  const ac = aircraftFromJson(withResults({}));
  expect("results" in ac).toBe(false);
  expect("results" in aircraftToJson(ac)).toBe(false);
});

it("non-object results block is omitted without throwing", () => {
  for (const bad of [null, "x", [], 7]) {
    const ac = aircraftFromJson(withResults(bad));
    expect("results" in ac).toBe(false);
    expect("results" in aircraftToJson(ac)).toBe(false);
  }
});

it("an entry missing payload is dropped and siblings survive", () => {
  const datcom = solverResult("datcom");
  const flow5 = solverResult("flow5");
  const ac = aircraftFromJson(
    withResults({ datcom, avl: { solver: "avl", raw: { notes: "no payload" } }, flow5 }),
  );
  expect(ac.results).toEqual({ datcom, flow5 });
  expect(aircraftToJson(ac).results).toEqual({ datcom, flow5 });
});

it("an entry whose payload is an array is dropped", () => {
  const ac = aircraftFromJson(
    withResults({ tornado: { solver: "tornado", payload: [1, 2, 3], raw: { ok: true } } }),
  );
  expect("results" in aircraftToJson(ac)).toBe(false);
});

it("an entry missing solver or with a non-object raw is dropped", () => {
  const datcom = solverResult("datcom");
  const ac = aircraftFromJson(
    withResults({
      datcom,
      avl: { payload: { ref: {} }, raw: { ok: true } },
      flow5: { solver: "flow5", payload: { ref: {} }, raw: "not an object" },
    }),
  );
  expect(ac.results).toEqual({ datcom });
});

it("a __proto__ key in the results block is skipped, not adopted as the prototype", () => {
  const hostile = JSON.parse(
    `{"__proto__": ${JSON.stringify(solverResult("evil"))}, "datcom": ${JSON.stringify(solverResult("datcom"))}}`,
  ) as Record<string, unknown>;
  expect(Object.getOwnPropertyNames(hostile)).toContain("__proto__");
  const results = aircraftFromJson(withResults(hostile)).results;
  expect(results?.datcom?.solver).toBe("datcom");
  expect(Object.getPrototypeOf(results)).toBe(Object.prototype);
  expect("payload" in (results as Record<string, unknown>)).toBe(false);
  expect(Object.keys(aircraftToJson(aircraftFromJson(withResults(hostile))).results ?? {})).toEqual(["datcom"]);
});

it("PLANFORM_RP copies PySide label/key pairs", () => {
  expect(PLANFORM_RP).toEqual([
    ["CHRDR", "Root Chord", "len"],
    ["CHRDBP", "Break Chord", "len"],
    ["CHRDTP", "Tip Chord", "len"],
    ["SSPN", "Semi-Span", "len"],
    ["SSPNOP", "Break Span", "len"],
    ["SAVSI", "Inboard Sweep", "deg"],
    ["SAVSO", "Outboard Sweep", "deg"],
    ["CHSTAT", "Sweep Reference", "le_te"],
    ["DHDADI", "Inboard Dihedral", "deg"],
    ["DHDADO", "Outboard Dihedral", "deg"],
    ["TC", "Thickness", "chord"],
    ["TWISTA", "Washout", "deg"],
    ["i", "Incidence", "deg"],
    ["X", "Position, X", "len"],
    ["Y", "Position, Y", "len"],
    ["Z", "Position, Z", "len"],
  ]);
});

it("AERO and Control/Body keys copy PySide lists", () => {
  expect(AERO_FIELDS[0]).toEqual(["ALSCHD", "Angle(s) of Attack", "deg"]);
  expect(AERO_NACA_FIELDS[0]).toEqual(["WG.NACA[0]", "Wing Root Airfoil", 0]);
  expect(CONTROL_BLOCKS[0][0]).toBe("F");
  expect(CONTROL_BLOCKS[0][3][0]).toEqual(["SPANFI", "SPANFO", "Span", "len"]);
  expect(BODY_STATION_ROWS).toBe(11);
});

it("theme storage key is aid-theme", () => {
  expect(THEME_STORAGE_KEY).toBe("aid-theme");
});

it("NACA 0012 survives commit as string", () => {
  expect(commitString("0012")).toBe("0012");
  expect(commitString("")).toBe(null);
  expect(commitString("   ")).toBe(null);
});

it("openRecent does not GET /models for local-only names", async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    json: async () => ({ summary: [] }),
  }));
  vi.stubGlobal("fetch", fetchMock);
  const store = createStore();
  store.getState().setModels(["Cessna 172"]);
  store.getState().openJsoncText(CESSNA_SUBSET_JSONC, "mine.jsonc");
  await store.getState().openRecent("mine.jsonc");
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/models"))).toBe(false);
});

it("applyValidateResult is not a parse error and clears on ok", () => {
  const store = createStore();
  store.getState().applyValidateResult({ ok: false, error: "bad aircraft" });
  expect(store.getState().parseError).toBeNull();
  expect(store.getState().validateError).toEqual({ message: "bad aircraft" });
  store.getState().applyValidateResult({ ok: true });
  expect(store.getState().validateError).toBeNull();
  expect(store.getState().parseError).toBeNull();
});

it("rememberRecent keeps last 5 JSONC names", () => {
  const storage = memoryStorage();
  rememberRecent("a.jsonc", storage);
  rememberRecent("b.jsonc", storage);
  rememberRecent("c.jsonc", storage);
  rememberRecent("d.jsonc", storage);
  rememberRecent("e.jsonc", storage);
  rememberRecent("f.jsonc", storage);
  expect(JSON.parse(storage.getItem("aid-recent") ?? "[]")).toEqual([
    "f.jsonc",
    "e.jsonc",
    "d.jsonc",
    "c.jsonc",
    "b.jsonc",
  ]);
});

function baseAircraftJson(): Record<string, unknown> {
  return {
    WG: { CHRDR: 2 },
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

function withResults(value: unknown): Record<string, unknown> {
  return { ...baseAircraftJson(), results: value };
}

function solverResult(solver: string): Record<string, unknown> {
  return {
    solver,
    payload: { source: "api", solver, axes: { alpha: [0, 5] }, tables: { CL: [0.4, 0.5] }, ref: { mac: 1.3 } },
    raw: { solver, lattice: { nodes: [[0, 0, 0], [1, 1, 1]], fields: ["cp"] }, note: "verbatim" },
  };
}

function memoryStorage(): Storage {
  const map = new Map<string, string>();
  return {
    get length() {
      return map.size;
    },
    clear() {
      map.clear();
    },
    getItem(key: string) {
      return map.has(key) ? map.get(key)! : null;
    },
    key(index: number) {
      return [...map.keys()][index] ?? null;
    },
    removeItem(key: string) {
      map.delete(key);
    },
    setItem(key: string, value: string) {
      map.set(key, value);
    },
  };
}

it("aeroBeta reads AERO.BETA in degrees and falls back to zero", () => {
  expect(aeroBeta({ ...emptyAircraft(), AERO: { BETA: 5 } })).toBe(5);
  expect(aeroBeta({ ...emptyAircraft(), AERO: { BETA: [5] } })).toBe(5);
  expect(aeroBeta(emptyAircraft())).toBe(0);
  expect(aeroBeta({ ...emptyAircraft(), AERO: { BETA: null } })).toBe(0);
  expect(aeroBeta({ ...emptyAircraft(), AERO: { BETA: "nonsense" } })).toBe(0);
});

it("the Aero tab carries a Beta row next to angle of attack", () => {
  const names = AERO_FIELDS.map(([field]) => field);
  expect(names.indexOf("BETA")).toBe(names.indexOf("ALSCHD") + 1);
  expect(AERO_FIELDS[names.indexOf("BETA")]).toEqual(["BETA", "Beta (deg)", "deg"]);
});
