from __future__ import annotations

from openai import OpenAI

from src.config import Settings


def chat_complete(
    settings: Settings,
    system: str,
    user: str,
    *,
    temperature: float = 0.35,
    max_tokens: int = 2500,
) -> str:
    client = OpenAI(api_key=settings.api_key, base_url=settings.api_base)
    try:
        resp = client.chat.completions.create(
            model=settings.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except Exception:
        # 部分网关参数名不同，降级重试
        resp = client.chat.completions.create(
            model=settings.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("模型返回空内容")
    return content.strip()
