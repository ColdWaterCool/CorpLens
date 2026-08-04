"""把四席框架成型为带 SOP 结构的需求分析书。"""
from __future__ import annotations

import re

from src.format_clean import extract_mermaid, sanitize_mermaid


def _strip_json_block(text: str) -> str:
    return re.sub(r"```json\s*[\s\S]*?```", "", text or "", flags=re.I).strip()


def _rename_market(fw: str) -> str:
    t = _strip_json_block(fw or "")
    t = re.sub(r"^###\s*框架·市场.*$", "### 市场与转型切入", t, count=1, flags=re.M)
    reps_h = [
        (r"^####\s*SOP关键词.*$", "#### SOP 关键词"),
        (r"^####\s*SOP切入\s*$", "#### SOP 切入主题与关键词"),
        (r"^####\s*企业基础与Brand\s*$", "#### 企业基础与 Brand Effect"),
        (r"^####\s*三柱加权根因\s*$", "#### 品牌/技术/创新力 · 加权根因"),
        (r"^####\s*核心卖点.*$", "#### 核心卖点（须守住）"),
        (r"^####\s*主体图谱\s*$", "#### 市场主体图谱"),
        (r"^####\s*地理要点\s*$", "#### 地理位置安排"),
        (r"^####\s*缺口与结论\s*$", "#### 需求、竞争与缺口"),
        (r"^####\s*缺口要点\s*$", "#### 需求、竞争与缺口"),
        (r"^####\s*机器数据\s*$", ""),
    ]
    for pat, to in reps_h:
        t = re.sub(pat, to, t, flags=re.M)
    reps = [
        (r"^-\s*切入主题：\s*", "- **切入主题**："),
        (r"^-\s*关键词：\s*", "- **关键词**："),
        (r"^-\s*为何先切这里：\s*", "- **为何先切这里**："),
        (r"^-\s*不做的边界：\s*", "- **不做的边界**："),
        (r"^-\s*品牌资产.*：\s*", "- **品牌资产**："),
        (r"^-\s*技术工艺资产：\s*", "- **技术工艺资产**："),
        (r"^-\s*创新力现状：\s*", "- **创新力现状**："),
        (r"^-\s*基础缺口.*：\s*", "- **基础缺口**："),
        (r"^-\s*根因公式：\s*", "- **根因公式**："),
        (r"^-\s*根本原因结论：\s*", "- **根本原因结论**："),
        (r"^-\s*历史/现有卖点：\s*", "- **历史/现有卖点**："),
        (r"^-\s*卖点兑现卡点：\s*", "- **卖点兑现卡点**："),
        (r"^-\s*转型后如何加强卖点：\s*", "- **转型后如何加强卖点**："),
        (r"^-\s*锚点：\s*", "- **锚点位置**："),
        (r"^-\s*半径：\s*", "- **服务半径**："),
        (r"^-\s*场景：\s*", "- **场景分布**："),
        (r"^-\s*策略[^：:]*[:：]\s*", "- **地理策略建议**："),
        (r"^-\s*待补充：\s*", "- **待补充地理信息**："),
        (r"^-\s*核心需求：\s*", "- **核心需求**："),
        (r"^-\s*竞争替代：\s*", "- **竞争与替代**："),
        (r"^-\s*数字化缺口：\s*", "- **数字化缺口（按主体×地理）**："),
        (r"^-\s*框架结论：\s*", "- **一句话市场结论**："),
        (r"^-\s*框架结论（一句话）：\s*", "- **一句话市场结论**："),
    ]
    return _apply_line_reps(t, reps)


