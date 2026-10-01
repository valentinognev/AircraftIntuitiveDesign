import { afterEach, expect, it, vi } from "vitest";
import { emptyAircraft } from "./aircraft";
import { postAnalyze } from "./api";
import {
  axisTicks,
  chartLayout,
  gridLines,
  overlaySeries,
  plotDomain,
  seriesFromPayload,
  solverStroke,
  svgPolyline,
  type HandshakePayload,
} from "./payload";
import { createStore } from "./store";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const DATCOM_PAYLOAD: HandshakePayload = {
  source: "aid",
  solver: "datcom",
  axes: { mach: [0.2], alpha: [-2, 0, 4], beta: [0] },
  tables: {
    cl: [[0.0, 0.2, 0.6]],
    cd: [[0.02, 0.02, 0.04]],
    cm: [[0.0, -0.01, -0.03]],
  },
  ref: {},
};

const TORNADO_PAYLOAD: HandshakePayload = {
  ...DATCOM_PAYLOAD,
  solver: "tornado",
  tables: {
    cl: [[0.1, 0.3, 0.5]],
    cd: [[0.02, 0.03, 0.04]],
    cm: [[0.01, 0.0, -0.02]],
  },
};

const FLOW5_PAYLOAD: HandshakePayload = {
  ...DATCOM_PAYLOAD,
  solver: "flow5",
};

const AVL_PAYLOAD: HandshakePayload = {
  ...DATCOM_PAYLOAD,
  solver: "avl",
};

it("plots CL, CD, Cm vs alpha from handshake payload", () => {
  const series = seriesFromPayload(DATCOM_PAYLOAD);
  expect(series.alpha).toEqual([-2, 0, 4]);
  expect(series.cl).toEqual([0.0, 0.2, 0.6]);
  expect(series.cd).toEqual([0.02, 0.02, 0.04]);
  expect(series.cm).toEqual([0.0, -0.01, -0.03]);
});

it("uses README overlay colors: DATCOM default, Tornado red, flow5 yellow", () => {
  expect(solverStroke("datcom")).toBe("currentColor");
  expect(solverStroke("tornado")).toBe("red");
  expect(solverStroke("flow5")).toBe("yellow");
  expect(solverStroke("avl")).toBe("currentColor");
  expect(solverStroke("avl")).toBe(solverStroke("datcom"));
});

it("overlays multiple solver payloads with those strokes", () => {
  const series = overlaySeries([DATCOM_PAYLOAD, TORNADO_PAYLOAD, FLOW5_PAYLOAD, AVL_PAYLOAD]);
  expect(series.map((s) => s.solver)).toEqual(["datcom", "tornado", "flow5", "avl"]);
  expect(series.map((s) => s.stroke)).toEqual(["currentColor", "red", "yellow", "currentColor"]);
});

it("maps overlay polylines onto one shared domain per chart", () => {
  const wide: HandshakePayload = {
    ...DATCOM_PAYLOAD,
    axes: { mach: [0.2], alpha: [0, 10], beta: [0] },
    tables: { cl: [[0, 1]], cd: [[0.02, 0.04]], cm: [[0, -0.1]] },
  };
  const half: HandshakePayload = {
    ...TORNADO_PAYLOAD,
    axes: { mach: [0.2], alpha: [0, 10], beta: [0] },
    tables: { cl: [[0, 0.5]], cd: [[0.02, 0.03]], cm: [[0, -0.05]] },
  };
  const series = overlaySeries([wide, half]);
  const domain = plotDomain(series, (s) => s.cl);
  expect(domain).toEqual({ xmin: 0, xmax: 10, ymin: 0, ymax: 1 });
  const ptsWide = svgPolyline(series[0].alpha, series[0].cl, 100, 100, 0, domain!);
  const ptsHalf = svgPolyline(series[1].alpha, series[1].cl, 100, 100, 0, domain!);
  expect(ptsWide).toBe("0,100 100,0");
  expect(ptsHalf).toBe("0,100 100,50");
});

it("lays out a plot rectangle with room for axis ticks", () => {
  const layout = chartLayout(400, 180);
  expect(layout.plot.x).toBeGreaterThan(24);
  expect(layout.plot.y).toBeGreaterThan(0);
  expect(layout.plot.x + layout.plot.width).toBeLessThan(400);
  expect(layout.plot.y + layout.plot.height).toBeLessThan(180);
  expect(layout.plot.width / layout.width).toBeGreaterThan(0.7);
  expect(layout.plot.height / layout.height).toBeGreaterThan(0.6);
});

