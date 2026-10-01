import { expect, test } from "vitest";
import { chartRows } from "./controlDeriv";

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
