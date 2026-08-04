from __future__ import annotations

import re
from dataclasses import dataclass


SECTION_KEYS = [
    ("1. 现状分析", "analysis"),
    ("2. 转型阶段判断", "stage"),
    ("3. 方向建议（含盈利/价值抓手）", "direction"),
    ("4. 近期行动", "actions"),
    ("5. 说明", "disclaimer"),
]


@dataclass
class Report:
    title: str
    raw_markdown: str
    sections: dict[str, str]
    missing: list[str]


def parse_report(md: str) -> Report:
    text = md.strip()
    title = "转型分析草案"
    m = re.search(r"^#\s+(.+)$", text, flags=re.M)
    if m:
        title = m.group(1).strip()

    sections: dict[str, str] = {}
    missing: list[str] = []

    # 按 ## N. 切分
    parts = re.split(r"(?m)^(##\s+\d+\.\s+[^\n]+)\s*$", text)
    # parts[0] = preamble, then heading, body, heading, body...
    heading_map = {h: k for h, k in SECTION_KEYS}
    i = 1
    while i + 1 < len(parts):
        heading = parts[i].strip()
        body = parts[i + 1].strip()
        # normalize heading key
        key = None
        for full, k in SECTION_KEYS:
            if heading.replace("## ", "").startswith(full.split(" ", 1)[0]) or full in heading:
                key = k
                break
        # more reliable: match by number prefix
        num = re.match(r"##\s+(\d+)\.", heading)
        if num:
            idx = int(num.group(1)) - 1
            if 0 <= idx < len(SECTION_KEYS):
                key = SECTION_KEYS[idx][1]
        if key:
            sections[key] = body
        i += 2

    for _, key in SECTION_KEYS:
        if key not in sections or not sections[key].strip():
            missing.append(key)

    return Report(title=title, raw_markdown=text, sections=sections, missing=missing)
