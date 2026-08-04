"""把 Mermaid 源码渲染成 PNG（优先本地 kroki/mermaid.ink，失败则返回空）。"""
from __future__ import annotations

import base64
import urllib.error
import urllib.request
from io import BytesIO


def mermaid_to_png(mermaid_source: str, timeout: float = 12.0) -> bytes | None:
    src = (mermaid_source or "").strip()
    if not src:
        return None
    # mermaid.ink：urlsafe base64
    encoded = base64.urlsafe_b64encode(src.encode("utf-8")).decode("ascii")
    urls = [
        f"https://mermaid.ink/img/{encoded}?type=png",
        f"https://kroki.io/mermaid/png/{_kroki_encode(src)}",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TransformAgent/0.5"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if data and len(data) > 200 and data[:8] == b"\x89PNG\r\n\x1a\n":
                    return data
                if data and len(data) > 200:
                    # kroki 也可能直接给 png
                    return data
        except Exception:
            continue
    return None


def _kroki_encode(text: str) -> str:
    # kroki: deflate + base64 urlsafe
    import zlib

    compressed = zlib.compress(text.encode("utf-8"), 9)[2:-4]
    return base64.urlsafe_b64encode(compressed).decode("ascii")


def png_or_placeholder(mermaid_source: str) -> tuple[bytes | None, str]:
    """返回 (png_bytes|None, note)。"""
    png = mermaid_to_png(mermaid_source)
    if png:
        return png, "流程图已渲染为图片"
    return None, "外网渲染服务不可用时，界面将使用内嵌 Mermaid 组件显示"
