import { afterEach, expect, it, vi } from "vitest";
import { emptyAircraft, type AircraftDict, type SavedSolverResult } from "./aircraft";
import { downloadAircraft, fetchStability, postAnalyze, validateAircraft } from "./api";
import * as api from "./api";
import { createStore } from "./store";

type CapturedBlob = { text: string; options: unknown };

type CapturedBrowser = {
  blobs: CapturedBlob[];
  urls: string[];
  revoked: string[];
  names: string[];
  hrefs: string[];
};

function stubBrowser(): CapturedBrowser {
  const captured: CapturedBrowser = { blobs: [], urls: [], revoked: [], names: [], hrefs: [] };
  class CapturedBlob {
    readonly type: string;
    readonly body: string;
    constructor(parts: unknown[], options?: { type?: string }) {
      this.body = parts.map((part) => String(part)).join("");
      this.type = options?.type ?? "";
      captured.blobs.push({ text: this.body, options });
    }
  }
  const anchor = {
    href: "",
    download: "",
    click: () => {
      captured.names.push(anchor.download);
      captured.hrefs.push(anchor.href);
    },
  };
  vi.stubGlobal("Blob", CapturedBlob);
  vi.stubGlobal("URL", {
    createObjectURL: (blob: { body: string }) => {
      captured.urls.push(blob.body);
      return `blob:${captured.urls.length}`;
    },
    revokeObjectURL: (url: string) => void captured.revoked.push(url),
  });
  vi.stubGlobal("document", { createElement: () => anchor });
  return captured;
}

function stubFetch(): { bodies: string[] } {
  vi.stubGlobal("location", { search: "" });
  const bodies: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      bodies.push(String(init?.body ?? ""));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          solver: "datcom",
          raw: solverResult("datcom").raw,
          payload: solverResult("datcom").payload,
        }),
      };
    }),
  );
  return { bodies };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it("downloadAircraft writes the results block it is handed", () => {
  const captured = stubBrowser();
  const results = { datcom: solverResult("datcom"), tornado: solverResult("tornado") };
  downloadAircraft(emptyAircraft(), "Cessna172", results);
  const written = JSON.parse(captured.blobs[0].text) as Record<string, unknown>;
  expect(written.results).toEqual(results);
});

it("the results block lands after unit in the saved file", () => {
  const captured = stubBrowser();
  downloadAircraft(emptyAircraft(), "Cessna172", { datcom: solverResult("datcom") });
  expect(Object.keys(JSON.parse(captured.blobs[0].text) as Record<string, unknown>)).toEqual([
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
    "results",
  ]);
});

it("downloadAircraft with no results argument serializes exactly today's bytes", () => {
  const captured = stubBrowser();
  downloadAircraft(populatedAircraft(), "Cessna172");
  expect(captured.blobs[0].text).toBe(JSON.stringify(populatedJson(), null, 4));
  expect("results" in (JSON.parse(captured.blobs[0].text) as Record<string, unknown>)).toBe(false);
});

it("an empty results block serializes exactly today's bytes", () => {
  const captured = stubBrowser();
  downloadAircraft(populatedAircraft(), "Cessna172", {});
  expect(captured.blobs[0].text).toBe(JSON.stringify(populatedJson(), null, 4));
  expect("results" in (JSON.parse(captured.blobs[0].text) as Record<string, unknown>)).toBe(false);
});

it("downloadAircraft does not mutate the aircraft it was handed", () => {
  stubBrowser();
  const ac = populatedAircraft();
  downloadAircraft(ac, "Cessna172", { datcom: solverResult("datcom") });
  expect("results" in ac).toBe(false);
  expect(ac.WG).toEqual({ CHRDR: 2, CHRDT: 1.4 });
});

it("downloadAircraft still names the file and revokes the object url", () => {
  const captured = stubBrowser();
  downloadAircraft(emptyAircraft(), "Cessna172", { datcom: solverResult("datcom") });
  expect(captured.names).toEqual(["Cessna172.jsonc"]);
  expect(captured.urls).toEqual([captured.blobs[0].text]);
  expect(captured.revoked).toEqual(captured.hrefs);
  expect(captured.blobs[0].options).toEqual({ type: "application/json" });
});

it("validateAircraft does not upload the results block", async () => {
  stubBrowser();
  const { bodies } = stubFetch();
  const ac = withResults({ datcom: solverResult("datcom") });
  await validateAircraft(ac);
  expect(bodies).toHaveLength(1);
  expect("results" in (bodyAircraft(bodies[0]))).toBe(false);
});

it("postAnalyze does not upload the results block", async () => {
  stubBrowser();
  const { bodies } = stubFetch();
  const ac = withResults({ datcom: solverResult("datcom") });
  await postAnalyze(ac, "tornado");
  expect(bodies).toHaveLength(1);
  expect("results" in (bodyAircraft(bodies[0]))).toBe(false);
});

it("fetchStability does not upload the results block", async () => {
  stubBrowser();
  const { bodies } = stubFetch();
  const ac = withResults({ datcom: solverResult("datcom") });
  await fetchStability(ac);
  expect(bodies).toHaveLength(1);
  expect("results" in (bodyAircraft(bodies[0]))).toBe(false);
});

