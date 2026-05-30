import { afterEach, describe, expect, it, vi } from "vitest";
import { cancelTask, createTaskSSE, getFunctions } from "./linguistApi";

describe("linguistApi SSE endpoints", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("getFunctions calls /functions", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ functions: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getFunctions();

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(String(fetchMock.mock.calls[0][0])).toContain("/functions");
  });

  it("createTaskSSE calls POST /task", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body: null });
    vi.stubGlobal("fetch", fetchMock);

    await createTaskSSE({ type: "translate", params: { text: "hi" } });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/task");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({
      type: "translate",
      params: { text: "hi" },
    });
  });

  it("cancelTask calls DELETE /task/{id}", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await cancelTask("task-abc");

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/task/task-abc");
    expect(init?.method).toBe("DELETE");
  });
});
