"""生成三柱薄弱贡献条形图。"""
from __future__ import annotations

from io import BytesIO

from src.ui_viz import MarketMeta


def fig_pillar_weights(meta: MarketMeta) -> bytes | None:
    if not meta.pillars:
        return None
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    names = [p["name"] for p in meta.pillars]
    contrib = [p["contrib"] for p in meta.pillars]
    strength = [p["strength"] for p in meta.pillars]

    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    y = range(len(names))
    ax.barh(list(y), contrib[::-1], color="#B91C1C", label="薄弱贡献=权重×(100-强度)")
    ax.barh([i + 0.0 for i in y], [s * 0.15 for s in strength[::-1]], color="#94A3B8", alpha=0.35, label="强度示意(×0.15)")
    ax.set_yticks(list(y))
    ax.set_yticklabels(names[::-1])
    ax.set_xlabel("薄弱贡献（越高越应优先治理）")
    ax.set_title("品牌 / 技术 / 创新力 · 加权根因")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()
