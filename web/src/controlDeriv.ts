const COEFFS = ["CL", "CD", "Cm", "CY", "Cl", "Cn"] as const;

export type ControlCoeff = (typeof COEFFS)[number];

export type ControlDerivRow = {
  surface: string;
  delta_deg: number;
  available: boolean;
  reason?: string;
} & Record<ControlCoeff, number | null>;

export type ControlDerivPayload = {
  solver: string;
  deltas_deg: number[];
  rows: ControlDerivRow[];
};

export type ControlChartSeries = {
  id: string;
  xs: number[];
  ys: number[];
};

/** Finite coefficients grouped by surface and name. Null and unavailable rows are omitted. */
export function chartRows(payload: ControlDerivPayload): ControlChartSeries[] {
  const grouped = new Map<string, ControlChartSeries>();
  for (const row of payload.rows) {
    if (row.available === false) continue;
    for (const name of COEFFS) {
      const value = row[name];
      if (value == null || !Number.isFinite(value)) continue;
      const id = `${payload.solver}-${row.surface}-${name}`;
      let series = grouped.get(id);
      if (series == null) {
        series = { id, xs: [], ys: [] };
        grouped.set(id, series);
      }
      series.xs.push(row.delta_deg);
      series.ys.push(value);
    }
  }
  return [...grouped.values()];
}
