import { beforeEach, describe, expect, it, vi } from "vitest";
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
  beforeEach(() => {
    vi.clearAllMocks();
  });

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

  it("ignores duplicate start while streaming", async () => {
    let resolveFirst!: () => void;
    vi.mocked(createTaskSSE).mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveFirst = () =>
            resolve(sseResponse(['event: task_done\ndata: {"taskId":"t1","status":"done"}\n\n']));
        }),
    );

    const { startSSE, isStreaming } = useSSE();
    const first = startSSE({ type: "translate", params: { text: "x" } });
    await Promise.resolve();
    expect(isStreaming.value).toBe(true);
    await startSSE({ type: "translate", params: { text: "y" } });
    expect(createTaskSSE).toHaveBeenCalledTimes(1);
    resolveFirst();
    await first;
  });

  it("reports malformed SSE JSON via onError", async () => {
    vi.mocked(createTaskSSE).mockResolvedValue(
      sseResponse(['event: token\ndata: not-json\n\n']),
    );

    const onError = vi.fn();
    const { startSSE } = useSSE();
    await startSSE({ type: "translate", params: { text: "x" } }, { onError });

    expect(onError).toHaveBeenCalledWith("流式数据解析失败");
  });

  it("deduplicates token events by seq", async () => {
    vi.mocked(createTaskSSE).mockResolvedValue(
      sseResponse([
        'event: token\ndata: {"content":"A","seq":1}\n\n',
        'event: token\ndata: {"content":"A","seq":1}\n\n',
        'event: token\ndata: {"content":"B","seq":2}\n\n',
        'event: task_done\ndata: {"taskId":"t1","status":"done"}\n\n',
      ]),
    );

    const { result, startSSE } = useSSE();
    await startSSE({ type: "translate", params: { text: "x" } });

    expect(result.value).toBe("AB");
  });

  it("reports disconnect when stream ends without task_done", async () => {
    vi.mocked(createTaskSSE).mockResolvedValue(
      sseResponse(['event: token\ndata: {"content":"partial"}\n\n']),
    );

    const onError = vi.fn();
    const { error, startSSE } = useSSE();
    await startSSE({ type: "translate", params: { text: "x" } }, { onError });

    expect(error.value).toBe("连接已断开，请重新提交");
    expect(onError).toHaveBeenCalledWith("连接已断开，请重新提交");
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
