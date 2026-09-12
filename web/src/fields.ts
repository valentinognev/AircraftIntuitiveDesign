export type FieldKind = "len" | "deg" | "le_te" | "chord" | "alt" | "mach" | "wt" | "inertia";

export type PlanformRow = readonly [field: string, label: string, kind: FieldKind];

export const PLANFORM_RP: readonly PlanformRow[] = [
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
];

export const PLANFORM_BREAKS = [3, 5, 8, 10, 13] as const;

export const AERO_FIELDS: readonly PlanformRow[] = [
  ["ALSCHD", "Angle(s) of Attack", "deg"],
  ["ALT", "Altitude", "alt"],
  ["MACH", "Mach Number", "mach"],
  ["WT", "Weight", "wt"],
  ["XCG", "CG Location, X", "len"],
  ["ZCG", "CG Location, Z", "len"],
  ["XI", "Inertia, X", "inertia"],
  ["YI", "Inertia, Y", "inertia"],
];

export const AERO_BREAKS = [1, 4, 6, 8, 11] as const;

export const AERO_NACA_FIELDS: readonly [key: string, label: string, cmpIndex: number][] = [
  ["WG.NACA[0]", "Wing Root Airfoil", 0],
  ["WG.NACA[1]", "Wing Tip Airfoil", 0],
  ["HT.NACA", "Tail Airfoil", 1],
];

export type ControlSpec = readonly [left: string, right: string | null, label: string, kind: FieldKind];

export type ControlBlock = readonly [
  prefix: "F" | "A" | "E" | "R",
  title: string,
  cmpIndex: number,
  specs: readonly ControlSpec[],
];

export const CONTROL_BLOCKS: readonly ControlBlock[] = [
  [
    "F",
    "Flaps:",
    0,
    [
      ["SPANFI", "SPANFO", "Span", "len"],
      ["CHRDFI", "CHRDFO", "Chord", "len"],
      ["DELTA", null, "Deflection", "deg"],
    ],
  ],
  [
    "A",
    "Ailerons:",
    0,
    [
      ["SPANFI", "SPANFO", "Span", "len"],
      ["CHRDFI", "CHRDFO", "Chord", "len"],
      ["DELTAL", "DELTAR", "Deflection", "deg"],
    ],
  ],
  [
    "E",
    "Elevator:",
    1,
    [
      ["SPANFI", "SPANFO", "Span", "len"],
      ["CHRDFI", "CHRDFO", "Chord", "len"],
      ["DELTA", null, "Deflection", "deg"],
    ],
  ],
  [
    "R",
    "Rudder:",
    2,
    [
      ["SPANFI", "SPANFO", "Span", "len"],
      ["CHRDFI", "CHRDFO", "Chord", "len"],
      ["DELTA", null, "Deflection", "deg"],
    ],
  ],
];

export const CONTROL_GRID_HEADERS = ["Inboard", "Outboard"] as const;

export const BODY_STATION_ROWS = 11;
export const EXTRA_BODY_STATION_ROWS = 7;
export const BODY_STATION_KEYS = ["N", "X", "P"] as const;

export function unitText(kind: string, unit: string, kts = true): string {
  if (kind === "len") return unit;
  if (kind === "deg") return "deg";
  if (kind === "le_te") return "LE-TE";
  if (kind === "chord") return "chord";
  if (kind === "alt") return "ft";
  if (kind === "mach") return kts ? "(or kts)" : "(or ft/s)";
  if (kind === "wt") return "lb";
  if (kind === "inertia") return unit === "in" ? "oz*in^2" : "slug*ft^2";
  if (kind === "naca") return "NACA";
  if (kind === "pos_hdr") return `Position, ${unit}`;
  return kind;
}
