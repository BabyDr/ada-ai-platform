import { describe, expect, it } from "vitest";
import { randomRequestId, randomUUID } from "./randomId";

describe("randomId", () => {
  it("randomUUID returns a v4-shaped string", () => {
    const id = randomUUID();
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    );
  });

  it("randomRequestId returns 16 hex chars", () => {
    expect(randomRequestId()).toMatch(/^[0-9a-f]{16}$/i);
  });

  it("falls back when crypto.randomUUID is missing", () => {
    const original = globalThis.crypto?.randomUUID;
    if (globalThis.crypto) {
      // @ts-expect-error test stub
      globalThis.crypto.randomUUID = undefined;
    }
    try {
      expect(randomUUID()).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
      );
    } finally {
      if (globalThis.crypto && original) {
        globalThis.crypto.randomUUID = original;
      }
    }
  });
});
