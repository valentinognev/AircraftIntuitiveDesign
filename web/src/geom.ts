import type { AircraftDict } from "./aircraft";

export class GeometryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GeometryError";
  }
}

export type Vec3 = { x: number; y: number; z: number };
export type Polyline = Vec3[];
export type WingOutline = { le: Polyline; te: Polyline };
export type Tessellation = { fuselage: Polyline[]; wings: WingOutline[] };
export type Scene = Tessellation;

export type SceneOk = { ok: true; scene: Scene };
export type SceneFail = { ok: false; message: string };
export type SceneResult = SceneOk | SceneFail;

function num(value: unknown, fallback = 0): number {
  if (value == null || value === "") return fallback;
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) throw new GeometryError("non-finite geometry value");
  return n;
}

function rad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function plotOn(ac: AircraftDict, index: number): boolean {
  const flag = ac.plot_cmp[index];
  if (flag == null) return true;
  return Number(flag) !== 0;
}

function finiteList(value: unknown, n: number): number[] {
  if (!Array.isArray(value)) return [];
  const out: number[] = [];
  for (let i = 0; i < Math.min(n, value.length); i++) {
    const v = num(value[i]);
    out.push(v);
  }
  return out;
}

type Kind = "wing" | "ht" | "vt";

function stationPoint(
  pt: Record<string, unknown>,
  span: number,
  chord: number,
  sweepDeg: number,
  dihedralDeg: number,
  chstat: number,
  chordRoot: number,
  kind: Kind,
): { le: Vec3; te: Vec3 } {
  const x0 = num(pt.X);
  const y0 = num(pt.Y);
  const z0 = num(pt.Z);
  const yAlong = span * Math.cos(rad(dihedralDeg));
  const zOff = yAlong * Math.tan(rad(dihedralDeg));
  const xLe = x0 + yAlong * Math.tan(rad(sweepDeg)) + chstat * (chordRoot - chord);
  if (kind === "vt") {
    return {
      le: { x: xLe, y: y0, z: z0 + span },
      te: { x: xLe + chord, y: y0, z: z0 + span },
    };
  }
  return {
    le: { x: xLe, y: y0 + yAlong, z: z0 + zOff },
    te: { x: xLe + chord, y: y0 + yAlong, z: z0 + zOff },
  };
}

function planformOutline(pt: Record<string, unknown>, kind: Kind): WingOutline | null {
  const chrdr = num(pt.CHRDR);
  const sspn = num(pt.SSPN);
  if (sspn < 0) throw new GeometryError("SSPN must be >= 0");
  if (chrdr < 0) throw new GeometryError("CHRDR must be >= 0");
  if (sspn === 0) return null;
  const chrdtp = pt.CHRDTP == null || pt.CHRDTP === "" ? chrdr : num(pt.CHRDTP);
  const savsi = num(pt.SAVSI);
  const savso = num(pt.SAVSO);
  const chstat = num(pt.CHSTAT);
  const dhdadi = num(pt.DHDADI);
  const dhdado = num(pt.DHDADO);
  const sspnop = num(pt.SSPNOP);
  const chrdbp = num(pt.CHRDBP);

  const le: Polyline = [];
  const te: Polyline = [];
  const push = (s: { le: Vec3; te: Vec3 }) => {
    le.push(s.le);
    te.push(s.te);
  };

  push(stationPoint(pt, 0, chrdr, savsi, dhdadi, chstat, chrdr, kind));
  if (chrdbp && sspnop > 0 && sspnop < sspn) {
    push(stationPoint(pt, sspnop, chrdbp, savsi, dhdadi, chstat, chrdr, kind));
    push(stationPoint(pt, sspn, chrdtp, savso, dhdado, chstat, chrdbp, kind));
  } else {
    push(stationPoint(pt, sspn, chrdtp, savsi, dhdadi, chstat, chrdr, kind));
  }
  return { le, te };
}

function mirrorY(wing: WingOutline): WingOutline {
  return {
    le: wing.le.map((p) => ({ ...p, y: -p.y })),
    te: wing.te.map((p) => ({ ...p, y: -p.y })),
  };
}

function fuselagePolylines(bd: Record<string, unknown>): Polyline[] {
  const nx = Math.max(0, Math.floor(num(bd.NX, 0)));
  const xs = finiteList(bd.X, nx || (Array.isArray(bd.X) ? bd.X.length : 0));
  const n = xs.length;
  if (n < 2) return [];
  const zu = finiteList(bd.ZU, n);
  const zl = finiteList(bd.ZL, n);
  const r = finiteList(bd.R, n);
  const upper: Polyline = [];
  const lower: Polyline = [];
  const right: Polyline = [];
  const left: Polyline = [];
  for (let i = 0; i < n; i++) {
    const x = xs[i];
    const u = zu[i] ?? 0;
    const l = zl[i] ?? 0;
    const half = r[i] ?? 0;
    const zc = (u + l) / 2;
    upper.push({ x, y: 0, z: u });
    lower.push({ x, y: 0, z: l });
    right.push({ x, y: half, z: zc });
    left.push({ x, y: -half, z: zc });
  }
  return [upper, lower, right, left];
}

export function tessellate(ac: AircraftDict): Tessellation {
  const fuselage: Polyline[] = [];
  const wings: WingOutline[] = [];
  if (plotOn(ac, 0)) {
    const wg = planformOutline(ac.WG, "wing");
    if (wg) {
      wings.push(wg);
      wings.push(mirrorY(wg));
    }
  }
  if (plotOn(ac, 1)) {
    const ht = planformOutline(ac.HT, "ht");
    if (ht) {
      wings.push(ht);
      wings.push(mirrorY(ht));
    }
  }
  if (plotOn(ac, 2)) {
    const vt = planformOutline(ac.VT, "vt");
    if (vt) wings.push(vt);
  }
  if (plotOn(ac, 3)) {
    fuselage.push(...fuselagePolylines(ac.BD));
  }
  return { fuselage, wings };
}

export function sceneFromConfig(ac: AircraftDict): SceneResult {
  try {
    return { ok: true, scene: tessellate(ac) };
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return { ok: false, message };
  }
}

export function keepLastGood(
  result: SceneResult,
  last: Scene | null,
): { scene: Scene | null; warning: string | null } {
  if (result.ok) return { scene: result.scene, warning: null };
  return { scene: last, warning: result.message };
}
