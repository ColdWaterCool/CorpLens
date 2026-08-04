"""从经济席框架解析图表数据；解析失败则用合理默认推断值。"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class ChartBundle:
    optimization: list[dict] = field(default_factory=list)
    marginal: list[dict] = field(default_factory=list)
    combo: list[dict] = field(default_factory=list)
    source: str = "default"


DEFAULT_CHARTS = ChartBundle(
    optimization=[
        {"item": "沟通/排期耗时", "ratio": 35},
        {"item": "近端转化", "ratio": 25},
        {"item": "复购留存", "ratio": 20},
        {"item": "收款对账", "ratio": 15},
        {"item": "其他扩张相关", "ratio": 5},
    ],
    marginal=[
        {"item": "近端老客复购", "benefit": 40, "effort": 20},
        {"item": "预约留痕", "benefit": 35, "effort": 25},
        {"item": "说明页获客", "benefit": 25, "effort": 30},
        {"item": "全城投放", "benefit": 15, "effort": 70},
    ],
    combo=[
        {"lever": "流程线上化", "efficiency": 40, "revenue": 20, "risk_down": 25},
        {"lever": "会员沉淀", "efficiency": 25, "revenue": 35, "risk_down": 20},
        {"lever": "近端深耕", "efficiency": 30, "revenue": 30, "risk_down": 30},
    ],
    source="default",
)


def extract_chart_bundle(*texts: str) -> ChartBundle:
    blob = "\n".join(t or "" for t in texts)
    m = re.search(r"```json\s*([\s\S]*?)```", blob, flags=re.I)
    raw = m.group(1).strip() if m else ""
    if not raw:
        # 尝试裸 JSON 对象
        m2 = re.search(r"\{\s*\"optimization\"[\s\S]*\}", blob)
        raw = m2.group(0) if m2 else ""
    if not raw:
        return DEFAULT_CHARTS
    try:
        data = json.loads(raw)
        opt = _norm_opt(data.get("optimization"))
        mar = _norm_mar(data.get("marginal"))
        com = _norm_combo(data.get("combo"))
        if not opt or not mar:
            return DEFAULT_CHARTS
        return ChartBundle(optimization=opt, marginal=mar, combo=com or DEFAULT_CHARTS.combo, source="model")
    except Exception:
        return DEFAULT_CHARTS


def _clip(n, lo=0, hi=100) -> int:
    try:
        v = int(round(float(n)))
    except Exception:
        v = 0
    return max(lo, min(hi, v))


def _norm_opt(rows) -> list[dict]:
    out = []
    if not isinstance(rows, list):
        return out
    for r in rows:
        if not isinstance(r, dict):
            continue
        item = str(r.get("item") or "").strip()
        if not item:
            continue
        out.append({"item": item[:20], "ratio": _clip(r.get("ratio", 0))})
    return out[:6]


def _norm_mar(rows) -> list[dict]:
    out = []
    if not isinstance(rows, list):
        return out
    for r in rows:
        if not isinstance(r, dict):
            continue
        item = str(r.get("item") or "").strip()
        if not item:
            continue
        out.append(
            {
                "item": item[:20],
                "benefit": _clip(r.get("benefit", 0)),
                "effort": _clip(r.get("effort", r.get("cost", 0))),
            }
        )
    return out[:6]


def _norm_combo(rows) -> list[dict]:
    out = []
    if not isinstance(rows, list):
        return out
    for r in rows:
        if not isinstance(r, dict):
            continue
        lever = str(r.get("lever") or "").strip()
        if not lever:
            continue
        out.append(
            {
                "lever": lever[:16],
                "efficiency": _clip(r.get("efficiency", 0)),
                "revenue": _clip(r.get("revenue", 0)),
                "risk_down": _clip(r.get("risk_down", 0)),
            }
        )
    return out[:5]
