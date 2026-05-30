import { describe, expect, it, vi } from "vitest";

const cancelTaskMock = vi.fn().mockResolvedValue(undefined);
const stopMock = vi.fn();

vi.mock("../services/linguistApi", () => ({
  cancelTask: (...args: unknown[]) => cancelTaskMock(...args),
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
  it("cancelCurrentTask aborts locally then DELETEs backend task", async () => {
    stopMock.mockClear();
    cancelTaskMock.mockClear();

    const { cancelCurrentTask } = useTask();
    await cancelCurrentTask();

    expect(stopMock.mock.invocationCallOrder[0]).toBeLessThan(
      cancelTaskMock.mock.invocationCallOrder[0]!,
    );
    expect(cancelTaskMock).toHaveBeenCalledWith("task-99");
  });
});
