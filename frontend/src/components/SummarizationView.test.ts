import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SummarizationView from "./SummarizationView.vue";

const submitTaskMock = vi.fn().mockResolvedValue(undefined);

const buttonStub = {
  template: '<button type="button" @click="$emit(\'click\')"><slot name="icon" /><slot /></button>',
};

vi.mock("../composables/useTask", () => ({
  useTask: () => ({
    result: ref(""),
    isStreaming: ref(false),
    error: ref(""),
    submitTask: submitTaskMock,
    cancelCurrentTask: vi.fn(),
  }),
}));

vi.mock("../composables/useQuickTextPrefill", () => ({
  useQuickTextPrefill: () => {},
}));

vi.mock("../composables/useTaskRecovery", () => ({
  recoverPersistedTask: vi.fn().mockResolvedValue(""),
}));

vi.mock("../composables/useLinguistTaskLog", () => ({
  createProcessingLog: vi.fn().mockResolvedValue({ id: "log-1" }),
  buildLinguistLogCallbacks: vi.fn().mockReturnValue({ onDone: vi.fn(), onError: vi.fn() }),
}));

vi.mock("../composables/useFileImport", () => ({
  useFileImport: () => ({
    dragActive: { value: false },
    fileInputRef: { value: null },
    triggerFileSelect: vi.fn(),
    handleFileChoose: vi.fn(),
    handleDragOver: vi.fn(),
    handleDragLeave: vi.fn(),
    handleDrop: vi.fn(),
  }),
}));

vi.mock("../utils/safeAsync", () => ({
  runSafe: (fn: () => Promise<void>) => fn(),
}));

describe("SummarizationView", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    });
    setActivePinia(createPinia());
    submitTaskMock.mockClear();
  });

  it("submitTask passes summarize params with keyPointsCount, wordLimit, tone", async () => {
    const wrapper = mount(SummarizationView, {
      global: {
        stubs: {
          ApiKeyBanner: true,
          StreamingBadge: true,
          TruncatedText: true,
          "a-select": true,
          "a-button": buttonStub,
          AButton: buttonStub,
        },
      },
    });

    await wrapper.find("textarea").setValue(
      "Meeting notes about quarterly goals and team updates.",
    );

    await wrapper.find('input[type="range"][min="50"]').setValue("300");
    await wrapper.find('input[type="range"][min="3"]').setValue("5");

    const summarizeBtn = wrapper
      .findAll("button")
      .find((b) => b.text().includes("生成总结"));
    expect(summarizeBtn).toBeTruthy();
    await summarizeBtn!.trigger("click");
    await vi.waitFor(() => expect(submitTaskMock).toHaveBeenCalled());

    const [type, params] = submitTaskMock.mock.calls[0]!;
    expect(type).toBe("summarize");
    expect(params).toMatchObject({
      text: "Meeting notes about quarterly goals and team updates.",
      keyPointsCount: 5,
      wordLimit: 300,
      tone: "Professional",
    });
  });
});
