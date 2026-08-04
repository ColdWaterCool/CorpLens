from __future__ import annotations

import html
import re


def mermaid_html(mermaid_source: str, height: int = 420) -> str:
    """用 CDN 渲染 Mermaid；失败时页面仍显示源码。"""
    src = mermaid_source.strip()
    if not src:
        return "<p>（暂无流程图）</p>"
    # 避免 </script> 打断
    safe = src.replace("</", "<\\/")
    escaped = html.escape(src)
    return f"""
<div class="mermaid-wrap">
  <div class="mermaid">{safe}</div>
  <details style="margin-top:0.75rem">
    <summary>查看流程图源码</summary>
    <pre style="white-space:pre-wrap">{escaped}</pre>
  </details>
</div>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
  mermaid.run();
</script>
"""


def strip_mermaid_fence(text: str) -> str:
    m = re.search(r"```mermaid\s*([\s\S]*?)```", text, flags=re.I)
    return m.group(1).strip() if m else text.strip()