it("places numeric ticks and a grid on the shared domain", () => {
  const domain = { xmin: -4, xmax: 16, ymin: 0, ymax: 1.5 };
  const xTicks = axisTicks(domain.xmin, domain.xmax);
  const yTicks = axisTicks(domain.ymin, domain.ymax);
  expect(xTicks.map((t) => t.value)).toEqual([-4, 0, 4, 8, 12, 16]);
  expect(yTicks.map((t) => t.value)).toEqual([0, 0.5, 1, 1.5]);
  expect(xTicks.every((t) => t.label.length > 0)).toBe(true);
  const lines = gridLines(domain, chartLayout(400, 180).plot);
  expect(lines.some((line) => line.y1 === line.y2)).toBe(true);
  expect(lines.some((line) => line.x1 === line.x2)).toBe(true);
  expect(lines.length).toBe(xTicks.length + yTicks.length);
});

it("draws each series across the plot rectangle", () => {
  const domain = { xmin: -4, xmax: 16, ymin: 0, ymax: 1.2 };
  const { width, height, plot } = chartLayout(400, 180);
  const pts = svgPolyline([-4, 16], [0, 1.2], width, height, 0, domain, plot);
  const [start, end] = pts.split(" ");
  expect(Number(start.split(",")[0])).toBeCloseTo(plot.x);
  expect(Number(end.split(",")[0])).toBeCloseTo(plot.x + plot.width);
});

it("ignores DATCOM no-data sentinels when scaling", () => {
  const series = overlaySeries([
    {
      ...DATCOM_PAYLOAD,
      axes: { mach: [0.2], alpha: [-2, 0, 4], beta: [0] },
      tables: { cl: [[0.2, 99999, 0.8]], cd: [[0.02, 0.03, 0.04]], cm: [[0, -0.01, -0.02]] },
    },
  ]);
  expect(plotDomain(series, (s) => s.cl)).toEqual({ xmin: -2, xmax: 4, ymin: 0.2, ymax: 0.8 });
  const pts = svgPolyline(series[0].alpha, series[0].cl, 100, 100, 0);
  expect(pts.split(" ")).toHaveLength(2);
});

it("postAnalyze POSTs handshake payload to CADAC when cadacSession is set", async () => {
  vi.stubGlobal("location", { search: "?cadacSession=sess-1" });
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes("/analyze")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
      };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true }) };
  });
  vi.stubGlobal("fetch", fetchMock);

  const result = await postAnalyze(emptyAircraft(), "datcom");
  expect(result.ok).toBe(true);
  if (result.ok) expect(result.payload.source).toBe("aid");

  const complete = fetchMock.mock.calls.find(([url]) =>
    String(url).includes("/handshake/sessions/sess-1/complete"),
  );
  expect(complete).toBeDefined();
  expect(complete![1]).toEqual({
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(DATCOM_PAYLOAD),
  });
});

it("postAnalyze does not POST CADAC when cadacSession is absent", async () => {
  vi.stubGlobal("location", { search: "" });
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
  }));
  vi.stubGlobal("fetch", fetchMock);
  await postAnalyze(emptyAircraft(), "datcom");
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(String(fetchMock.mock.calls[0][0])).toBe("/analyze");
});

it("runAnalyze stores lastPayload", async () => {
  vi.stubGlobal("location", { search: "" });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
    })),
  );
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().lastPayload).toEqual(DATCOM_PAYLOAD);
  expect(store.getState().tab).toBe("aero");
  expect(store.getState().analyzing).toBe(false);
});

it("clears analyzing on openNew and if revision changes mid-analyze", async () => {
  let finish: (value: unknown) => void = () => {};
  const gate = new Promise((resolve) => {
    finish = resolve;
  });
  vi.stubGlobal("location", { search: "" });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      await gate;
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
      };
    }),
  );
  const store = createStore();
  store.getState().openNew();
  const pending = store.getState().runAnalyze("datcom");
  expect(store.getState().analyzing).toBe(true);
  store.getState().openNew();
  expect(store.getState().analyzing).toBe(false);
  finish(undefined);
  await pending;
  expect(store.getState().analyzing).toBe(false);
});

