import { describe, expect, it, vi } from "vitest";
import { createStreamBuffer } from "./useStreamBuffer";

describe("createStreamBuffer", () => {
  it("flushes accumulated text on stop", () => {
    vi.useFakeTimers();
    const flushed: string[] = [];
    const buf = createStreamBuffer((c) => flushed.push(c), 16);

    buf.push("Hel");
    buf.push("lo");
    buf.stop();

    expect(flushed.join("")).toBe("Hello");
    vi.useRealTimers();
  });

  it("batches pushes within interval", () => {
    vi.useFakeTimers();
    const flushed: string[] = [];
    const buf = createStreamBuffer((c) => flushed.push(c), 16);

    buf.push("a");
    buf.push("b");
    vi.advanceTimersByTime(16);
    expect(flushed).toEqual(["ab"]);

    buf.stop();
    vi.useRealTimers();
  });
});
