from __future__ import annotations

"""常用 OpenAI 兼容提供商预设（免费调试优先）。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    key: str
    title: str
    api_base: str
    model: str
    signup_url: str
    note: str


# 国内友好 / 常见免费或注册送额度；具体额度以各平台控制台为准
PRESETS: dict[str, ProviderPreset] = {
    "siliconflow": ProviderPreset(
        key="siliconflow",
        title="硅基流动（推荐调试）",
        api_base="https://api.siliconflow.cn/v1",
        model="Qwen/Qwen2.5-14B-Instruct",
        signup_url="https://cloud.siliconflow.cn/",
        note="大陆直连；默认 14B 更稳。若额度不足可改 OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct",
    ),
    "zhipu": ProviderPreset(
        key="zhipu",
        title="智谱 GLM",
        api_base="https://open.bigmodel.cn/api/paas/v4",
        model="glm-4-flash",
        signup_url="https://open.bigmodel.cn/",
        note="大陆直连；Flash 档常有免费/低价额度",
    ),
    "deepseek": ProviderPreset(
        key="deepseek",
        title="DeepSeek",
        api_base="https://api.deepseek.com/v1",
        model="deepseek-chat",
        signup_url="https://platform.deepseek.com/",
        note="大陆直连；新用户常有赠送额度，用完按量付费",
    ),
    "mimo": ProviderPreset(
        key="mimo",
        title="小米 MiMo",
        api_base="https://api.xiaomimimo.com/v1",
        model="mimo-v2.5-pro",
        signup_url="https://mimo.mi.com/",
        note="已测通过；当前账号若余额不足需充值",
    ),
    "groq": ProviderPreset(
        key="groq",
        title="Groq（海外免费层）",
        api_base="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        signup_url="https://console.groq.com/",
        note="有免费层但可能需可访问外网",
    ),
    "openrouter": ProviderPreset(
        key="openrouter",
        title="OpenRouter 免费模型",
        api_base="https://openrouter.ai/api/v1",
        model="openrouter/auto",
        signup_url="https://openrouter.ai/",
        note="聚合多模型；可选带 :free 后缀的免费模型",
    ),
}


def resolve_provider(name: str) -> ProviderPreset | None:
    key = (name or "").strip().lower()
    if not key or key in {"custom", "openai", "none"}:
        return None
    return PRESETS.get(key)
