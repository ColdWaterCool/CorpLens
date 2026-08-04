from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.providers import resolve_provider

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"


@dataclass
class Settings:
    mock: bool
    api_base: str
    api_key: str
    model: str
    provider: str
    llm_assemble: bool


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env", override=True)
    mock_raw = os.getenv("TRANSFORM_AGENT_MOCK", "1").strip().lower()
    mock = mock_raw in {"1", "true", "yes", "on"}

    provider_name = os.getenv("LLM_PROVIDER", "custom").strip().lower()
    preset = resolve_provider(provider_name)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    api_base = os.getenv("OPENAI_API_BASE", "").strip().rstrip("/")
    model = os.getenv("OPENAI_MODEL", "").strip()

    if preset:
        api_base = api_base or preset.api_base
        model = model or preset.model
    else:
        api_base = api_base or "https://api.openai.com/v1"
        model = model or "gpt-4o-mini"

    if not api_key:
        mock = True

    assemble_raw = os.getenv("TRANSFORM_AGENT_LLM_ASSEMBLE", "0").strip().lower()
    llm_assemble = assemble_raw in {"1", "true", "yes", "on"}

    return Settings(
        mock=mock,
        api_base=api_base,
        api_key=api_key,
        model=model,
        provider=preset.key if preset else "custom",
        llm_assemble=llm_assemble,
    )


def read_prompt(rel: str) -> str:
    """读取 prompts/ 下文件。rel 如 seats/market.md 或 skills/xxx.md"""
    rel = rel.replace("\\", "/").lstrip("/")
    if rel.startswith("prompts/"):
        rel = rel[len("prompts/") :]
    path = PROMPTS / rel
    return path.read_text(encoding="utf-8")


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def save_env(updates: dict[str, str]) -> Path:
    """合并写入 .env（仅本机，已被 gitignore）。"""
    env_path = ROOT / ".env"
    existing: dict[str, str] = {}
    order: list[str] = []
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            existing[k] = v.strip()
            if k not in order:
                order.append(k)
    for k, v in updates.items():
        if k not in order:
            order.append(k)
        existing[k] = str(v)
    # 清理已废弃键
    existing.pop("CORPLENS_USE_PRIVATE", None)
    preferred = [
        "TRANSFORM_AGENT_MOCK",
        "LLM_PROVIDER",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "OPENAI_MODEL",
        "TRANSFORM_AGENT_LLM_ASSEMBLE",
    ]
    keys = [k for k in preferred if k in existing] + [
        k for k in order if k not in preferred and k in existing
    ]
    lines = [
        "# 企析智体 CorpLens 本地配置 —— 切勿提交到 GitHub",
        "",
    ]
    for k in keys:
        lines.append(f"{k}={existing[k]}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env_path


def mask_key(key: str) -> str:
    k = (key or "").strip()
    if len(k) <= 8:
        return "（未填写）" if not k else "****"
    return k[:4] + "…" + k[-4:]
