"""清洗模型输出：去掉错误代码栅、修复 Mermaid 常见语法问题。"""
from __future__ import annotations

import re


def strip_outer_fence(text: str, languages: tuple[str, ...] = ("markdown", "md", "")) -> str:
    """去掉整篇被 ```markdown ... ``` 包裹的情况。"""
    raw = (text or "").strip()
    if not raw.startswith("```"):
        return raw
    m = re.match(r"^```([a-zA-Z0-9_-]*)\s*\n([\s\S]*?)\n```\s*$", raw)
    if not m:
        return raw
    lang = (m.group(1) or "").lower()
    if lang in languages or lang == "":
        return m.group(2).strip()
    return raw


def strip_nested_markdown_fences(text: str) -> str:
    """去掉章节里残留的 ```markdown / ``` 包裹，保留 mermaid 块。"""
    out = text or ""
    # 去掉 ```markdown ... ```（非贪婪，可多段）
    out = re.sub(r"```(?:markdown|md)\s*\n([\s\S]*?)```", r"\1", out, flags=re.I)
    # 去掉误写的单独 ``` 收尾残留（成对已处理）
    return out.strip()


def extract_mermaid(text: str) -> str:
    m = re.search(r"```mermaid\s*([\s\S]*?)```", text or "", flags=re.I)
    if m:
        return sanitize_mermaid(m.group(1))
    if "flowchart" in (text or "") or "graph " in (text or ""):
        return sanitize_mermaid(text or "")
    return ""


_BAD_ID = re.compile(r"\b([A-Za-z]+)##\s*")


def sanitize_mermaid(src: str) -> str:
    """尽量把常见坏语法修成可渲染图；修不好则返回安全兜底图。"""
    s = (src or "").strip()
    s = s.replace("```mermaid", "").replace("```", "").strip()
    # A## 家长 → 丢弃坏片段，后面用兜底
    if "##" in s or re.search(r"[\u4e00-\u9fff]\s*-->", s) and re.search(r"subgraph\s+[\u4e00-\u9fff]", s):
        # 中文当 subgraph id 也可能坏；继续尝试轻量修复
        pass
    s = _BAD_ID.sub(lambda m: m.group(1) + "_", s)
    # 去掉节点 ID 中的空格：A 1[ → A1[
    s = re.sub(r"\b([A-Za-z]+)(\d*)\s+\[", r"\1\2[", s)
    # TOO → TOBE 笔误
    s = s.replace("TOO", "TOBE")
    if not _mermaid_looks_ok(s):
        return _fallback_mermaid()
    return s


def _mermaid_looks_ok(s: str) -> bool:
    if "flowchart" not in s and not s.strip().startswith("graph"):
        return False
    if "##" in s:
        return False
    # 节点 ID 不应含中文
    if re.search(r"\b[\u4e00-\u9fff]+\s*(\[|-->)", s):
        return False
    if "subgraph ASIS" not in s and 'subgraph ASIS[' not in s:
        # 宽松：至少有 subgraph
        if "subgraph" not in s:
            return False
    return True


def _fallback_mermaid() -> str:
    return """flowchart TD
  subgraph ASIS["现状"]
    A1[获客/咨询] --> A2[人工沟通排期]
    A2 --> A3[履约]
    A3 --> A4[收款与零散记录]
  end
  subgraph TOBE["目标"]
    B1[对外说明与入口] --> B2[在线预约/登记]
    B2 --> B3[履约留痕]
    B3 --> B4[回访与复购]
  end
  ASIS -.->|优先近端主体| TOBE"""


def clean_seat_output(key: str, content: str) -> str:
    text = strip_outer_fence(content or "")
    text = text.replace("\ufeff", "").replace("\ufffd", "")
    if key == "diagram":
        body = extract_mermaid(text) or sanitize_mermaid(text)
        return f"```mermaid\n{body}\n```"
    text = strip_nested_markdown_fences(text)
    text = _fix_markdown_tables(text)
    return text.strip()


def _fix_markdown_tables(text: str) -> str:
    """补全表格缺省的收尾 |、去掉空行表。"""
    lines = []
    for line in text.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            if re.match(r"^\|\s*(\|\s*)+$", s.strip()):
                continue
            if not s.endswith("|"):
                s = s + " |"
            # 规范化连续空单元格
            lines.append(s)
        else:
            lines.append(line)
    return "\n".join(lines)

def clean_assembled_document(doc: str, mermaid: str = "") -> str:
    text = strip_outer_fence(doc or "")
    text = strip_nested_markdown_fences(text)
    text = _normalize_headings(text)
    text = _drop_empty_table_rows(text)
    # 若终稿里 mermaid 坏了，用已清洗的 mermaid 替换第 4 章代码块
    if mermaid:
        cleaned = sanitize_mermaid(mermaid)
        block = f"```mermaid\n{cleaned}\n```"
        if re.search(r"```mermaid[\s\S]*?```", text, flags=re.I):
            text = re.sub(r"```mermaid[\s\S]*?```", block, text, count=1, flags=re.I)
        elif "## 4." in text:
            text = re.sub(
                r"(## 4\.[^\n]*\n)",
                r"\1\n" + block + "\n",
                text,
                count=1,
            )
    return text.strip() + "\n"


def _normalize_headings(text: str) -> str:
    """把模型偶发的「第一部分」等标题扳回标准编号。"""
    reps = [
        (r"^##\s*第[一二三四五零0-9]+部分[:：\s]*企业速写\s*$", "## 0. 企业速写"),
        (r"^##\s*第[一二三四五0-9]+部分[:：\s]*市场分析\s*$", "## 1. 市场分析"),
        (r"^##\s*第[一二三四五0-9]+部分[:：\s]*经济.*$", "## 2. 经济与价值粗览"),
        (r"^##\s*第[一二三四五0-9]+部分[:：\s]*实现路线\s*$", "## 3. 实现路线"),
        (r"^##\s*第[一二三四五0-9]+部分[:：\s]*流程.*$", "## 4. 流程对照图（现状 → 目标）"),
        (r"^##\s*第[一二三四五0-9]+部分[:：\s]*说明\s*$", "## 5. 说明"),
        (r"^###\s*\d+[\.、]\s*市场与问题\s*$", "### 市场与问题"),
        (r"^###\s*\d+[\.、]\s*经济与价值\s*$", "### 经济与价值"),
        (r"^###\s*\d+[\.、]\s*实现路线\s*$", "### 实现路线"),
        (r"^####\s*\d+[\.、]?\s*主体图谱\s*$", "#### 市场主体图谱"),
        (r"^####\s*主体图谱\s*$", "#### 市场主体图谱"),
    ]
    lines = []
    for line in text.splitlines():
        replaced = line
        for pat, to in reps:
            if re.match(pat, line.strip()):
                replaced = to
                break
        lines.append(replaced)
    return "\n".join(lines)


def _drop_empty_table_rows(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.strip().startswith("|") and re.match(r"^\|\s*(\|\s*)+$", line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines)
