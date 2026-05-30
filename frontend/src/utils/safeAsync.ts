/**
 * 前端异步安全执行工具（开发规范 §3.1：async 必须 try/catch）。
 */

/** 将 unknown 异常转为可读字符串。 */
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * 执行异步函数并捕获异常；失败时调用 onError，避免未处理的 Promise rejection。
 * @returns 成功时返回 fn 的结果；失败时返回 undefined。
 */
export async function runSafe<T>(
  fn: () => Promise<T>,
  onError?: (message: string, error: unknown) => void,
): Promise<T | undefined> {
  try {
    return await fn();
  } catch (error) {
    const message = errorMessage(error);
    onError?.(message, error);
    console.error(message, error);
    return undefined;
  }
}

/**
 * 执行同步函数并捕获异常（DOM / JSON 等）。
 * @returns 成功时返回 fn 的结果；失败时返回 undefined。
 */
export function runSafeSync<T>(fn: () => T, onError?: (message: string, error: unknown) => void): T | undefined {
  try {
    return fn();
  } catch (error) {
    const message = errorMessage(error);
    onError?.(message, error);
    console.error(message, error);
    return undefined;
  }
}
