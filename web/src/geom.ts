import type { AircraftDict } from "./aircraft";

export class GeometryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GeometryError";
  }
}

export type Vec3 = { x: number; y: number; z: number };
export type Polyline = Vec3[];
/** Spanwise rows of an airfoil loft. `rows[span][chord]`. */
export type SurfaceGrid = { name: string; rows: Vec3[][] };
export type Tessellation = { fuselage: Polyline[]; wings: SurfaceGrid[] };
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

/** Quarter-chord fraction used by Plot_Planform / aid.viz._loft. */
const CHORD_REF = 0.25;
const SPAN_COUNT = 9;
const NP_KINDS = ["wing 2", "ht 2", "vt 2", "prop"] as const;

function linspace(a: number, b: number, n: number): number[] {
  if (n <= 1) return [b];
  const out: number[] = [];
  for (let i = 0; i < n; i++) out.push(a + ((b - a) * i) / (n - 1));
  return out;
}

function tand(deg: number): number {
  return Math.tan(rad(deg));
}

function naca4(tc: number): number[][] {
  const n = 16;
  const yt = (x: number) => {
    if (x <= 0) return 0;
    return (
      5 *
      tc *
      (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1015 * x ** 4)
    );
  };
  const pts: number[][] = [];
  for (let i = n; i >= 0; i--) pts.push([i / n, -yt(i / n)]);
  for (let i = 1; i <= n; i++) pts.push([i / n, yt(i / n)]);
  return pts;
}

function asAirfoils(data: unknown): number[][][] {
  if (!Array.isArray(data) || data.length === 0) return [];
  const first = data[0];
  if (!Array.isArray(first)) return [];
  if (Array.isArray(first[0])) {
    return data.map((foil) =>
      (foil as unknown[]).map((row) => {
        const pair = row as unknown[];
        return [num(pair[0]), num(pair[1])];
      }),
    );
  }
  return [
    data.map((row) => {
      const pair = row as unknown[];
      return [num(pair[0]), num(pair[1])];
    }),
  ];
}

type Station = { y: number; c: number; dx: number; dz: number; theta: number };

function stations(pt: Record<string, unknown>, kind: string): Station[] {
  const y0 = num(pt.Y);
  const z0 = num(pt.Z);
  const x0 = num(pt.X);
  const chrdr = num(pt.CHRDR);
  const chrdtp = num(pt.CHRDTP) || chrdr;
  const chrdbp = num(pt.CHRDBP);
  const sspn = num(pt.SSPN);
  if (sspn < 0) throw new GeometryError("SSPN must be >= 0");
  if (chrdr < 0) throw new GeometryError("CHRDR must be >= 0");
  if (sspn === 0 || chrdr === 0) return [];
  const sspnop = num(pt.SSPNOP);
  const savsi = num(pt.SAVSI);
  const savso = num(pt.SAVSO);
  const chstat = num(pt.CHSTAT);
  const dhdadi = num(pt.DHDADI);
  const dhdado = num(pt.DHDADO);
  const inc = num(pt.i);
  const twista = num(pt.TWISTA);

  let y: number[] = [];
  let c: number[] = [];
  let dx: number[] = [];
  let dz: number[] = [];

  if (chrdbp && sspnop) {
    let yBreak = sspnop * Math.cos(rad(dhdadi));
    if (kind === "prop") yBreak *= Math.cos(rad(savsi));
    const n1 = Math.max(2, Math.round((SPAN_COUNT * Math.abs(yBreak)) / sspn) || 2);
    const y1 = linspace(0, yBreak, n1).map((v) => y0 + v);
    const span1 = y1[y1.length - 1] - y0 || 1;
    const c1 = y1.map((yy) => chrdr + ((yy - y0) / span1) * (chrdbp - chrdr));
    const dx1 = y1.map((yy) => x0 + (yy - y0) * tand(savsi) + chstat * (chrdr - chrdbp) * ((yy - y0) / span1));
    const dz1 = y1.map((yy) => z0 + (yy - y0) * tand(dhdadi));
    let yOut = yBreak + (sspn - sspnop) * Math.cos(rad(dhdado));
    if (kind === "prop") yOut = yBreak + (yOut - yBreak) * Math.cos(rad(savso));
    const n2 = Math.max(2, SPAN_COUNT - n1);
    const y2 = linspace(yBreak, yOut, n2).map((v) => y0 + v);
    const span2 = y2[y2.length - 1] - y2[0] || 1;
    const c2 = y2.map((yy) => chrdbp + ((yy - y2[0]) / span2) * (chrdtp - chrdbp));
    const dx2 = y2.map(
      (yy) => dx1[dx1.length - 1] + (yy - y2[0]) * tand(savso) + chstat * (chrdbp - chrdtp) * ((yy - y2[0]) / span2),
    );
    const dz2 = y2.map((yy) => dz1[dz1.length - 1] + (yy - y2[0]) * tand(dhdado));
    y = y1.concat(y2);
    c = c1.concat(c2);
    dx = dx1.concat(dx2);
    dz = dz1.concat(dz2);
  } else {
    let yOut = sspn * Math.cos(rad(dhdadi));
    if (kind === "prop") yOut *= Math.cos(rad(savsi));
    y = linspace(0, yOut, SPAN_COUNT).map((v) => y0 + v);
    const span = y[y.length - 1] - y0;
    c = y.map((yy) => chrdr + (span ? (yy - y0) / span : 0) * (chrdtp - chrdr));
    dx = y.map((yy) => {
      const frac = span ? (yy - y0) / span : 0;
      return x0 + (yy - y0) * tand(savsi) + chstat * (chrdr - chrdtp) * frac;
    });
    dz = y.map((yy) => z0 + (yy - y0) * tand(dhdadi));
  }

  const span = y[y.length - 1] - y0;
  return y.map((yy, i) => {
    const frac = span ? (yy - y0) / span : 0;
    const theta = inc - frac * twista;
    const chord = c[i];
    return {
      y: yy,
      c: chord * Math.cos(rad(theta)),
      dx: dx[i] + CHORD_REF * chord,
      dz: dz[i],
      theta,
    };
  });
}

