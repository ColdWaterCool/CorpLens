from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from src.assemble_template import assemble_from_frameworks, assembled_looks_healthy
from src.chart_data import ChartBundle, extract_chart_bundle
from src.charts import build_all_charts
from src.config import Settings
from src.format_clean import clean_assembled_document, clean_seat_output, extract_mermaid
from src.mermaid_image import mermaid_to_png
from src.seats import SEATS, Seat, _context_block, run_assemble, run_seat
from src.ui_viz import MarketMeta, extract_market_meta
from src.weight_chart import fig_pillar_weights
from src.demo_mock import mock_seat as _demo_mock_seat


@dataclass
class EnterpriseInput:
    name: str
    one_liner: str
    status: str
    industry: str = "未指定"
    location: str = ""
    actors: str = ""
    headcount: str = ""
    salary_min: str = ""
    salary_max: str = ""
    education_mix: str = ""
    brand_years: str = ""
    brand_notes: str = ""
    policy_notes: str = ""
    local_favor: str = ""


@dataclass
class SeatResult:
    key: str
    title: str
    content: str
    ok: bool = True
    error: str = ""


@dataclass
class MultiSeatReport:
    name: str
    seats: dict[str, SeatResult] = field(default_factory=dict)
    assembled_markdown: str = ""
    mermaid: str = ""
    mermaid_png: bytes | None = None
    chart_bundle: ChartBundle | None = None
    chart_pngs: dict[str, bytes] = field(default_factory=dict)
    market_meta: MarketMeta | None = None
    weight_png: bytes | None = None


def _mock_seat(key: str, data: EnterpriseInput) -> str:
    """公开演示示意稿（宠物洗护店模板，非内部行业案例）。"""
    return _demo_mock_seat(key, data)



def generate_multiseat(
    data: EnterpriseInput,
    settings: Settings,
    on_seat_done=None,
    mock_stagger_sec: float = 0.35,
) -> MultiSeatReport:
    ctx = _context_block(
        data.name.strip() or "未命名企业",
        data.industry.strip() or "未指定",
        data.one_liner.strip() or "（未填写）",
        data.status.strip() or "（未填写）",
        data.location.strip(),
        data.actors.strip(),
        data.headcount.strip(),
        data.salary_min.strip(),
        data.salary_max.strip(),
        data.education_mix.strip(),
        data.brand_years.strip(),
        data.brand_notes.strip(),
        data.policy_notes.strip(),
        data.local_favor.strip(),
    )
    report = MultiSeatReport(name=data.name.strip() or "未命名企业")

    def _one(seat: Seat) -> SeatResult:
        try:
            if settings.mock and mock_stagger_sec > 0:
                delay = {"market": 0.3, "economy": 0.45, "roadmap": 0.6, "diagram": 0.75}.get(seat.key, 0.4)
                time.sleep(delay)
            content = run_seat(seat, ctx, settings, lambda k: _mock_seat(k, data))
            content = clean_seat_output(seat.key, content)
            return SeatResult(key=seat.key, title=seat.title, content=content, ok=True)
        except Exception as e:
            return SeatResult(key=seat.key, title=seat.title, content="", ok=False, error=str(e))

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_one, s): s for s in SEATS}
        for fut in as_completed(futs):
            result = fut.result()
            report.seats[result.key] = result
            if on_seat_done:
                on_seat_done(result.key, result)

    for s in SEATS:
        if s.key not in report.seats:
            report.seats[s.key] = SeatResult(s.key, s.title, "", ok=False, error="未完成")

    diag = report.seats.get("diagram")
    if diag and diag.content:
        report.mermaid = extract_mermaid(diag.content)

    frameworks = {
        k: (v.content if v and v.ok else f"（{k} 席失败：{(v.error if v else '无')}）")
        for k, v in report.seats.items()
    }

    template_doc = assemble_from_frameworks(
        name=report.name,
        industry=data.industry.strip() or "未指定",
        one_liner=data.one_liner.strip() or "（未填写）",
        location=data.location.strip(),
        actors=data.actors.strip(),
        market_fw=frameworks.get("market", ""),
        economy_fw=frameworks.get("economy", ""),
        roadmap_fw=frameworks.get("roadmap", ""),
        diagram_fw=frameworks.get("diagram", ""),
        headcount=data.headcount,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        education_mix=data.education_mix,
        brand_years=data.brand_years,
    )

    assembled = template_doc
    if (not settings.mock) and getattr(settings, "llm_assemble", False):
        try:
            llm_doc = run_assemble(ctx, frameworks, settings, template_doc)
            if assembled_looks_healthy(llm_doc):
                assembled = llm_doc
        except Exception:
            assembled = template_doc

    report.assembled_markdown = clean_assembled_document(assembled, report.mermaid)
    from_doc = extract_mermaid(report.assembled_markdown)
    if from_doc:
        report.mermaid = from_doc
        report.assembled_markdown = clean_assembled_document(report.assembled_markdown, report.mermaid)

    if not assembled_looks_healthy(report.assembled_markdown):
        report.assembled_markdown = clean_assembled_document(template_doc, report.mermaid)
        report.mermaid = extract_mermaid(report.assembled_markdown) or report.mermaid

    report.chart_bundle = extract_chart_bundle(frameworks.get("economy", ""), frameworks.get("roadmap", ""))
    try:
        report.chart_pngs = build_all_charts(report.chart_bundle)
    except Exception:
        report.chart_pngs = {}
    try:
        report.mermaid_png = mermaid_to_png(report.mermaid) if report.mermaid else None
    except Exception:
        report.mermaid_png = None

    report.market_meta = extract_market_meta(frameworks.get("market", ""))
    try:
        report.weight_png = fig_pillar_weights(report.market_meta) if report.market_meta else None
    except Exception:
        report.weight_png = None

    return report


def generate_report(data: EnterpriseInput, settings: Settings):
    from src.parse import parse_report

    multi = generate_multiseat(data, settings, mock_stagger_sec=0)
    return parse_report(multi.assembled_markdown)