it("an aircraft carrying a results block still validates and analyzes as geometry only", async () => {
  stubBrowser();
  const { bodies } = stubFetch();
  const ac = withResults({ datcom: solverResult("datcom") });
  expect(await validateAircraft(ac)).toEqual({ ok: true });
  const analyzed = await postAnalyze(ac, "tornado");
  expect(analyzed.ok).toBe(true);
  const sent = bodies.map((body) => bodyAircraft(body));
  for (const aircraft of sent) expect(aircraft).toEqual(populatedJson());
});

it("saveAircraftFromStore writes the usablePayload-gated block into the download", () => {
  const captured = stubBrowser();
  stubFetch();
  const store = createStore();
  const good = solverResult("datcom");
  const gated: SavedSolverResult = {
    solver: "tornado",
    payload: {},
    raw: { note: "unplottable" },
  };
  const loaded = { ...populatedJson(), results: { datcom: good, tornado: gated } };
  store.getState().openAircraft(loaded, "Cessna172");
  api.saveAircraftFromStore(store.getState());
  const written = JSON.parse(captured.blobs[0].text) as {
    results?: Record<string, SavedSolverResult>;
  };
  expect(written.results).toEqual({ datcom: good });
  expect("tornado" in (written.results ?? {})).toBe(false);
  expect(captured.names).toEqual(["Cessna172.jsonc"]);
});

it("saveAircraftFromStore writes a geometry-only file when resultsForSave is undefined", () => {
  const captured = stubBrowser();
  stubFetch();
  const store = createStore();
  store.getState().openAircraft(populatedJson(), "Cessna172");
  api.saveAircraftFromStore(store.getState());
  expect(captured.blobs[0].text).toBe(JSON.stringify(populatedJson(), null, 4));
});

it("saveAircraftFromStore downloads nothing without an aircraft", () => {
  const captured = stubBrowser();
  stubFetch();
  const store = createStore();
  expect(api.saveAircraftFromStore(store.getState())).toBeUndefined();
  expect(captured.blobs).toHaveLength(0);
});

it("saveAircraftFromStore falls back to aircraft.jsonc when the stem is missing", () => {
  const captured = stubBrowser();
  stubFetch();
  const store = createStore();
  store.getState().openAircraft(populatedJson(), "Cessna172");
  store.setState({ stem: null });
  api.saveAircraftFromStore(store.getState());
  expect(captured.names).toEqual(["aircraft.jsonc"]);
});

it("downloadAircraft ignores results carried by the aircraft it is handed", () => {
  const captured = stubBrowser();
  const ac: AircraftDict = {
    ...populatedAircraft(),
    results: { datcom: solverResult("datcom") },
  };
  downloadAircraft(ac, "Cessna172");
  expect("results" in (JSON.parse(captured.blobs[0].text) as Record<string, unknown>)).toBe(false);
});

function bodyAircraft(body: string): Record<string, unknown> {
  const parsed = JSON.parse(body) as { aircraft?: Record<string, unknown> };
  return parsed.aircraft ?? {};
}

function populatedAircraft(): AircraftDict {
  return {
    ...emptyAircraft(),
    WG: { CHRDR: 2, CHRDT: 1.4 },
    HT: { CHRDR: 1.3 },
    VT: { CHRDR: 5 },
    NP: [null, 2, null, null],
    NB: [1, 1],
    AERO: { MACH: 0.03 },
    plot_cmp: [1, 0, 1, 0],
  };
}

function populatedJson(): Record<string, unknown> {
  return JSON.parse(JSON.stringify(populatedAircraft())) as Record<string, unknown>;
}

function withResults(results: Record<string, SavedSolverResult>): AircraftDict {
  return { ...populatedAircraft(), results };
}

function solverResult(solver: string): SavedSolverResult {
  return {
    solver,
    payload: {
      source: "api",
      solver,
      axes: { alpha: [0, 5] },
      tables: { CL: [0.4, 0.5] },
      ref: { mac: 1.3 },
    },
    raw: { solver, lattice: { nodes: [[0, 0, 0], [1, 1, 1]], fields: ["cp"] }, note: "verbatim" },
  };
}
it("postAnalyze sends the sideslip from AERO.BETA in the request body", async () => {
  stubBrowser();
  const { bodies } = stubFetch();
  await postAnalyze({ ...populatedAircraft(), AERO: { MACH: 0.03, BETA: 5 } }, "tornado");
  expect((JSON.parse(bodies[0]) as { beta?: unknown }).beta).toBe(5);
});

it("postAnalyze sends beta zero when the aircraft carries no BETA key", async () => {
  stubBrowser();
  const { bodies } = stubFetch();
  await postAnalyze(populatedAircraft(), "tornado");
  expect((JSON.parse(bodies[0]) as { beta?: unknown }).beta).toBe(0);
});

it("fetchStability sends the sideslip too", async () => {
  stubBrowser();
  const { bodies } = stubFetch();
  await fetchStability({ ...populatedAircraft(), AERO: { MACH: 0.03, BETA: -5 } });
  expect((JSON.parse(bodies[0]) as { beta?: unknown }).beta).toBe(-5);
});
