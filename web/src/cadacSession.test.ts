import { afterEach, expect, it, vi } from "vitest";
import { cadacCallbackUrl, openNewIfCadacSession } from "./cadacSession";
import { createStore } from "./store";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("builds CADAC complete URL from cadacSession query", () => {
  vi.stubGlobal("location", { search: "?cadacSession=sess-1" });
  expect(cadacCallbackUrl()).toBe(
    "http://127.0.0.1:8001/handshake/sessions/sess-1/complete",
  );
});

it("returns null when cadacSession query is absent", () => {
  vi.stubGlobal("location", { search: "" });
  expect(cadacCallbackUrl()).toBeNull();
});

it("returns null when cadacSession is empty", () => {
  vi.stubGlobal("location", { search: "?cadacSession=" });
  expect(cadacCallbackUrl()).toBeNull();
});

it("opens New (editor) when cadacSession is non-empty", () => {
  vi.stubGlobal("location", { search: "?cadacSession=sess-1" });
  const store = createStore();
  openNewIfCadacSession(() => store.getState().openNew());
  expect(store.getState().view).toBe("editor");
  expect(store.getState().stem).toBe("untitled");
  expect(store.getState().aircraft).not.toBeNull();
});

it("stays on start when cadacSession is absent", () => {
  vi.stubGlobal("location", { search: "" });
  const store = createStore();
  openNewIfCadacSession(() => store.getState().openNew());
  expect(store.getState().view).toBe("start");
  expect(store.getState().aircraft).toBeNull();
});
