/**
 * 启动 Python Sidecar（FastAPI / Uvicorn）。
 *
 * 为何用 Node 脚本包一层？
 * - 统一从「仓库根」执行 `npm run sidecar`，自动切到 backend 目录；
 * - 优先使用 backend/.venv 里的 Python，避免机器全局版本不一致。
 *
 * 对应 npm 脚本：根 package.json 里的 `"sidecar": "node scripts/sidecar.mjs"`。
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// 本文件在 scripts/ 下，上一级即仓库根 AdaAgent/
const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const pyDir = path.join(root, "backend");
const isWin = process.platform === "win32";
const venvPy = path.join(pyDir, ".venv", isWin ? "Scripts/python.exe" : "bin/python");

// 有虚拟环境就用 .venv，否则退回系统 python3（或 Windows 的 py 启动器）。
const exe = fs.existsSync(venvPy) ? venvPy : isWin ? "py" : "python3";
// uvicorn 加载 adaagent.main:app 即 FastAPI 实例；端口与前端 .env.development 中 VITE_* 一致。
const args = ["-m", "uvicorn", "adaagent.main:app", "--host", "127.0.0.1", "--port", "18765"];

const child = spawn(exe, args, {
  cwd: pyDir,
  stdio: "inherit",
  shell: false,
});
child.on("exit", (code) => process.exit(code ?? 0));