it("clears analyzing after a field edit during in-flight Analyze", async () => {
  let finish: (value: unknown) => void = () => {};
  const gate = new Promise((resolve) => {
    finish = resolve;
  });
  vi.stubGlobal("location", { search: "" });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      await gate;
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
      };
    }),
  );
  const store = createStore();
  store.getState().openNew();
  const pending = store.getState().runAnalyze("datcom");
  expect(store.getState().analyzing).toBe(true);
  store.getState().setGroupField("WG", "CHRDR", 3);
  expect(store.getState().revision).toBeGreaterThan(1);
  finish(undefined);
  await pending;
  expect(store.getState().analyzing).toBe(false);
});

it("CADAC complete HTTP 500 sets handshake error and keeps lastPayload", async () => {
  vi.stubGlobal("location", { search: "?cadacSession=sess-1" });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/analyze")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
        };
      }
      return { ok: false, status: 500, json: async () => ({ ok: false, error: "complete failed" }) };
    }),
  );
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().lastPayload).toEqual(DATCOM_PAYLOAD);
  expect(store.getState().payloads.datcom).toEqual(DATCOM_PAYLOAD);
  expect(store.getState().handshakeError).toBe("CADAC complete HTTP 500");
  expect(store.getState().analyzeError).toBeNull();
});

it("CADAC complete network error sets handshake error and keeps lastPayload", async () => {
  vi.stubGlobal("location", { search: "?cadacSession=sess-1" });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/analyze")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
        };
      }
      throw new Error("Failed to fetch");
    }),
  );
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().lastPayload).toEqual(DATCOM_PAYLOAD);
  expect(store.getState().handshakeError).toBe("Failed to fetch");
  expect(store.getState().analyzeError).toBeNull();
});

const DATCOM_RAW = { cl: [0.2], alpha: [0] };
const TORNADO_RAW = { CL: [0.4], alpha: [1] };
const HANDBOOK = { y: [0, 1], Cl: [0.1, 0.2] };

function stubAnalyze(jsonFor: (solver: string) => unknown) {
  vi.stubGlobal("location", { search: "" });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (!String(input).includes("/analyze")) {
        return { ok: true, status: 200, json: async () => ({}) };
      }
      const req = JSON.parse(String(init?.body ?? "{}")) as { solver?: string };
      return {
        ok: true,
        status: 200,
        json: async () => jsonFor(req.solver ?? "datcom"),
      };
    }),
  );
}

it("postAnalyze includes an object handbook, otherwise null", async () => {
  vi.stubGlobal("location", { search: "" });
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      ok: true,
      solver: "datcom",
      raw: DATCOM_RAW,
      payload: DATCOM_PAYLOAD,
      handbook: HANDBOOK,
    }),
  }));
  vi.stubGlobal("fetch", fetchMock);
  const withBook = await postAnalyze(emptyAircraft(), "datcom");
  expect(withBook.ok).toBe(true);
  if (withBook.ok) expect(withBook.handbook).toEqual(HANDBOOK);

  fetchMock.mockImplementation(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ ok: true, solver: "datcom", raw: DATCOM_RAW, payload: DATCOM_PAYLOAD }),
  }));
  const omitted = await postAnalyze(emptyAircraft(), "datcom");
  expect(omitted.ok).toBe(true);
  if (omitted.ok) expect(omitted.handbook).toBeNull();

  fetchMock.mockImplementation(async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      ok: true,
      solver: "datcom",
      raw: DATCOM_RAW,
      payload: DATCOM_PAYLOAD,
      handbook: [0.1, 0.2],
    }),
  }));
  const notObject = await postAnalyze(emptyAircraft(), "datcom");
  expect(notObject.ok).toBe(true);
  if (notObject.ok) expect(notObject.handbook).toBeNull();
});

it("stores analyze raw at raws.datcom and keeps lastPayload", async () => {
  stubAnalyze(() => ({ ok: true, solver: "datcom", raw: DATCOM_RAW, payload: DATCOM_PAYLOAD }));
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().raws.datcom).toEqual(DATCOM_RAW);
  expect(store.getState().lastPayload).toEqual(DATCOM_PAYLOAD);
});

