import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useWorkspaceStore } from "./workspace";

function mockLocalStorage() {
  const store: Record<string, string> = {};
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => {
      store[k] = v;
    },
    removeItem: (k: string) => {
      delete store[k];
    },
    clear: () => {
      for (const k of Object.keys(store)) delete store[k];
    },
  });
}

describe("useWorkspaceStore", () => {
  beforeEach(() => {
    mockLocalStorage();
    setActivePinia(createPinia());
  });

  it("setQuickText updates quickText", () => {
    const store = useWorkspaceStore();
    store.setQuickText("hello from dashboard");
    expect(store.quickText).toBe("hello from dashboard");
  });

  it("toggleTheme persists to localStorage", () => {
    const store = useWorkspaceStore();
    const initial = store.isDark;
    store.toggleTheme();
    expect(store.isDark).toBe(!initial);
    expect(localStorage.getItem("adaagent-dark")).toBe(String(!initial));
  });
});
