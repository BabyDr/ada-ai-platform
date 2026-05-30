import { describe, expect, it, vi } from "vitest";
import { useSSE } from "./useSSE";

vi.mock("../services/linguistApi", () => ({
  createTaskSSE: vi.fn(),
}));

import { createTaskSSE } from "../services/linguistApi";

function sseResponse(chunks: string[]): Response {
  let i = 0;
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (i >= chunks.length) {
        controller.close();
        return;
      }
      controller.enqueue(new TextEncoder().encode(chunks[i++]));
    },
  });
  return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

describe("useSSE", () => {
  it("accumulates token content into result", async () => {
    vi.mocked(createTaskSSE).mockResolvedValue(
      sseResponse([
        'event: task_start\ndata: {"taskId":"t1"}\n\n',
        'event: token\ndata: {"content":"Hel"}\n\n',
        'event: token\ndata: {"content":"lo"}\n\n',
        'event: task_done\ndata: {"taskId":"t1","status":"done"}\n\n',
      ]),
    );

    const { result, startSSE, currentTaskId } = useSSE();
    await startSSE({ type: "translate", params: { text: "x" } });

    expect(result.value).toBe("Hello");
    expect(currentTaskId.value).toBe("t1");
  });

  it("stop() aborts without setting error", async () => {
    vi.mocked(createTaskSSE).mockImplementation((_body, sig) =>
      new Promise((_resolve, reject) => {
        sig?.addEventListener("abort", () => {
          reject(new DOMException("The operation was aborted", "AbortError"));
        });
      }),
    );

    const { error, isStreaming, startSSE, stop } = useSSE();
    const pending = startSSE({ type: "translate", params: { text: "x" } });
    await Promise.resolve();
    stop();
    await pending;

    expect(error.value).toBe("");
    expect(isStreaming.value).toBe(false);
  });
});
