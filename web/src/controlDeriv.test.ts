import { expect, test } from "vitest";
import { chartRows, controlLegendText } from "./controlDeriv";

const HANDBOOK = {
  solver: "handbook",
  deltas_deg: [0, 5],
  rows: [
    { surface: "flap", delta_deg: 0, available: true, reason: "", CL: 0.02, CD: null, Cm: -0.01, CY: null, Cl: null, Cn: null },
    { surface: "flap", delta_deg: 5, available: true, reason: "", CL: 0.02, CD: null, Cm: -0.01, CY: null, Cl: null, Cn: null },
    { surface: "rudder", delta_deg: 0, available: false, reason: "datcom has no rudder namelist", CL: null, CD: null, Cm: null, CY: null, Cl: null, Cn: null },
  ],
};

// README.md:44: "any series that was not computed at that sideslip gets ` (beta=0)`
// appended, and at `BETA == 0` every label is byte-identical to the pre-feature text."
// The Controls chart is handbook-only and the handbook has no sideslip input, so its
// curves are at beta = 0 whatever the run asked for.
test("marks the handbook control curves at a sideslip and not at zero", () => {
  const swept = chartRows(HANDBOOK, 5);
  const flapCL = swept.find((s) => s.id === "handbook-flap-CL");
  expect(flapCL?.label).toBe("handbook-flap-CL (beta=0)");
  expect(swept.every((s) => s.label?.includes("(beta=0)"))).toBe(true);
  // The id is unchanged: `Results.tsx` writes it to data-series and Results reads it.
  expect(swept.some((s) => s.id === "handbook-flap-CL")).toBe(true);

  const upright = chartRows(HANDBOOK, 0);
  expect(upright.every((s) => s.label === undefined)).toBe(true);
  expect(controlLegendText(upright[0])).toBe("handbook-flap-CL");
});

test("zero and five degree probes survive null coefficients", () => {
  const rows = chartRows({
    solver: "handbook",
    deltas_deg: [0, 5],
    rows: [
      { surface: "flap", delta_deg: 0, available: true, reason: "", CL: 0.02, CD: null, Cm: -0.01, CY: null, Cl: null, Cn: null },
      { surface: "flap", delta_deg: 5, available: true, reason: "", CL: 0.02, CD: null, Cm: -0.01, CY: null, Cl: null, Cn: null },
      { surface: "rudder", delta_deg: 0, available: false, reason: "datcom has no rudder namelist", CL: null, CD: null, Cm: null, CY: null, Cl: null, Cn: null },
    ],
  });
  const flapCL = rows.find((s) => s.id === "handbook-flap-CL");
  expect(flapCL?.xs).toEqual([0, 5]);
  expect(flapCL?.ys).toEqual([0.02, 0.02]);
  expect(rows.some((s) => s.id.includes("rudder"))).toBe(false);
});