function foilAt(foils: number[][][], t: number): number[][] {
  if (foils.length < 2) return foils[0];
  const a = foils[0];
  const b = foils[1];
  const n = Math.min(a.length, b.length);
  const out: number[][] = [];
  for (let i = 0; i < n; i++) {
    out.push([a[i][0] * (1 - t) + b[i][0] * t, a[i][1] * (1 - t) + b[i][1] * t]);
  }
  return out;
}

function loftFrame(pt: Record<string, unknown>, kind: string): Vec3[][] | null {
  const framePt: Record<string, unknown> =
    kind.includes("vt") || kind === "prop" ? { ...pt, Y: num(pt.Z), Z: num(pt.Y) } : pt;
  const st = stations(framePt, kind);
  if (st.length < 2) return null;
  let foils = asAirfoils(pt.DATA);
  if (foils.length === 0 || foils[0].length < 2) foils = [naca4(num(pt.TC) || 0.12)];
  const y0 = st[0].y;
  const y1 = st[st.length - 1].y;
  return st.map((s) => {
    const t = y1 !== y0 ? (s.y - y0) / (y1 - y0) : 0;
    const tanT = Math.tan(rad(s.theta));
    return foilAt(foils, t).map(([x, z]) => ({
      x: (x - CHORD_REF) * s.c + s.dx,
      y: s.y,
      z: z * s.c + s.dz + (CHORD_REF - x) * tanT * s.c,
    }));
  });
}

function mirrorRows(rows: Vec3[][]): Vec3[][] {
  return rows.map((row) => row.map((p) => ({ ...p, y: -p.y })));
}