def _rename_economy(fw: str) -> str:
    t = _strip_json_block(fw or "")
    t = re.sub(r"^###\s*框架·经济\s*$", "### 经济理论与边际效益", t, count=1, flags=re.M)
    reps_h = [
        (r"^####\s*调查与人力成本\s*$", "#### 调查与人力成本"),
        (r"^####\s*成本与收入.*$", "#### 成本与收入（展开）"),
        (r"^####\s*PEC政经文\s*$", "#### PEC 政经文分析"),
        (r"^####\s*结构与付费\s*$", "#### 成本收入与付费结构"),
        (r"^####\s*经济理论要点\s*$", "#### 经济理论要点"),
        (r"^####\s*价值抓手与边际\s*$", "#### 价值抓手与边际"),
        (r"^####\s*图表数据.*$", ""),
    ]
    for pat, to in reps_h:
        t = re.sub(pat, to, t, flags=re.M)
    reps = [
        (r"^-\s*在职人数：\s*", "- **在职人数**："),
        (r"^-\s*薪资区间：\s*", "- **薪资区间**："),
        (r"^-\s*月人力成本区间.*：\s*", "- **月人力成本区间（推断）**："),
        (r"^-\s*编制结构解读：\s*", "- **编制结构解读**："),
        (r"^-\s*仍需追问：\s*", "- **仍需追问**："),
        (r"^-\s*人力：\s*", "- **人力**："),
        (r"^-\s*原料/货品：\s*", "- **原料/货品**："),
        (r"^-\s*租金场地：\s*", "- **租金场地**："),
        (r"^-\s*获客/平台抽成：\s*", "- **获客/平台抽成**："),
        (r"^-\s*成本粗览：\s*", "- **成本结构粗览**："),
        (r"^-\s*收入方式：\s*", "- **收入方式（现状推断）**："),
        (r"^-\s*谁付费[×xX].*?[:：]\s*", "- **谁付费 × 在哪赚钱（粗）**："),
        (r"^-\s*政治/政策关注点：\s*", "- **政治/政策关注点**："),
        (r"^-\s*经济/市场结构：\s*", "- **经济/市场结构**："),
        (r"^-\s*文化/地方好感度：\s*", "- **文化/地方好感度**："),
        (r"^-\s*PEC综合含义：\s*", "- **PEC 综合含义**："),
        (r"^-\s*价值抓手：\s*", "- **价值抓手优先级**："),
        (r"^-\s*不建议先砸钱：\s*", "- **不建议先砸钱的地方**："),
        (r"^-\s*框架结论：\s*", "- **一句话经济结论**："),
        (r"^-\s*框架结论（一句话）：\s*", "- **一句话经济结论**："),
        (r"^-\s*理论(\d+)：\s*", r"- **理论\1**："),
    ]
    return _apply_line_reps(t, reps)


def _rename_roadmap(fw: str) -> str:
    t = _strip_json_block(fw or "")
    t = re.sub(r"^###\s*框架·路线\s*$", "### 实现过程 · 方式 · 创新点", t, count=1, flags=re.M)
    reps_h = [
        (r"^####\s*优先级排序.*$", "#### 优先级排序（P0–P3）"),
        (r"^####\s*平台化运维成本.*$", "#### 平台化运维成本"),
        (r"^####\s*阶段判断\s*$", "#### 阶段判断"),
        (r"^####\s*优化点排序\s*$", "#### 优化点排序"),
        (r"^####\s*辩驳·人力资源\s*$", "#### 辩驳 · 人力资源"),
        (r"^####\s*辩驳·品牌渠道\s*$", "#### 辩驳 · 品牌渠道"),
        (r"^####\s*辩驳·产品创新\s*$", "#### 辩驳 · 产品创新"),
        (r"^####\s*辩驳·平台化战略\s*$", "#### 辩驳 · 平台化战略"),
        (r"^####\s*实现过程.*$", "#### 实现过程（SOP 步骤）"),
        (r"^####\s*实现方式\s*$", "#### 实现方式"),
        (r"^####\s*创新点.*$", "#### 创新点"),
        (r"^####\s*里程碑与风险\s*$", "#### 里程碑与风险"),
    ]
    for pat, to in reps_h:
        t = re.sub(pat, to, t, flags=re.M)
    reps = [
        (r"^-\s*当前阶段：\s*", "- **当前阶段**："),
        (r"^-\s*判断依据：\s*", "- **判断依据**："),
        (r"^-\s*优先主体与地理：\s*", "- **优先主体与地理**："),
        (r"^-\s*下一阶段目标：\s*", "- **下一阶段目标**："),
        (r"^-\s*工具选型原则：\s*", "- **工具选型原则**："),
        (r"^-\s*组织分工：\s*", "- **组织分工**："),
        (r"^-\s*试点范围：\s*", "- **试点范围**："),
        (r"^-\s*度量指标：\s*", "- **度量指标**："),
        (r"^-\s*90\s*天里程碑：\s*", "- **90 天里程碑**："),
        (r"^-\s*依赖与风险：\s*", "- **依赖与风险**："),
        (r"^-\s*近期行动：\s*", "- **近期行动**："),
    ]
    return _apply_line_reps(t, reps)


