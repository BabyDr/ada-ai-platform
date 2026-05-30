"""AI TextFlow CLI — 调用 Sidecar SSE 任务接口（translate / summarize / list）。Author: RenXiaodi"""

from __future__ import annotations

import json
import os
import sys

import click
import httpx

BASE_URL = os.environ.get("AI_APP_BASE_URL", "http://127.0.0.1:18765").rstrip("/")


@click.group()
def cli() -> None:
    """AI TextFlow CLI — 翻译与总结工具"""


@cli.command()
@click.option("--text", required=True, help="要翻译的文本")
@click.option("--from", "from_lang", required=True, help="源语言代码，如 zh/en/ja")
@click.option("--to", "to_lang", required=True, help="目标语言代码")
@click.option("--tone", default="Professional", help="语调（Professional/Conversational/Technical/Academic/Creative）")
def translate(text: str, from_lang: str, to_lang: str, tone: str) -> None:
    """翻译文本"""
    _stream_task(
        "translate",
        {
            "text": text,
            "sourceLang": from_lang,
            "targetLang": to_lang,
            "tone": tone,
        },
    )


@cli.command()
@click.option("--text", required=True, help="要总结的文本")
@click.option("--max-points", "key_points", default=3, help="要点数量")
@click.option("--word-limit", default=0, help="字数上限，0 表示不限")
@click.option("--tone", default="Professional", help="语调")
def summarize(text: str, key_points: int, word_limit: int, tone: str) -> None:
    """总结文本"""
    params: dict[str, object] = {
        "text": text,
        "keyPointsCount": key_points,
        "tone": tone,
    }
    if word_limit:
        params["wordLimit"] = word_limit
    _stream_task("summarize", params)


@cli.command("list")
def list_functions() -> None:
    """查看可用功能"""
    resp = httpx.get(f"{BASE_URL}/api/functions", timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    for fn in data["functions"]:
        click.echo(f"  {fn['id']:20s} {fn['name']:8s} - {fn['description']}")


def _stream_task(task_type: str, params: dict[str, object]) -> None:
    """调用 POST /api/task，终端逐字打印 token 内容。"""
    with httpx.stream(
        "POST",
        f"{BASE_URL}/api/task",
        json={"type": task_type, "params": params},
        timeout=120.0,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            try:
                data = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            content = data.get("content")
            if content:
                click.echo(content, nl=False)
                sys.stdout.flush()
    click.echo()


if __name__ == "__main__":
    cli()
