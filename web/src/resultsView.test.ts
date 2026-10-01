import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, expect, it } from "vitest";
import type { HandshakePayload } from "./payload";
import { Results } from "./Results";
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
