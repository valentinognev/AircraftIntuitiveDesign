import { useStore } from "zustand";
import {
  axisTicks,
  chartLayout,
  gridLines,
  overlaySeries,
  plotDomain,
  stabilityText,
  svgPolyline,
  type PlotSeries,
} from "./payload";
import store from "./store";

const LAYOUT = chartLayout();

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
  const { width, height, plot } = LAYOUT;
  const xTicks = domain ? axisTicks(domain.xmin, domain.xmax) : [];
  const yTicks = domain ? axisTicks(domain.ymin, domain.ymax) : [];
  const dx = domain ? domain.xmax - domain.xmin || 1 : 1;
  const dy = domain ? domain.ymax - domain.ymin || 1 : 1;
  const yOf = (value: number) => plot.y + plot.height - ((value - (domain?.ymin ?? 0)) / dy) * plot.height;
  const xOf = (value: number) => plot.x + ((value - (domain?.xmin ?? 0)) / dx) * plot.width;
  return (
    <figure className="min-w-0">
      <figcaption className="text-xs font-medium text-slate-600 dark:text-slate-300">
        {title}
      </figcaption>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="h-44 w-full text-slate-700 dark:text-slate-200"
        role="img"
        aria-label={`${title} (${ylabel})`}
      >
        {domain
          ? gridLines(domain, plot).map((line, i) => (
              <line
                key={i}
                x1={line.x1}
                y1={line.y1}
                x2={line.x2}
                y2={line.y2}
                stroke="currentColor"
                strokeOpacity={0.22}
              />
            ))
          : null}
        <rect
          x={plot.x}
          y={plot.y}
          width={plot.width}
          height={plot.height}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.7}
        />
        {yTicks.map((tick) => (
          <text
            key={`y-${tick.label}`}
            x={plot.x - 6}
            y={yOf(tick.value)}
            fill="currentColor"
            fontSize={12}
            textAnchor="end"
            dominantBaseline="middle"
          >
            {tick.label}
          </text>
        ))}
        {xTicks.map((tick) => (
          <text
            key={`x-${tick.label}`}
            x={xOf(tick.value)}
            y={plot.y + plot.height + 18}
            fill="currentColor"
            fontSize={12}
            textAnchor="middle"
          >
            {tick.label}
          </text>
        ))}
        <text
          x={plot.x + plot.width / 2}
          y={height - 8}
          fill="currentColor"
          fontSize={12}
          textAnchor="middle"
        >
          α (deg)
        </text>
        {domain
          ? series.map((s) => {
              const pts = svgPolyline(s.alpha, pick(s), width, height, 0, domain, plot);
              if (!pts) return null;
              return (
                <polyline
                  key={s.solver}
                  points={pts}
                  fill="none"
                  stroke={s.stroke}
                  strokeWidth={1.75}
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
