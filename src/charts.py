"""生成优化比例 / 边际效益组合图（PNG bytes）。"""
from __future__ import annotations

from io import BytesIO
from typing import Iterable

from src.chart_data import ChartBundle


def _setup_font():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def _to_png(fig) -> bytes:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="white")
    import matplotlib.pyplot as plt

    plt.close(fig)
    return buf.getvalue()


def fig_optimization_ratio(bundle: ChartBundle) -> bytes:
    plt = _setup_font()
    rows = bundle.optimization or []
    labels = [r["item"] for r in rows]
    vals = [r["ratio"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    colors = ["#B91C1C", "#DC2626", "#F87171", "#FCA5A5", "#FEE2E2"]
    bars = ax.barh(labels[::-1], vals[::-1], color=(colors * 3)[: len(vals)][::-1])
    ax.set_xlabel("预估可优化比例（% · 推断）")
    ax.set_title("流程环节 · 预估优化比例")
    ax.set_xlim(0, max(vals + [50]) * 1.15)
    for b, v in zip(bars, vals[::-1]):
        ax.text(v + 0.8, b.get_y() + b.get_height() / 2, f"{v}%", va="center", fontsize=9)
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    fig.tight_layout()
    return _to_png(fig)


def fig_marginal_benefit(bundle: ChartBundle) -> bytes:
    plt = _setup_font()
    rows = bundle.marginal or []
    labels = [r["item"] for r in rows]
    benefit = [r["benefit"] for r in rows]
    effort = [r["effort"] for r in rows]
    x = range(len(labels))
    fig, ax1 = plt.subplots(figsize=(7.5, 3.8))
    w = 0.36
    ax1.bar([i - w / 2 for i in x], benefit, width=w, color="#B91C1C", label="边际效益（推断）")
    ax1.bar([i + w / 2 for i in x], effort, width=w, color="#64748B", label="投入/难度（推断）")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels, rotation=15, ha="right")
    ax1.set_ylabel("指数（0-100）")
    ax1.set_title("举措组合 · 边际效益 vs 投入难度")
    ax1.set_ylim(0, 100)
    # 效益/投入比折线
    ax2 = ax1.twinx()
    ratio = [round(b / e, 2) if e else 0 for b, e in zip(benefit, effort)]
    ax2.plot(list(x), ratio, color="#CA8A04", marker="o", linewidth=2, label="效益/投入比")
    ax2.set_ylabel("效益÷投入")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8)
    ax1.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return _to_png(fig)


def fig_combo_levers(bundle: ChartBundle) -> bytes:
    plt = _setup_font()
    rows = bundle.combo or []
    labels = [r["lever"] for r in rows]
    eff = [r["efficiency"] for r in rows]
    rev = [r["revenue"] for r in rows]
    risk = [r["risk_down"] for r in rows]
    import numpy as np

    x = np.arange(len(labels))
    w = 0.25
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.bar(x - w, eff, width=w, color="#B91C1C", label="提效")
    ax.bar(x, rev, width=w, color="#1D4ED8", label="增收潜力")
    ax.bar(x + w, risk, width=w, color="#15803D", label="降风险")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("指数（0-100 · 推断）")
    ax.set_title("转型抓手组合 · 提效 / 增收 / 降风险")
    ax.legend(fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return _to_png(fig)


def build_all_charts(bundle: ChartBundle) -> dict[str, bytes]:
    return {
        "optimization": fig_optimization_ratio(bundle),
        "marginal": fig_marginal_benefit(bundle),
        "combo": fig_combo_levers(bundle),
    }
