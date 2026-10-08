import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { expect, test } from "vitest";
import { chartRows, type ControlDerivPayload } from "./controlDeriv";
import { ControlDerivChart } from "./Results";

// README.md:44: "any series that was not computed at that sideslip gets ` (beta=0)`
// appended, and at `BETA == 0` every label is byte-identical to the pre-feature text."
// The Controls chart is handbook-only (one solver, `solver: "handbook"`, per
// docs/superpowers/plans/2026-10-01-control-derivatives.md), and the handbook has no
// sideslip capability, so its curves are always at beta = 0 -- the mark therefore
// appears whenever the run asked for a sideslip. This asserts the legend a reader sees,
// not the series id: `Results.tsx` writes the id to `data-series` and it must stay bare.
const HANDBOOK: ControlDerivPayload = {
  solver: "handbook",
  deltas_deg: [0, 5],
  rows: [
    { surface: "flap", delta_deg: 0, available: true, reason: "", CL: 0.02, CD: null, Cm: -0.01, CY: null, Cl: null, Cn: null },
    { surface: "flap", delta_deg: 5, available: true, reason: "", CL: 0.05, CD: null, Cm: -0.03, CY: null, Cl: null, Cn: null },
  ],
};

const render = (payload: ControlDerivPayload, beta: number): string =>
  renderToStaticMarkup(createElement(ControlDerivChart, { series: chartRows(payload, beta) }));

test("the control-chart legend marks the handbook curves at a sideslip", () => {
  const markup = render(HANDBOOK, 5);
  expect(markup).toContain("handbook-flap-CL (beta=0)");
  expect(markup).toContain("handbook-flap-Cm (beta=0)");
  // The series id is a stable key, not a label: it rides on data-series, unmarked.
  expect(markup).toContain('data-series="handbook-flap-CL"');
});

test("the control-chart legend is unmarked at zero sideslip", () => {
  const markup = render(HANDBOOK, 0);
  expect(markup).not.toContain("(beta=0)");
  expect(markup).toContain("handbook-flap-CL");
});
