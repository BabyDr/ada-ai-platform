import type { NativeElements } from "@vue/runtime-dom";

declare global {
  namespace JSX {
    interface IntrinsicElements extends NativeElements {
      [elem: string]: unknown;
    }
  }
}

export {};
