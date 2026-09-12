import { afterEach, expect, it, vi } from "vitest";
import { aircraftFromJson, aircraftToJson, parseJsonc } from "./aircraft";
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
