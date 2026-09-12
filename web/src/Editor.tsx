import { useEffect, useRef, useState } from "react";
import { useStore } from "zustand";
import { downloadAircraft, validateAircraft } from "./api";
import { VALIDATE_MS, debounce } from "./debounce";
import { AircraftCanvas } from "./AircraftCanvas";
import { extraTabs } from "./extras";
import { Results } from "./Results";
import store, { TABS, type TabId } from "./store";
import { ThemeToggle } from "./ThemeToggle";
import { AeroTab } from "./tabs/AeroTab";
import { BodyTab } from "./tabs/BodyTab";
import { ControlTab } from "./tabs/ControlTab";
import { ExtraOutlet, ExtraTab } from "./tabs/ExtraTab";
import { HTTab } from "./tabs/HTTab";
import { VTTab } from "./tabs/VTTab";
import { WingTab } from "./tabs/WingTab";

function FormOutlet({ tab }: { tab: TabId }) {
  switch (tab) {
    case "wing":
      return <WingTab />;
    case "ht":
      return <HTTab />;
    case "vt":
      return <VTTab />;
    case "control":
      return <ControlTab />;
    case "body":
      return <BodyTab />;
    case "aero":
      return <AeroTab />;
    case "geometry":
      return <AircraftCanvas />;
    case "plus":
      return <ExtraTab />;
    case "body2":
    case "body3":
    case "prop":
    case "wing2":
    case "ht2":
    case "vt2":
      return <ExtraOutlet tab={tab} />;
  }
}

function openLocalJsonc(file: File): void {
  const reader = new FileReader();
  reader.onload = () => {
    const text = typeof reader.result === "string" ? reader.result : "";
    store.getState().openJsoncText(text, file.name);
  };
  reader.onerror = () => {
    store.getState().applyParseFail("failed to read file");
  };
  reader.readAsText(file);
}

export function Editor() {
  const stem = useStore(store, (s) => s.stem);
  const aircraft = useStore(store, (s) => s.aircraft);
  const parseError = useStore(store, (s) => s.parseError);
  const validateError = useStore(store, (s) => s.validateError);
  const analyzeError = useStore(store, (s) => s.analyzeError);
  const handshakeError = useStore(store, (s) => s.handshakeError);
  const analyzing = useStore(store, (s) => s.analyzing);
  const tab = useStore(store, (s) => s.tab);
  const fileRef = useRef<HTMLInputElement>(null);
  const [solver, setSolver] = useState("datcom");

  useEffect(() => {
    const queued = debounce(() => {
      const { aircraft: ac, revision } = store.getState();
      if (ac == null) return;
      void validateAircraft(ac).then((result) => {
        if (store.getState().revision !== revision) return;
        store.getState().applyValidateResult(result);
      });
    }, VALIDATE_MS);
    return store.subscribe((state, prev) => {
      if (state.revision === prev.revision) return;
      queued();
    });
  }, []);

  return (
    <div className="flex h-full flex-col bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-900">
        <div className="mr-auto min-w-0 flex-1 pr-3">
          <h1 className="truncate text-lg font-semibold">AID</h1>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400" title={stem ?? ""}>
            {stem}
          </p>
          {parseError ? (
            <p className="truncate text-xs text-red-600 dark:text-red-400" title={parseError.message}>
              {parseError.message}
            </p>
          ) : null}
          {validateError ? (
            <p className="truncate text-xs text-red-600 dark:text-red-400" title={validateError.message}>
              {validateError.message}
            </p>
          ) : null}
          {analyzeError ? (
            <p className="truncate text-xs text-red-600 dark:text-red-400" title={analyzeError.message}>
              {analyzeError.message}
            </p>
          ) : null}
          {handshakeError ? (
            <p className="truncate text-xs text-red-600 dark:text-red-400" title={handshakeError}>
              {handshakeError}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-3 py-1 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          onClick={() => store.getState().goStart()}
        >
          File
        </button>
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-3 py-1 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          onClick={() => store.getState().openNew()}
        >
          New
        </button>
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-3 py-1 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          onClick={() => fileRef.current?.click()}
        >
          Open
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".jsonc,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (file) openLocalJsonc(file);
          }}
        />
        <ThemeToggle />
        <select
          className="rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          value={solver}
          onChange={(e) => setSolver(e.target.value)}
          aria-label="solver"
        >
          <option value="datcom">DATCOM</option>
          <option value="tornado">Tornado</option>
          <option value="avl">AVL</option>
          <option value="flow5">flow5</option>
        </select>
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-3 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          disabled={aircraft == null || analyzing}
          onClick={() => {
            void store.getState().runAnalyze(solver);
          }}
        >
          Analyze
        </button>
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-3 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          disabled={aircraft == null}
          onClick={() => {
            if (aircraft == null) return;
            downloadAircraft(aircraft, stem ?? "aircraft");
          }}
        >
          Save
        </button>
      </header>
      <div className="flex min-h-0 flex-1">
        <nav className="w-48 shrink-0 overflow-y-auto border-r border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900">
          <ul className="space-y-1 text-sm">
            {[...TABS, ...extraTabs(aircraft)].map((item) => {
              const active = tab === item.id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`w-full rounded px-2 py-1 text-left ${
                      active
                        ? "bg-slate-800 text-white dark:bg-slate-100 dark:text-slate-900"
                        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                    }`}
                    onClick={() => store.getState().setTab(item.id)}
                  >
                    {item.label}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>
        {tab === "geometry" ? (
          <main className="min-h-0 min-w-0 flex-1">
            <AircraftCanvas />
          </main>
        ) : (
          <>
            <main className="min-w-0 flex-1 overflow-y-auto p-4">
              {aircraft == null && parseError != null ? (
                <p className="text-sm text-red-600 dark:text-red-400">{parseError.message}</p>
              ) : aircraft == null ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
              ) : (
                <FormOutlet tab={tab} />
              )}
            </main>
            <aside className="min-h-0 w-[42%] min-w-[16rem] shrink-0 border-l border-slate-200 dark:border-slate-800">
              {tab === "aero" ? <Results /> : <AircraftCanvas />}
            </aside>
          </>
        )}
      </div>
    </div>
  );
}
