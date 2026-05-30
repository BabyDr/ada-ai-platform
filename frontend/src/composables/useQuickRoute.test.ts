import { createPinia, setActivePinia } from "pinia";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { detectQuickRouteTarget } from "./useQuickRoute";
import { useQuickTextPrefill } from "./useQuickTextPrefill";
import { useWorkspaceStore } from "../stores/workspace";

describe("detectQuickRouteTarget", () => {
  it("routes short plain text to translation", () => {
    expect(detectQuickRouteTarget("风格和他人个天人合一还一塌糊涂呢")).toBe("translation");
  });

  it("routes long text to summarization", () => {
    expect(detectQuickRouteTarget("a".repeat(251))).toBe("summarization");
  });

  it("routes keyword text to summarization", () => {
    expect(detectQuickRouteTarget("请帮我总结这段会议记录")).toBe("summarization");
  });
});

describe("useQuickTextPrefill", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    });
    setActivePinia(createPinia());
  });

  it("prefills target and clears previous output via onPrefill", async () => {
    const { effectScope } = await import("vue");
    const workspace = useWorkspaceStore();
    const inputText = ref("旧输入");
    const previousOutput = ref("旧总结结果");
    const onPrefill = vi.fn(() => {
      previousOutput.value = "";
    });

    const scope = effectScope();
    scope.run(() => useQuickTextPrefill(inputText, onPrefill));

    workspace.setQuickText("新的快捷文本");
    await Promise.resolve();

    expect(onPrefill).toHaveBeenCalledOnce();
    expect(previousOutput.value).toBe("");
    expect(inputText.value).toBe("新的快捷文本");
    expect(workspace.quickText).toBe("");

    scope.stop();
  });
});