it("keeps datcom raw when a tornado analyze is stored", async () => {
  stubAnalyze((solver) =>
    solver === "tornado"
      ? { ok: true, solver: "tornado", raw: TORNADO_RAW, payload: TORNADO_PAYLOAD }
      : { ok: true, solver: "datcom", raw: DATCOM_RAW, payload: DATCOM_PAYLOAD },
  );
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  await store.getState().runAnalyze("tornado");
  expect(store.getState().raws.datcom).toEqual(DATCOM_RAW);
  expect(store.getState().raws.tornado).toEqual(TORNADO_RAW);
});

it("openNew clears raws and handbook", async () => {
  stubAnalyze(() => ({
    ok: true,
    solver: "datcom",
    raw: DATCOM_RAW,
    payload: DATCOM_PAYLOAD,
    handbook: HANDBOOK,
  }));
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().raws.datcom).toEqual(DATCOM_RAW);
  expect(store.getState().handbook).toEqual(HANDBOOK);
  store.getState().openNew();
  expect(store.getState().raws).toEqual({});
  expect(store.getState().handbook).toBeNull();
});

it("openAircraft clears raws and handbook", async () => {
  stubAnalyze(() => ({
    ok: true,
    solver: "datcom",
    raw: DATCOM_RAW,
    payload: DATCOM_PAYLOAD,
    handbook: HANDBOOK,
  }));
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  store.getState().openAircraft(emptyAircraft(), "cessna");
  expect(store.getState().raws).toEqual({});
  expect(store.getState().handbook).toBeNull();
});

it("stores handbook y and Cl from analyze JSON", async () => {
  stubAnalyze(() => ({
    ok: true,
    solver: "datcom",
    raw: DATCOM_RAW,
    payload: DATCOM_PAYLOAD,
    handbook: { y: [0, 1], Cl: [0.1, 0.2] },
  }));
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().handbook).toEqual({ y: [0, 1], Cl: [0.1, 0.2] });
});

it("leaves the previous handbook when a later analyze omits it or sends invalid y/Cl", async () => {
  const responses: unknown[] = [
    {
      ok: true,
      solver: "datcom",
      raw: DATCOM_RAW,
      payload: DATCOM_PAYLOAD,
      handbook: HANDBOOK,
    },
    { ok: true, solver: "datcom", raw: { cl: [0.3], alpha: [1] }, payload: DATCOM_PAYLOAD },
    {
      ok: true,
      solver: "datcom",
      raw: DATCOM_RAW,
      payload: DATCOM_PAYLOAD,
      handbook: { y: [0, 1], Cl: [0.1] },
    },
    {
      ok: true,
      solver: "datcom",
      raw: DATCOM_RAW,
      payload: DATCOM_PAYLOAD,
      handbook: { y: [0, Number.NaN], Cl: [0.1, 0.2] },
    },
    {
      ok: true,
      solver: "datcom",
      raw: DATCOM_RAW,
      payload: DATCOM_PAYLOAD,
      handbook: { Cl: [0.1, 0.2] },
    },
    {
      ok: true,
      solver: "datcom",
      raw: DATCOM_RAW,
      payload: DATCOM_PAYLOAD,
      handbook: { y: [0, Number.POSITIVE_INFINITY], Cl: [0.1, 0.2] },
    },
  ];
  let i = 0;
  stubAnalyze(() => responses[i++]);
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().handbook).toEqual(HANDBOOK);
  await store.getState().runAnalyze("datcom");
  expect(store.getState().handbook).toEqual(HANDBOOK);
  expect(store.getState().raws.datcom).toEqual({ cl: [0.3], alpha: [1] });
  for (let n = 2; n < responses.length; n += 1) {
    await store.getState().runAnalyze("datcom");
    expect(store.getState().handbook).toEqual(HANDBOOK);
  }
});

it("successful CADAC complete does not set handshake error", async () => {
  vi.stubGlobal("location", { search: "?cadacSession=sess-1" });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/analyze")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, solver: "datcom", raw: {}, payload: DATCOM_PAYLOAD }),
        };
      }
      return { ok: true, status: 200, json: async () => ({ ok: true }) };
    }),
  );
  const store = createStore();
  store.getState().openNew();
  await store.getState().runAnalyze("datcom");
  expect(store.getState().lastPayload).toEqual(DATCOM_PAYLOAD);
  expect(store.getState().handshakeError).toBeNull();
  expect(store.getState().analyzeError).toBeNull();
});