def _apply_line_reps(t: str, reps: list[tuple[str, str]]) -> str:
    lines = []
    for line in t.splitlines():
        done = False
        for pat, to in reps:
            if re.match(pat, line):
                lines.append(re.sub(pat, to, line, count=1))
                done = True
                break
        if not done:
            lines.append(line)
    # 去掉空 #### 残留
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def assemble_from_frameworks(
    *,
    name: str,
    industry: str,
    one_liner: str,
    location: str,
    actors: str,
    market_fw: str,
    economy_fw: str,
    roadmap_fw: str,
    diagram_fw: str,
    headcount: str = "",
    salary_min: str = "",
    salary_max: str = "",
    education_mix: str = "",
    brand_years: str = "",
) -> str:
    mermaid = extract_mermaid(diagram_fw) or sanitize_mermaid(diagram_fw)
    market = _rename_market(market_fw)
    economy = _rename_economy(economy_fw)
    roadmap = _rename_roadmap(roadmap_fw)
    return f"""# {name} · 转型需求分析书（草案）

> 按企业转型 SOP（辩证版）：Brand/技术/创新加权根因 → PEC 政经文 → 四象限辩驳与试验 → 思考化流程图。比例与指数均为**推断示意**。

## 0. 企业速写与调查口径
- **名称**：{name}
- **行业**：{industry or '未指定'}
- **业务一句话**：{one_liner or '（未填写）'}
- **地理位置**：{location or '（未填写）'}
- **已知市场主体**：{actors or '（未填写，见市场分析推断）'}
- **在职人数**：{headcount or '（待调查）'}
- **薪资区间**：最低 {salary_min or '（待调查）'} / 最高 {salary_max or '（待调查）'}
- **教育/岗位结构**：{education_mix or '（待调查）'}
- **品牌年限/老字号**：{brand_years or '（待调查）'}

## 1. 市场与转型切入（SOP）
{market}

## 2. 经济理论与边际效益（含 PEC）
{economy}

> 效益组合图见产品界面「效益图」分页。

## 3. 实现过程 · 方式 · 创新点（四象限辩驳）
{roadmap}

## 4. 流程对照图（思考化：决策 / 试点 / 守住卖点）

> 产品界面渲染为图片；下载文稿保留源码。

```mermaid
{mermaid}
```

## 5. 说明
本稿强调：守住 Brand Effect、用加权找根因、用试验决定自动化与渠道边界。图表指数用于排序讨论，不构成财务预测。补充真实调研后请修订。
"""


def assembled_looks_healthy(doc: str) -> bool:
    if not doc or len(doc) < 500:
        return False
    if "```markdown" in doc:
        return False
    if "## 0. 企业速写" not in doc:
        return False
    if "## 1." not in doc or "## 3." not in doc:
        return False
    if "```mer\n" in doc or "0ubgraph" in doc:
        return False
    if doc.count("口口") >= 2 or "角角" in doc:
        return False
    if "```mermaid" not in doc:
        return False
    return True
