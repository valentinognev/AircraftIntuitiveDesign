import { useStore } from "zustand";
import { NumField, NumInput } from "../Field";
import { EXTRA_BODY_STATION_ROWS, BODY_STATION_KEYS, PLANFORM_BREAKS, PLANFORM_RP, unitText } from "../fields";
import { PLUS_PARTS, hiddenPlusButtons, type ExtraTabId } from "../extras";
import store from "../store";

function ExtraPlanformTab({
  slot,
  cmpIndex,
  title,
}: {
  slot: number;
  cmpIndex: number;
  title: string;
}) {
  const aircraft = useStore(store, (s) => s.aircraft);
  const group = (aircraft?.NP?.[slot] ?? {}) as Record<string, unknown>;
  const unit = aircraft?.unit ?? "ft";
  const plotOn = Number(aircraft?.plot_cmp?.[cmpIndex] ?? 1) !== 0;
  return (
    <form className="space-y-1" onSubmit={(e) => e.preventDefault()}>
      {PLANFORM_RP.map(([field, label, kind], i) => (
        <div key={field}>
          <NumField
            label={label}
            value={group[field]}
            unit={unitText(kind, unit)}
            checkbox={
              i === 0 ? (
                <input
                  type="checkbox"
                  checked={plotOn}
                  onChange={(e) => store.getState().setPlotCmp(cmpIndex, e.target.checked)}
                  aria-label={`${title} visible`}
                />
              ) : undefined
            }
            onCommit={(v) => store.getState().setSlotField("NP", slot, field, v)}
          />
          {PLANFORM_BREAKS.includes((i + 1) as (typeof PLANFORM_BREAKS)[number]) ? (
            <hr className="my-2 border-slate-300 dark:border-slate-700" />
          ) : null}
        </div>
      ))}
    </form>
  );
}

function ExtraBodyTab({
  slot,
  cmpIndex,
  title,
}: {
  slot: number;
  cmpIndex: number;
  title: string;
}) {
  const aircraft = useStore(store, (s) => s.aircraft);
  const group = (aircraft?.NB?.[slot] ?? {}) as Record<string, unknown>;
  const unit = aircraft?.unit ?? "ft";
  const plotOn = Number(aircraft?.plot_cmp?.[cmpIndex] ?? 1) !== 0;
  const arrays = {
    N: Array.isArray(group.N) ? group.N : [],
    X: Array.isArray(group.X) ? group.X : [],
    P: Array.isArray(group.P) ? group.P : [],
  };
  return (
    <form className="space-y-2" onSubmit={(e) => e.preventDefault()}>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={plotOn}
          onChange={(e) => store.getState().setPlotCmp(cmpIndex, e.target.checked)}
          aria-label={`${title} visible`}
        />
        {title}
      </label>
      <div className="grid grid-cols-3 gap-2 text-center text-xs font-semibold text-slate-500 dark:text-slate-400">
        <span>Station</span>
        <span>{unitText("pos_hdr", unit)}</span>
        <span>Shape</span>
      </div>
      {Array.from({ length: EXTRA_BODY_STATION_ROWS }, (_, i) => (
        <div key={i} className="grid grid-cols-3 gap-2">
          {BODY_STATION_KEYS.map((key) => (
            <NumInput
              key={key}
              value={arrays[key][i]}
              ariaLabel={`NB[${slot}].${key}[${i}]`}
              onCommit={(v) => store.getState().setSlotArrayField("NB", slot, key, i, v)}
            />
          ))}
        </div>
      ))}
      {(["X0", "Y0", "Z0"] as const).map((field, i) => (
        <NumField
          key={field}
          label={`Position, ${["X", "Y", "Z"][i]}`}
          value={group[field]}
          unit={unitText("len", unit)}
          onCommit={(v) => store.getState().setSlotField("NB", slot, field, v)}
        />
      ))}
    </form>
  );
}

export function ExtraOutlet({ tab }: { tab: ExtraTabId }) {
  switch (tab) {
    case "body2":
      return <ExtraBodyTab slot={0} cmpIndex={8} title="Body 2" />;
    case "body3":
      return <ExtraBodyTab slot={1} cmpIndex={9} title="Body 3" />;
    case "prop":
      return <ExtraPlanformTab slot={3} cmpIndex={7} title="Prop" />;
    case "wing2":
      return <ExtraPlanformTab slot={0} cmpIndex={4} title="Wing 2" />;
    case "ht2":
      return <ExtraPlanformTab slot={1} cmpIndex={5} title="HT 2" />;
    case "vt2":
      return <ExtraPlanformTab slot={2} cmpIndex={6} title="VT 2" />;
  }
}

export function ExtraTab() {
  const aircraft = useStore(store, (s) => s.aircraft);
  const hidden = hiddenPlusButtons(aircraft);
  return (
    <div className="space-y-3 p-1">
      <p className="text-sm">Choose a Component to Add:</p>
      {PLUS_PARTS.map((name, i) =>
        hidden.includes(name) ? null : (
          <button
            key={name}
            type="button"
            className="block w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            onClick={() => store.getState().addPart(i + 1)}
          >
            {name}
          </button>
        ),
      )}
    </div>
  );
}
