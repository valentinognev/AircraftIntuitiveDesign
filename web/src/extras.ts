import { PLANFORM_RP } from "./fields";
import type { AircraftDict } from "./aircraft";

export const PLUS_PARTS = ["New Body", "Propeller", "New Wing", "New HT", "New VT"] as const;

export function ensureNpNb(ac: AircraftDict): AircraftDict {
  const NP = [...(ac.NP ?? [])];
  while (NP.length < 4) NP.push(null);
  const NB = [...(ac.NB ?? [])];
  while (NB.length < 2) NB.push(null);
  return { ...ac, NP, NB };
}

function bodyLength(ac: AircraftDict): number {
  const raw = ac.BD?.X;
  const x = Array.isArray(raw) ? raw.map(Number).filter((n) => Number.isFinite(n)) : [];
  if (x.length < 2) return 1;
  return x[x.length - 1] - x[0];
}

function defaultPlanform(ac: AircraftDict, slot: number): Record<string, unknown> {
  const L = bodyLength(ac);
  let vals: number[];
  let naca: string;
  if (slot === 0) {
    vals = [L / 4, L / 4, L / 4, L / 2, 0, 0, 0, 0.25, 0, 0, 0.12, 0, 0, L / 4, 0, 0];
    naca = "2412";
  } else if (slot === 1) {
    vals = [L / 8, L / 8, L / 8, L / 4, 0, 0, 0, 1, 0, 0, 0.12, 0, 0, (7 * L) / 8, 0, 0];
    naca = "0012";
  } else if (slot === 2) {
    vals = [L / 8, L / 8, L / 8, L / 4, 0, 0, 0, 1, 0, 0, 0.12, 0, 0, (7 * L) / 8, 0, 0];
    naca = "0012";
  } else {
    vals = [L / 32, L / 32, L / 64, L / 8, 0, 0, 0, 0, 0, 0, 0.12, 30, 30, L / 4, L / 4, 0];
    naca = "0012";
  }
  const pt: Record<string, unknown> = {};
  PLANFORM_RP.forEach(([field], i) => {
    pt[field] = vals[i];
  });
  pt.NACA = naca;
  pt.SSPNE = pt.SSPN;
  return pt;
}

function defaultBody(ac: AircraftDict): Record<string, unknown> {
  const L = bodyLength(ac);
  const nx = 7;
  const x: number[] = [];
  for (let i = 0; i < nx; i++) x.push((i * (L / 4)) / (nx - 1));
  const r = L / 24;
  const s = Math.PI * r * r;
  return {
    NX: nx,
    X: x,
    ZU: Array(nx).fill(r),
    ZL: Array(nx).fill(-r),
    R: Array(nx).fill(r),
    S: Array(nx).fill(s),
    N: Array.from({ length: nx }, (_, i) => i + 1),
    P: Array(nx).fill(1),
    ITYPE: 1,
    X0: L / 4,
    Y0: L / 4,
    Z0: 0,
  };
}

function isDict(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

export type ExtraTabId = "body2" | "body3" | "prop" | "wing2" | "ht2" | "vt2";

export type ExtraTabInfo = { id: ExtraTabId; label: string };

const NP_TABS: { slot: number; id: ExtraTabId; label: string }[] = [
  { slot: 3, id: "prop", label: "Prop" },
  { slot: 0, id: "wing2", label: "Wing 2" },
  { slot: 1, id: "ht2", label: "HT 2" },
  { slot: 2, id: "vt2", label: "VT 2" },
];

export function extraTabs(ac: AircraftDict | null): ExtraTabInfo[] {
  if (ac == null) return [];
  const padded = ensureNpNb(ac);
  const tabs: ExtraTabInfo[] = [];
  if (isDict(padded.NB[0])) tabs.push({ id: "body2", label: "Body 2" });
  if (isDict(padded.NB[1])) tabs.push({ id: "body3", label: "Body 3" });
  for (const item of NP_TABS) {
    if (isDict(padded.NP[item.slot])) tabs.push({ id: item.id, label: item.label });
  }
  return tabs;
}

export function hiddenPlusButtons(ac: AircraftDict | null): string[] {
  if (ac == null) return [];
  const padded = ensureNpNb(ac);
  const hidden: string[] = [];
  if (isDict(padded.NB[0]) && isDict(padded.NB[1])) hidden.push("New Body");
  if (isDict(padded.NP[3])) hidden.push("Propeller");
  if (isDict(padded.NP[0])) hidden.push("New Wing");
  if (isDict(padded.NP[1])) hidden.push("New HT");
  if (isDict(padded.NP[2])) hidden.push("New VT");
  return hidden;
}

export function extraTabForPart(ac: AircraftDict, component: number): ExtraTabId | null {
  if (component === 1) {
    return isDict(ensureNpNb(ac).NB[1]) ? "body3" : "body2";
  }
  if (component === 2) return "prop";
  if (component === 3) return "wing2";
  if (component === 4) return "ht2";
  if (component === 5) return "vt2";
  return null;
}

export function addPart(ac: AircraftDict, component: number): AircraftDict {
  const next = ensureNpNb(ac);
  const NP = [...next.NP];
  const NB = [...next.NB];
  if (component === 1) {
    const slot = isDict(NB[0]) ? 1 : 0;
    if (!isDict(NB[slot])) NB[slot] = defaultBody(next);
  } else if (component === 2) {
    if (!isDict(NP[3])) NP[3] = defaultPlanform(next, 3);
  } else if (component === 3) {
    if (!isDict(NP[0])) NP[0] = defaultPlanform(next, 0);
  } else if (component === 4) {
    if (!isDict(NP[1])) NP[1] = defaultPlanform(next, 1);
  } else if (component === 5) {
    if (!isDict(NP[2])) NP[2] = defaultPlanform(next, 2);
  } else {
    return next;
  }
  return { ...next, NP, NB };
}

export function patchSlotField(
  ac: AircraftDict,
  list: "NP" | "NB",
  slot: number,
  key: string,
  value: unknown,
): AircraftDict {
  const padded = ensureNpNb(ac);
  const arr = [...padded[list]];
  const cur = isDict(arr[slot]) ? { ...arr[slot] } : {};
  cur[key] = value;
  arr[slot] = cur;
  return { ...padded, [list]: arr };
}

export function patchSlotArrayItem(
  ac: AircraftDict,
  list: "NP" | "NB",
  slot: number,
  key: string,
  index: number,
  value: unknown,
): AircraftDict {
  const padded = ensureNpNb(ac);
  const arr = [...padded[list]];
  const cur = isDict(arr[slot]) ? { ...arr[slot] } : {};
  const listVal = Array.isArray(cur[key]) ? [...(cur[key] as unknown[])] : [];
  while (listVal.length <= index) listVal.push(null);
  listVal[index] = value;
  cur[key] = listVal;
  arr[slot] = cur;
  return { ...padded, [list]: arr };
}
