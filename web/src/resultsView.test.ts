import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, expect, it } from "vitest";
import type { HandshakePayload } from "./payload";
import { flownBeta, Results } from "./Results";
import store from "./store";

const snapshot = store.getState();

afterEach(() => {
  store.setState(snapshot, true);
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

const TAB_LABELS = ["Forces", "Moments", "Derivatives", "Downwash", "Controls", "Spanwise", "Sections"];

function markup(initialTab?: string): string {
  return renderToStaticMarkup(createElement(Results, initialTab ? { initialTab } : {}));
}

it("asks to analyze when no solver raw and no handshake series exist", () => {
  store.setState({ raws: { panel: { cl: [1] } }, handbook: null, lastPayload: null, payloads: {}, lastStability: null });
  expect(markup()).toContain("Analyze to plot CL, CD, Cm vs α.");
});

it("keeps the three handshake charts when raws is empty", () => {
  store.setState({
    raws: {},
    handbook: null,
    lastStability: null,
    lastPayload: DATCOM_PAYLOAD,
    payloads: { datcom: DATCOM_PAYLOAD },
  });
  const html = markup();
  expect(html).toContain("CL vs α");
  expect(html).toContain("CD vs α");
  expect(html).toContain("Cm vs α");
  expect(html).not.toContain(">Forces<");
});

it("replaces those charts with seven tabs when a solver raw exists", () => {
  store.setState({
    raws: { datcom: { alpha: [0, 2], cl: [0.1, 0.2] }, panel: { cl: [1] } },
    handbook: null,
    lastPayload: DATCOM_PAYLOAD,
    payloads: { datcom: DATCOM_PAYLOAD },
    lastStability: { alpha: 2, summary: ["static margin 10%"] },
  });
  const html = markup();
  for (const label of TAB_LABELS) expect(html).toContain(`>${label}</button>`);
  expect(html).toMatch(/aria-selected="true"[^>]*>Forces<\/button>/);
  expect(html.indexOf("static margin 10%")).toBeLessThan(html.indexOf(">Forces</button>"));
  expect(html).not.toContain("CL vs α");
  expect(html).toContain(">CL<");
  expect(html).not.toContain("Spanwise lift");
});

it("draws one AVL sample as a circle and several samples as a polyline", () => {
  store.setState({
    raws: { avl: { alpha: 4, CLtot: 0.2 } },
    handbook: null,
    lastPayload: null,
    payloads: {},
    lastStability: null,
  });
  const one = markup("forces");
  expect(one).toMatch(/<circle[^>]*r="3.5"[^>]*fill="magenta"/);
  expect(one).not.toMatch(/<polyline[^>]*stroke="magenta"/);

  store.setState({
    raws: { avl: { alpha: [-4, 0, 4], CLtot: [0.1, 0.4, 0.7] } },
    handbook: null,
    lastPayload: null,
    payloads: {},
    lastStability: null,
  });
  const many = markup("forces");
  expect(many).toMatch(/<polyline[^>]*points="[^"]* [^"]*"[^>]*stroke="magenta"/);
  expect(many).not.toMatch(/<circle[^>]*fill="magenta"/);
});

it("shows only the selected tab, including spanwise names and section table alignment", () => {
  store.setState({
    raws: {
      datcom: { sections: { wing: { cm0: 0.1 }, ht: {}, vt: {} } },
      tornado: { spanwise: [{ name: "Wing", y: [0, 1], Cl: [0.2, 0.4] }] },
    },
    handbook: { y: [0, 1], Cl: [0.1, 0.3] },
    lastPayload: null,
    payloads: {},
    lastStability: { alpha: Number.NaN },
  });
  const spanwise = markup("spanwise");
  expect(spanwise).toMatch(/aria-selected="true"[^>]*>Spanwise<\/button>/);
  expect(spanwise).toContain("Spanwise lift");
  expect(spanwise).toContain("Prandtl");
  expect(spanwise).toContain("Tornado Wing");
  expect(spanwise).not.toContain("Section definition");

  const sections = markup("sections");
  expect(sections).toContain("Section definition");
  expect(sections).toContain("font-medium");
  expect(sections).toContain("text-right");
  expect(sections).toContain(">0.1<");
  expect(sections).not.toContain("Spanwise lift");
});

// The `(beta=0)` mark is a provenance claim about the plotted numbers, so it must
// follow the run that produced them. These four cases pin that from both sides:
// an editor-only sideslip must not relabel a β=0 run, and a flown sideslip must
// still be disclosed when the editor has been put back to zero.
function sideslipPayload(solver: string, beta: number): HandshakePayload {
  return {
    source: "aid",
    solver,
    axes: { mach: [0.2], alpha: [-2, 0, 4], beta: [beta] },
    tables: { cl: [[0.0, 0.2, 0.6]], cd: [[0.02, 0.02, 0.04]], cm: [[0.0, -0.01, -0.03]] },
    ref: {},
  };
}

function withSideslipInEditor(beta: number): void {
  store.setState({
    ...store.getState(),
    aircraft: { AERO: { ALSCHD: [-2, 0, 4], BETA: beta } } as never,
  });
}

it("labels from the run, not from a Beta edited after the run", () => {
  const datcom = sideslipPayload("datcom", 0);
  store.setState({
    raws: { datcom: { alpha: [-2, 0, 4], cl: [0.0, 0.2, 0.6], cd: [0.02, 0.02, 0.04] } },
    handbook: null,
    lastStability: { alpha: 4, summary: [] },
    lastPayload: datcom,
    payloads: { datcom },
  });

  // A run at beta = 0 stays unlabelled even once the editor claims a sideslip.
  withSideslipInEditor(5);
  expect(markup("forces")).not.toContain("(beta=0)");

  // ... and a run that really flew a sideslip is still disclosed when the
  // editor has been put back to zero, which is the same defect the other way.
  const flown = sideslipPayload("tornado", 5);
  store.setState({
    ...store.getState(),
    raws: { datcom: { alpha: [-2, 0, 4], cl: [0.0, 0.2, 0.6] } },
    payloads: { datcom, tornado: flown },
    lastPayload: flown,
  });
  withSideslipInEditor(0);
  expect(markup("forces")).toContain("(beta=0)");
});

it("flownBeta reads the run's payload and nothing else", () => {
  expect(flownBeta([])).toBe(0);
  expect(flownBeta([sideslipPayload("datcom", 0), sideslipPayload("avl", 0)])).toBe(0);
  expect(flownBeta([sideslipPayload("datcom", 0), sideslipPayload("tornado", 5)])).toBe(5);
  // flow5 is the other sideslip-capable solver; the value is whatever the run flew.
  expect(flownBeta([sideship0(), sideslipPayload("flow5", -3)])).toBe(-3);
  // Non-numeric or missing beta is not a sideslip.
  const broken = sideslipPayload("tornado", 5);
  broken.axes.beta = [];
  expect(flownBeta([broken])).toBe(0);
  const nan = sideslipPayload("tornado", 5);
  nan.axes.beta = [Number.NaN];
  expect(flownBeta([nan])).toBe(0);

  function sideship0(): HandshakePayload {
    return sideslipPayload("datcom", 0);
  }
});
