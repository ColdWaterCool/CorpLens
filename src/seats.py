from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.config import Settings, read_prompt
from src.llm import chat_complete


@dataclass(frozen=True)
class Seat:
    key: str
    title: str
    prompt_file: str
    blurb: str


SEATS: list[Seat] = [
    Seat("market", "市场·切入席", "seats/market.md", "关键词 · 品牌/技术/创新加权"),
    Seat("economy", "经济·效益席", "seats/economy.md", "人力调查 · PEC · 边际效益"),
    Seat("roadmap", "实现·创新席", "seats/roadmap.md", "四象限辩驳 · P0优先级 · 运维成本"),
    Seat("diagram", "流程图席", "seats/diagram.md", "决策·试点·目标链"),
]

DIALECTIC_SKILL = "skills/corplens_dialectic.md"


def _context_block(
    name: str,
    industry: str,
    one_liner: str,
    status: str,
    location: str = "",
    actors: str = "",
    headcount: str = "",
    salary_min: str = "",
    salary_max: str = "",
    education_mix: str = "",
    brand_years: str = "",
    brand_notes: str = "",
    policy_notes: str = "",
    local_favor: str = "",
) -> str:
    return (
        f"企业/项目名称：{name}\n"
        f"行业：{industry}\n"
        f"业务一句话：{one_liner}\n"
        f"所在城市/商圈/服务半径：{location or '（未填写）'}\n"
        f"已知市场主体：{actors or '（未填写）'}\n"
        f"在职人数：{headcount or '（待调查）'}\n"
        f"薪资最低：{salary_min or '（待调查）'}；薪资最高：{salary_max or '（待调查）'}\n"
        f"教育/岗位结构：{education_mix or '（待调查）'}\n"
        f"品牌年限/老字号情况：{brand_years or '（待调查）'}\n"
        f"品牌与工艺备注：{brand_notes or '（未填写）'}\n"
        f"已知政策关注点：{policy_notes or '（待核验）'}\n"
        f"地方好感度/文化备注：{local_favor or '（待调查）'}\n"
        f"当前状态描述：\n{status}\n"
    )


def _system_with_skill(seat_prompt_rel: str) -> str:
    base = read_prompt(seat_prompt_rel)
    try:
        skill = read_prompt(DIALECTIC_SKILL)
        return (
            base
            + "\n\n---\n# 必循思考流 Skill（嵌入，勿在正文提内部案例名）\n"
            + skill
        )
    except Exception:
        return base


def run_seat(seat: Seat, context: str, settings: Settings, mock_fn: Callable[[str], str]) -> str:
    if settings.mock:
        return mock_fn(seat.key)
    system = _system_with_skill(seat.prompt_file)
    user = (
        "请基于以下企业调查信息完成本席位分析。"
        "严格按席位格式输出；吸收思考流 Skill 的辩驳与试验要求；"
        "对用户可见正文禁止出现无关的内部案例店名。\n\n"
        + context
    )
    max_tokens = 1800 if seat.key != "diagram" else 900
    return chat_complete(settings, system, user, max_tokens=max_tokens)


def run_assemble(context: str, frameworks: dict[str, str], settings: Settings, mock_doc: str) -> str:
    if settings.mock:
        return mock_doc
    system = read_prompt("assemble.md")
    try:
        system = system + "\n\n" + read_prompt(DIALECTIC_SKILL)
    except Exception:
        pass
    parts = [
        "请将四席框架成型为《转型需求分析书》终稿。",
        "保留加权根因、PEC、P0–P3、思考化流程图；勿提及内部案例店名。",
        "",
        "## 企业信息",
        context,
        "",
        "## 市场·切入席",
        frameworks.get("market", "（无）"),
        "",
        "## 经济·效益席",
        frameworks.get("economy", "（无）"),
        "",
        "## 实现·创新席",
        frameworks.get("roadmap", "（无）"),
        "",
        "## 流程图席",
        frameworks.get("diagram", "（无）"),
    ]
    return chat_complete(settings, system, "\n".join(parts), temperature=0.3, max_tokens=4500)
