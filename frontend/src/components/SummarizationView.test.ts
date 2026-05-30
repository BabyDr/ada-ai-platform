import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SummarizationView from "./SummarizationView.vue";

const submitTaskMock = vi.fn().mockResolvedValue(undefined);
const mockResult = ref("");
const mockIsStreaming = ref(false);

const buttonStub = {
  template: '<button type="button" @click="$emit(\'click\')"><slot name="icon" /><slot /></button>',
};

vi.mock("../composables/useTask", () => ({
  useTask: () => ({
    result: mockResult,
    isStreaming: mockIsStreaming,
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
    mockResult.value = "";
    mockIsStreaming.value = false;
  });

  it("shows structured summary after task completes instead of raw JSON", async () => {
    submitTaskMock.mockImplementation(
      async (_type: string, _params: unknown, handlers: { onDone?: (p: unknown) => void }) => {
        mockResult.value = '{"overview":"测试概述","keyPoints":["要点一","要点二","要点三"]}';
        handlers.onDone?.({
          status: "done",
          duration: "1.0s",
          result: {
            overview: "测试概述",
            keyPoints: ["要点一", "要点二", "要点三"],
          },
        });
      },
    );

    const wrapper = mount(SummarizationView, {
      global: {
        stubs: {
          ApiKeyBanner: true,
          StreamingBadge: true,
          TruncatedText: { template: "<span>{{ text }}</span>", props: ["text"] },
          "a-select": true,
          "a-button": buttonStub,
          AButton: buttonStub,
        },
      },
    });

    await wrapper.find("textarea").setValue("测试文档内容");
    const summarizeBtn = wrapper.findAll("button").find((b) => b.text().includes("生成总结"));
    await summarizeBtn!.trigger("click");
    await vi.waitFor(() => expect(wrapper.text()).toContain("测试概述"));
    expect(wrapper.text()).toContain("要点一");
    expect(wrapper.text()).not.toContain('"keyPoints"');
    expect(mockResult.value).toBe("");
  });

  it("submitTask passes summarize params with summaryMode, keyPointsCount, wordLimit, tone", async () => {
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
      summaryMode: "points",
      keyPointsCount: 5,
      wordLimit: 300,
      tone: "Professional",
    });
  });
});
