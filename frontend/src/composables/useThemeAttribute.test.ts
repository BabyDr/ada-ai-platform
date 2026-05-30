import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { ref } from "vue";
import { useThemeAttribute } from "./useThemeAttribute";

describe("useThemeAttribute", () => {
  beforeEach(() => {
    document.documentElement.removeAttribute("data-theme");
  });

  afterEach(() => {
    document.documentElement.removeAttribute("data-theme");
  });

  it("sets data-theme from isDark and updates on toggle", async () => {
    const isDark = ref(true);
    useThemeAttribute(isDark);
    expect(document.documentElement.dataset.theme).toBe("dark");

    isDark.value = false;
    await Promise.resolve();
    expect(document.documentElement.dataset.theme).toBe("light");
  });
});
