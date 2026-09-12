import { useRef } from "react";
import { useStore } from "zustand";
import store from "./store";
import { ThemeToggle } from "./ThemeToggle";

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

export function StartScreen() {
  const models = useStore(store, (s) => s.models);
  const modelsError = useStore(store, (s) => s.modelsError);
  const parseError = useStore(store, (s) => s.parseError);
  const recent = useStore(store, (s) => s.recent);
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <h1 className="text-2xl font-semibold">Aircraft Intuitive Design</h1>
      <div className="flex flex-wrap items-center justify-center gap-2">
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-4 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          onClick={() => store.getState().openNew()}
        >
          New
        </button>
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-4 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          onClick={() => fileRef.current?.click()}
        >
          Open file
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
      </div>
      {parseError ? (
        <p className="text-sm text-red-600 dark:text-red-400">{parseError.message}</p>
      ) : null}
      {modelsError ? (
        <p className="text-sm text-red-600 dark:text-red-400">{modelsError}</p>
      ) : null}
      {recent.length > 0 ? (
        <div className="w-full max-w-md">
          <h2 className="mb-1 text-sm font-semibold">Recent</h2>
          <ul className="space-y-1 text-sm">
            {recent.map((name) => (
              <li key={name}>
                <button
                  type="button"
                  className="w-full rounded bg-white px-3 py-1.5 text-left text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  onClick={() => void store.getState().openRecent(name)}
                >
                  {name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="w-full max-w-md">
        <h2 className="mb-1 text-sm font-semibold">Load examples</h2>
        {models == null && modelsError == null ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading examples…</p>
        ) : models != null && models.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No models.</p>
        ) : (
          <ul className="max-h-80 space-y-1 overflow-y-auto text-sm">
            {(models ?? []).map((name) => (
              <li key={name}>
                <button
                  type="button"
                  className="w-full rounded bg-white px-3 py-1.5 text-left text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  onClick={() => void store.getState().openExample(name)}
                >
                  {name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
