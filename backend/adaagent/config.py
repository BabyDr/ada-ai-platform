"""
应用配置（pydantic-settings）。

仅承载 SSE 任务管线相关的开关：
- `llm_mode`：mock | real。real 模式复用现有 GLM 流式（密钥沿用 GLM_API_KEY/ZHIPU_API_KEY）。
- `task_timeout_seconds`：单任务超时时间，防止模型调用挂死。

环境变量经 bootstrap_env.load_app_dotenv() 注入到 os.environ，此处直接读取即可。
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行期配置，支持环境变量覆盖（大小写不敏感）。"""

    llm_mode: str = "mock"  # mock | real
    task_timeout_seconds: int = 60
    max_concurrent_tasks: int = 3
    max_logs: int = 500
    max_task_entries: int = 1000
    zombie_task_seconds: int = 300

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
