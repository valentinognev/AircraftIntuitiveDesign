import { useStore } from "zustand";
import { NumInput } from "../Field";
import { CONTROL_BLOCKS, CONTROL_GRID_HEADERS, unitText } from "../fields";
import store from "../store";

export function ControlTab() {
  const aircraft = useStore(store, (s) => s.aircraft);
  const unit = aircraft?.unit ?? "ft";
  return (
    <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
      {CONTROL_BLOCKS.map(([prefix, title, _cmp, specs], bi) => {
        const group = (aircraft?.[prefix] ?? {}) as Record<string, unknown>;
        return (
          <section key={prefix}>
            <div className="grid grid-cols-[minmax(6rem,1fr)_1fr_1fr_3rem] items-center gap-2">
              <h3 className="text-sm font-semibold">{title}</h3>
              {CONTROL_GRID_HEADERS.map((h) => (
                <span
                  key={h}
                  className="text-center text-xs font-semibold text-slate-500 dark:text-slate-400"
                >
                  {h}
                </span>
              ))}
              <span />
              {specs.map(([left, right, label, kind]) => (
                <div key={`${prefix}.${left}`} className="contents">
                  <span className="text-right text-sm">{label}</span>
                  {right == null ? (
                    <div className="col-span-2">
                      <NumInput
                        value={group[left]}
                        ariaLabel={`${prefix}.${left}`}
                        onCommit={(v) => store.getState().setGroupField(prefix, left, v)}
                      />
                    </div>
                  ) : (
                    <>
                      <NumInput
                        value={group[left]}
                        ariaLabel={`${prefix}.${left}`}
                        onCommit={(v) => store.getState().setGroupField(prefix, left, v)}
                      />
                      <NumInput
                        value={group[right]}
                        ariaLabel={`${prefix}.${right}`}
                        onCommit={(v) => store.getState().setGroupField(prefix, right, v)}
                      />
                    </>
                  )}
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {unitText(kind, unit)}
                  </span>
                </div>
              ))}
            </div>
            {bi < CONTROL_BLOCKS.length - 1 ? (
              <hr className="my-3 border-slate-300 dark:border-slate-700" />
            ) : null}
          </section>
        );
      })}
    </form>
  );
}
