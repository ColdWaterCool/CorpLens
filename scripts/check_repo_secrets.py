"""扫描仓库中是否误含疑似 API Key（上线前建议跑）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAT = re.compile(r"sk-[a-zA-Z0-9]{20,}|tp-[a-zA-Z0-9]{20,}")
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "private", "test", "outputs"}
SKIP_FILES = {".env"}  # 本机密钥文件，不扫描内容是否存在，只警告勿提交


def main() -> int:
    bad: list[str] = []
    env_path = ROOT / ".env"
    if env_path.exists():
        print("[提示] 检测到本机 .env —— 请确认未 git add / commit。")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        if path.name in SKIP_FILES or path.name.endswith(".png") or path.name.endswith(".zip"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if PAT.search(text):
            bad.append(str(path.relative_to(ROOT)))

    if bad:
        print("[失败] 以下文件疑似含 API Key，请删除后再公开：")
        for b in bad:
            print(" -", b)
        return 1
    print("[通过] 未在可公开文件中发现疑似 API Key。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
