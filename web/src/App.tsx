import { useEffect } from "react";
import { useStore } from "zustand";
import { fetchModels } from "./api";
import { openNewIfCadacSession } from "./cadacSession";
import { Editor } from "./Editor";
import { StartScreen } from "./StartScreen";
import store from "./store";

async function loadModelsInto(): Promise<void> {
  try {
    const names = await fetchModels();
    store.getState().setModels(names);
  } catch {
    store.getState().setModelsError("API unreachable");
  }
}

export default function App() {
  const view = useStore(store, (s) => s.view);

  useEffect(() => {
    void loadModelsInto();
    openNewIfCadacSession(() => store.getState().openNew());
  }, []);

  if (view === "start") {
    return <StartScreen />;
  }

  return <Editor />;
}
