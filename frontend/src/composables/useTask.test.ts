import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

const cancelTaskMock = vi.fn().mockResolvedValue(undefined);
const stopMock = vi.fn();

vi.mock("../services/linguistApi", () => ({
  cancelTask: (...args: unknown[]) => cancelTaskMock(...args),
  fetchHealth: vi.fn().mockResolvedValue({ status: "ok" }),
}));

vi.mock("./useSSE", () => ({
  useSSE: () => ({
    result: { value: "" },
    isStreaming: { value: false },
    error: { value: "" },
    currentTaskId: { value: "task-99" },
    startSSE: vi.fn().mockResolvedValue(undefined),
    stop: stopMock,
  }),
}));

import { useTask } from "./useTask";

describe("useTask", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    });
    setActivePinia(createPinia());
    stopMock.mockClear();
    cancelTaskMock.mockClear();
  });

  it("cancelCurrentTask aborts locally then DELETEs backend task", async () => {
    const { cancelCurrentTask } = useTask();
    await cancelCurrentTask();

    expect(stopMock.mock.invocationCallOrder[0]).toBeLessThan(
      cancelTaskMock.mock.invocationCallOrder[0]!,
    );
    expect(cancelTaskMock).toHaveBeenCalledWith("task-99");
  });
});
