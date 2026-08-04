"""快速探测当前 .env 里的模型是否可用。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_settings
from src.llm import chat_complete


def main() -> int:
    settings = load_settings()
    print(f"provider = {settings.provider}")
    print(f"mock     = {settings.mock}")
    print(f"base     = {settings.api_base}")
    print(f"model    = {settings.model}")
    print(f"key      = {'已配置' if settings.api_key else '空'}")
    if settings.mock:
        print("当前为示意模式：请设 TRANSFORM_AGENT_MOCK=0 并填写 OPENAI_API_KEY")
        return 1
    text = chat_complete(
        settings,
        system="你是简洁助手，用中文回答。",
        user="只回复：接口连通。",
    )
    print("--- 模型回复 ---")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
