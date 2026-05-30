/**
 * 16ms 流式渲染缓冲（#3 / #15）：批量 flush 减少 Vue 重渲染次数。
 */
export function createStreamBuffer(flushFn: (chunk: string) => void, intervalMs = 16) {
  let pending = "";
  let timer: ReturnType<typeof setInterval> | null = null;

  function flush() {
    if (!pending) return;
    const chunk = pending;
    pending = "";
    flushFn(chunk);
  }

  function push(text: string) {
    pending += text;
    if (timer === null) {
      timer = setInterval(flush, intervalMs);
    }
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
    flush();
  }

  return { push, stop, flush };
}