function gridsFor(pt: Record<string, unknown>, kind: string): SurfaceGrid[] {
  const frame = loftFrame(pt, kind);
  if (!frame) return [];
  if (kind === "prop") {
    const px = num(pt.X);
    const pz = num(pt.Y);
    const py = num(pt.Z);
    const chrdr = num(pt.CHRDR);
    const blade = (sign: 1 | -1): Vec3[][] =>
      frame.map((row) =>
        row.map((p) =>
          sign === 1
            ? { x: p.z + px - pz, y: p.x - px + pz - chrdr / 2, z: p.y }
            : { x: p.z + px - pz, y: -p.x + px + pz + chrdr / 2, z: -p.y + 2 * py },
        ),
      );
    return [
      { name: "prop", rows: blade(1) },
      { name: "prop", rows: blade(-1) },
    ];
  }
  if (kind.includes("vt")) {
    const world = frame.map((row) => row.map((p) => ({ x: p.x, y: p.z, z: p.y })));
    const out: SurfaceGrid[] = [{ name: kind, rows: world }];
    if (num(pt.Y) || num(pt.DHDADI) || num(pt.DHDADO)) {
      out.push({ name: kind, rows: mirrorRows(world) });
    }
    return out;
  }
  return [
    { name: kind, rows: frame },
    { name: kind, rows: mirrorRows(frame) },
  ];
}

/** Angular samples around a body station. Multiple of 4 so superellipses close. */
const BODY_SAMPLES = 32;

function sectionRing(
  x: number,
  half: number,
  zc: number,
  h: number,
  power: number,
  superellipse: boolean,
): Polyline {
  const ring: Polyline = [];
  if (!superellipse) {
    for (let k = 0; k < BODY_SAMPLES; k++) {
      const theta = (2 * Math.PI * k) / BODY_SAMPLES;
      ring.push({ x, y: half * Math.cos(theta), z: zc + h * Math.sin(theta) });
    }
    return ring;
  }
  const q = BODY_SAMPLES / 4;
  const exp = 2 / 2 ** power;
  const cos: number[] = [];
  const sin: number[] = [];
  for (let k = 0; k < q; k++) {
    const theta = (Math.PI / 2) * (k / (q - 1));
    cos.push(Math.cos(theta) ** exp);
    sin.push(Math.sin(theta) ** exp);
  }
  const yQuad = [-1, 1, 1, -1];
  const zSign = [1, 1, -1, -1];
  const flip = [false, true, false, true];
  for (let quad = 0; quad < 4; quad++) {
    for (let k = 0; k < q; k++) {
      const j = flip[quad] ? q - 1 - k : k;
      ring.push({
        x,
        y: yQuad[quad] * half * cos[j],
        z: zc + zSign[quad] * h * sin[j],
      });
    }
  }
  return ring;
}

function fuselageRings(bd: Record<string, unknown>): Polyline[] {
  const nx = Math.max(0, Math.floor(num(bd.NX, 0)));
  const xs = finiteList(bd.X, nx || (Array.isArray(bd.X) ? bd.X.length : 0));
  const n = xs.length;
  if (n < 2) return [];
  const zu = finiteList(bd.ZU, n);
  const zl = finiteList(bd.ZL, n);
  const r = finiteList(bd.R, n);
  const pListed = Array.isArray(bd.P) ? finiteList(bd.P, n) : [];
  const p = pListed.length < n ? Array<number>(n).fill(1) : pListed;
  const superellipse = p.some((v) => v !== 1);
  const rings: Polyline[] = [];
  for (let i = 0; i < n; i++) {
    const u = zu[i] ?? 0;
    const l = zl[i] ?? 0;
    const zc = (u + l) / 2;
    rings.push(sectionRing(xs[i], r[i] ?? 0, zc, u - zc, p[i] ?? 1, superellipse));
  }
  return rings;
}

export function tessellate(ac: AircraftDict): Tessellation {
  const fuselage: Polyline[] = [];
  const wings: SurfaceGrid[] = [];
  if (plotOn(ac, 0)) wings.push(...gridsFor(ac.WG, "wing"));
  if (plotOn(ac, 1)) wings.push(...gridsFor(ac.HT, "ht"));
  if (plotOn(ac, 2)) wings.push(...gridsFor(ac.VT, "vt"));
  if (plotOn(ac, 3)) fuselage.push(...fuselageRings(ac.BD));
  ac.NP.forEach((slot, i) => {
    if (slot == null || typeof slot !== "object") return;
    if (!plotOn(ac, 4 + i)) return;
    wings.push(...gridsFor(slot as Record<string, unknown>, NP_KINDS[i] ?? "wing 2"));
  });
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
