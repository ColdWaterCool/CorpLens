"""市场席可视化：关键词圆圈 + 三柱加权根因 + 计算说明。"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field


@dataclass
class MarketMeta:
    keywords: list[str] = field(default_factory=list)
    pillars: list[dict] = field(default_factory=list)
    root_cause: str = ""


def extract_market_meta(text: str) -> MarketMeta:
    meta = MarketMeta()
    m = re.search(r"```json\s*([\s\S]*?)```", text or "", flags=re.I)
    if not m:
        km = re.search(r"关键词：\s*(.+)", text or "")
        if km:
            meta.keywords = [x.strip() for x in re.split(r"[、,，/|]", km.group(1)) if x.strip()][:6]
        return meta
    try:
        data = json.loads(m.group(1))
        meta.keywords = [str(x).strip() for x in (data.get("keywords") or []) if str(x).strip()][:6]
        pillars = []
        for p in data.get("pillars") or []:
            if not isinstance(p, dict):
                continue
            name = str(p.get("name") or "").strip()
            if not name:
                continue
            strength = int(p.get("strength", 50))
            weight = float(p.get("weight", 0.33))
            strength = max(0, min(100, strength))
            weight = max(0.0, min(1.0, weight))
            contrib = round(weight * (100 - strength), 1)
            pillars.append(
                {
                    "name": name,
                    "strength": strength,
                    "weight": weight,
                    "contrib": contrib,
                    "weakness_link": str(p.get("weakness_link") or ""),
                }
            )
        meta.pillars = pillars
        meta.root_cause = str(data.get("root_cause") or "").strip()
    except Exception:
        pass
    return meta


def keywords_circles_html(keywords: list[str]) -> str:
    if not keywords:
        keywords = ["待提炼关键词"]
    colors = ["#B91C1C", "#9A3412", "#A16207", "#1D4ED8", "#0F766E", "#6D28D9"]
    cells = []
    for i, kw in enumerate(keywords):
        c = colors[i % len(colors)]
        cells.append(
            f"""
            <div style="
              width:112px;height:112px;border-radius:50%;
              border:3px solid {c};color:{c};
              display:flex;align-items:center;justify-content:center;
              text-align:center;padding:10px;font-weight:700;font-size:13px;
              background:radial-gradient(circle at 30% 30%, #fff, #f8fafc);
              box-shadow:0 2px 8px rgba(0,0,0,.06);
            ">{html.escape(kw)}</div>
            """
        )
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:18px;align-items:center;'
        'justify-content:flex-start;padding:12px 4px 8px 4px;min-height:140px;">'
        + "".join(cells)
        + "</div>"
    )


def weight_method_html(meta: MarketMeta) -> str:
    """固定展示计算方式与思考过程（不依赖 JSON 展开）。"""
    lines = [
        "<div style='padding:14px 16px;border:1px solid #e5e7eb;border-radius:12px;"
        "background:#fafafa;line-height:1.7;margin:8px 0 16px 0;'>",
        "<div style='font-weight:700;margin-bottom:6px;'>加权计算方式</div>",
        "<div>对每个支柱：<code>薄弱贡献 = 权重 × (100 − 强度)</code>。"
        "权重之和应为 1。薄弱贡献越高，越应优先治理。</div>",
        "<div style='margin-top:8px;font-weight:700;'>思考过程（简版）</div>",
        "<ol style='margin:6px 0 0 18px;padding:0;'>",
        "<li>先看企业基础与 Brand Effect：老店信任资产能否稳定兑现。</li>",
        "<li>再评技术可复制性、创新渠道能力，避免只谈「上系统」。</li>",
        "<li>用薄弱贡献排序，得到根本原因，再决定 SOP 切入主题。</li>",
        "</ol>",
    ]
    if meta.pillars:
        bits = "；".join(f"{p['name']}贡献 {p['contrib']}" for p in meta.pillars)
        top = max(meta.pillars, key=lambda x: x["contrib"])
        lines.append(f"<div style='margin-top:10px;'><b>本次计算：</b>{html.escape(bits)}。</div>")
        lines.append(
            f"<div><b>优先根因支柱：</b>{html.escape(top['name'])}"
            f"（薄弱贡献 {top['contrib']}）</div>"
        )
    if meta.root_cause:
        lines.append(
            f"<div style='margin-top:6px;'><b>根本原因结论：</b>"
            f"{html.escape(meta.root_cause)}</div>"
        )
    lines.append("</div>")
    return "".join(lines)


def pillars_table_md(meta: MarketMeta) -> str:
    if not meta.pillars:
        return ""
    lines = [
        "| 支柱 | 强度 | 权重 | 薄弱贡献 | 与问题联系 |",
        "|------|------|------|----------|------------|",
    ]
    for p in meta.pillars:
        lines.append(
            f"| {p['name']} | {p['strength']} | {p['weight']:.2f} | **{p['contrib']}** | {p['weakness_link'] or '—'} |"
        )
    total = round(sum(p["contrib"] for p in meta.pillars), 1)
    top = max(meta.pillars, key=lambda x: x["contrib"])
    lines += [
        "",
        f"- **薄弱贡献合计**：{total}",
        f"- **优先根因支柱**：{top['name']}（贡献 {top['contrib']}）",
    ]
    if meta.root_cause:
        lines.append(f"- **根本原因结论**：{meta.root_cause}")
    return "\n".join(lines)


def strip_json_blocks(text: str) -> str:
    return re.sub(r"```json\s*[\s\S]*?```", "", text or "", flags=re.I).strip()


def parse_priority_blocks(text: str) -> list[dict]:
    """从实现席文本提取 P0/P1... 条目。"""
    rows = []
    for m in re.finditer(
        r"^\s*-?\s*\*?\*?P([0-3])\*?\*?\s*[:：]\s*(.+)$",
        text or "",
        flags=re.M | re.I,
    ):
        rows.append({"level": f"P{m.group(1)}", "text": m.group(2).strip()})
    # 去重保序
    seen = set()
    out = []
    for r in rows:
        if r["level"] in seen:
            continue
        seen.add(r["level"])
        out.append(r)
    return out


def economy_cost_table_md(data_headcount: str, salary_min: str, salary_max: str) -> str:
    """根据调查字段做简易人力成本表（推断）。"""
    try:
        n = float(data_headcount)
    except Exception:
        n = None
    try:
        lo, hi = float(salary_min), float(salary_max)
        avg = (lo + hi) / 2
    except Exception:
        lo = hi = avg = None
    lines = [
        "| 项目 | 数值 | 说明 |",
        "|------|------|------|",
        f"| 在职人数 | {data_headcount or '待补充'} | 来自调查选择 |",
        f"| 薪资下限 | {salary_min or '待补充'} | 元/月 |",
        f"| 薪资上限 | {salary_max or '待补充'} | 元/月 |",
    ]
    if avg is not None:
        lines.append(f"| 推算均值 | {int(round(avg))} | (下限+上限)/2 |")
    if n is not None and avg is not None:
        month = int(round(n * avg))
        lines.append(f"| 月人力成本区间中枢 | ≈ {month} | 人数×均值（推断，未含社保加班） |")
        lines.append(f"| 年化粗算 | ≈ {month * 12} | 中枢×12（推断） |")
    else:
        lines.append("| 月人力成本 | 待补齐人数与薪资带 | 无法计算 |")
    lines.append("")
    lines.append("> 上表只服务讨论排序，不构成财务审计结论。")
    return "\n".join(lines)
