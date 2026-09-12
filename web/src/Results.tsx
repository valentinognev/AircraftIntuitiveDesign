import { useStore } from "zustand";
import { overlaySeries, plotDomain, stabilityText, svgPolyline, type PlotSeries } from "./payload";
import store from "./store";

const PLOT_W = 280;
const PLOT_H = 120;

function Chart({
  title,
  ylabel,
  series,
  pick,
}: {
  title: string;
  ylabel: string;
  series: PlotSeries[];
  pick: (s: PlotSeries) => number[];
}) {
  const domain = plotDomain(series, pick);
  return (
    <figure className="min-w-0">
      <figcaption className="text-xs font-medium text-slate-600 dark:text-slate-300">
        {title}
      </figcaption>
      <svg
        viewBox={`0 0 ${PLOT_W} ${PLOT_H}`}
        className="h-28 w-full text-slate-800 dark:text-slate-100"
        role="img"
        aria-label={title}
      >
        <text x="8" y="12" className="fill-current text-[9px]">
          {ylabel}
        </text>
        <text x={PLOT_W - 40} y={PLOT_H - 2} className="fill-current text-[9px]">
          α
        </text>
        {domain
          ? series.map((s) => {
              const pts = svgPolyline(s.alpha, pick(s), PLOT_W, PLOT_H, 8, domain);
              if (!pts) return null;
              return (
                <polyline
                  key={s.solver}
                  points={pts}
                  fill="none"
                  stroke={s.stroke}
                  strokeWidth={1.5}
                />
              );
            })
          : null}
      </svg>
    </figure>
  );
}

export function Results() {
  const lastPayload = useStore(store, (s) => s.lastPayload);
  const payloads = useStore(store, (s) => s.payloads);
  const lastStability = useStore(store, (s) => s.lastStability);
  const series = overlaySeries(
    lastPayload == null ? [] : Object.values(payloads).length ? Object.values(payloads) : [lastPayload],
  );
  const summary = stabilityText(lastStability);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-y-auto bg-white p-3 dark:bg-slate-900">
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
        Aerodynamics
      </div>
      {summary ? (
        <p className="mb-3 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{summary}</p>
      ) : (
        <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">Load an aircraft for CG / static margin.</p>
      )}
      {series.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Analyze to plot CL, CD, Cm vs α.</p>
      ) : (
        <div className="space-y-2">
          <Chart title="CL vs α" ylabel="CL" series={series} pick={(s) => s.cl} />
          <Chart title="CD vs α" ylabel="CD" series={series} pick={(s) => s.cd} />
          <Chart title="Cm vs α" ylabel="Cm" series={series} pick={(s) => s.cm} />
          <ul className="flex flex-wrap gap-3 text-xs">
            {series.map((s) => (
              <li key={s.solver} className="flex items-center gap-1">
                <span className="inline-block h-0.5 w-4" style={{ background: s.stroke === "currentColor" ? "currentColor" : s.stroke }} />
                {s.solver}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
