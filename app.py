from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import survey_options as opt
from src.config import load_settings, mask_key, save_env
from src.llm import chat_complete
from src.mermaid_view import mermaid_html
from src.pipeline import EnterpriseInput, generate_multiseat
from src.providers import PRESETS
from src.seats import SEATS
from src.ui_viz import (
    economy_cost_table_md,
    keywords_circles_html,
    parse_priority_blocks,
    pillars_table_md,
    strip_json_blocks,
    weight_method_html,
)

st.set_page_config(
    page_title="企析智体 CorpLens",
    page_icon="◈",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "企析智体 CorpLens\n企业转型需求分析智能体（公开演示版）",
    },
)

st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      header [data-testid="stToolbar"] {visibility: hidden; height: 0;}
      footer {visibility: hidden;}
      .stDeployButton {display: none !important;}
      div[data-testid="stStatusWidget"] {visibility: hidden;}
      div[data-baseweb="tab-list"] {
        gap: 1.25rem !important;
        flex-wrap: wrap !important;
        row-gap: 0.75rem !important;
        border-bottom: 1px solid #e5e7eb;
        padding: 0.35rem 0 0.6rem 0;
        margin-bottom: 1.25rem;
      }
      button[data-baseweb="tab"] {
        font-weight: 650 !important;
        font-size: 0.98rem !important;
        padding: 0.55rem 1rem !important;
      }
      .block-card {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin: 0.85rem 0 1.25rem 0;
        background: #fff;
      }
      .sec-title { font-size: 1.05rem; font-weight: 700; margin: 0.2rem 0 0.65rem 0; }
      .brand-line { font-size: 0.95rem; color: #64748B; margin-top: -0.4rem; margin-bottom: 0.8rem; }
      .prio-p0 {border-left: 5px solid #B91C1C; padding: 0.65rem 0.85rem; background:#FEF2F2; margin:0.4rem 0; border-radius:8px;}
      .prio-p1 {border-left: 5px solid #C2410C; padding: 0.65rem 0.85rem; background:#FFF7ED; margin:0.4rem 0; border-radius:8px;}
      .prio-p2 {border-left: 5px solid #A16207; padding: 0.65rem 0.85rem; background:#FFFBEB; margin:0.4rem 0; border-radius:8px;}
      .prio-p3 {border-left: 5px solid #64748B; padding: 0.65rem 0.85rem; background:#F8FAFC; margin:0.4rem 0; border-radius:8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# 公开演示模板：社区宠物洗护（非内部行业案例）
SAMPLE = EnterpriseInput(
    name="示例·邻里宠洗工作室",
    one_liner="到店 + 私域复购",
    industry="本地生活 / 到店服务",
    location="长三角（如杭州/上海周边） · 社区底商",
    actors="到店顾客（核心付费）、家属 / 陪同决策人、美团 / 点评等平台、本地竞品老店",
    status=(
        "社区宠物洗护小店，主要靠微信口头预约和老客转介绍。"
        "排班与服务记录散落在聊天记录里；高峰易改约冲突。"
        "想做复购提醒和轻预约，但不确定要不要先上美团扩量。"
    ),
    headcount="6",
    salary_min="4000",
    salary_max="8000",
    education_mix="熟练工 / 柜面较多、学徒不足、断层明显",
    brand_years="3–8年（站稳）",
    brand_notes="有固定老客群、视觉与IP尚未统一、核心卖点是认人认手艺 / 服务",
    policy_notes="门店卫生与用工、消防 / 场地证照、尚不清楚，需要排查",
    local_favor="本地信任强，认老店",
)

SAMPLE_CHOICES = {
    "industry": "本地生活 / 到店服务",
    "business_form": "到店 + 私域复购",
    "location_city": "长三角（如杭州/上海周边）",
    "location_scene": "社区底商",
    "actors_sel": [
        "到店顾客（核心付费）",
        "家属 / 陪同决策人",
        "美团 / 点评等平台",
        "本地竞品老店",
    ],
    "brand_years": "3–8年（站稳）",
    "brand_assets": ["有固定老客群", "视觉与IP尚未统一", "核心卖点是认人认手艺 / 服务"],
    "headcount_band": "4–8人",
    "salary_band": "中等（约4000–8000）",
    "education_sel": ["熟练工 / 柜面较多", "学徒不足、断层明显"],
    "policy_sel": ["用工与社保", "消防 / 场地证照", "尚不清楚，需要排查"],
    "local_favor": "本地信任强，认老店",
}

SEAT_META = {s.key: s for s in SEATS}


def _apply_sample_to_state() -> None:
    st.session_state["name"] = SAMPLE.name
    st.session_state["status"] = SAMPLE.status
    for k, v in SAMPLE_CHOICES.items():
        st.session_state[k] = v


def _collect_input_from_form() -> EnterpriseInput:
    name = (st.session_state.get("name") or "未命名企业").strip() or "未命名企业"
    status = (st.session_state.get("status") or "").strip()
    industry = st.session_state.get("industry") or "未指定"
    one_liner = opt.compose_one_liner(st.session_state.get("business_form") or "")
    location = opt.compose_location(
        st.session_state.get("location_city") or "",
        st.session_state.get("location_scene") or "",
    )
    actors = opt.join_multi(st.session_state.get("actors_sel") or [])
    brand_years = st.session_state.get("brand_years") or ""
    brand_notes = opt.join_multi(st.session_state.get("brand_assets") or [])
    head_band = st.session_state.get("headcount_band") or ""
    headcount = opt.HEADCOUNT_MAP.get(head_band, "")
    sal_band = st.session_state.get("salary_band") or ""
    smin, smax = opt.SALARY_MAP.get(sal_band, ("", ""))
    education_mix = opt.join_multi(st.session_state.get("education_sel") or [])
    policy_notes = opt.join_multi(st.session_state.get("policy_sel") or [])
    local_favor = st.session_state.get("local_favor") or ""
    return EnterpriseInput(
        name=name,
        industry=industry,
        one_liner=one_liner,
        status=status,
        location=location,
        actors=actors,
        headcount=headcount,
        salary_min=smin,
        salary_max=smax,
        education_mix=education_mix,
        brand_years=brand_years,
        brand_notes=brand_notes,
        policy_notes=policy_notes,
        local_favor=local_favor,
    )


def _api_panel() -> None:
    """首页顶部：接入 API。"""
    settings = load_settings()
    with st.container(border=True):
        st.markdown("### 接入大模型 API")
        st.caption(
            "Key 只写入本机 `.env`（已在 .gitignore，**不会也不应提交到 GitHub**）。"
            "无 Key 时自动示意模式。"
        )
        st.warning("上线公开仓库前请确认：从未把真实 API Key 写进 README / 截图 / 示例文件。")
        prov_keys = list(PRESETS.keys()) + ["custom"]
        labels = {k: PRESETS[k].title for k in PRESETS}
        labels["custom"] = "自定义 OpenAI 兼容接口"
        default_prov = settings.provider if settings.provider in prov_keys else "siliconflow"
        c1, c2 = st.columns([1.2, 1.8], gap="large")
        with c1:
            provider = st.selectbox(
                "服务商",
                prov_keys,
                index=prov_keys.index(default_prov),
                format_func=lambda k: labels[k],
                key="ui_provider",
            )
            use_live = st.toggle(
                "启用真模型（关闭则示意模式）",
                value=not settings.mock,
                key="ui_use_live",
            )
        with c2:
            preset = PRESETS.get(provider)
            api_key = st.text_input(
                "API Key",
                value=settings.api_key,
                type="password",
                placeholder="sk-…（仅保存在本机）",
                key="ui_api_key",
            )
            api_base = st.text_input(
                "API Base",
                value=settings.api_base or (preset.api_base if preset else ""),
                key="ui_api_base",
            )
            model = st.text_input(
                "模型名",
                value=settings.model or (preset.model if preset else ""),
                key="ui_model",
            )
            if preset:
                st.caption(f"{preset.note} · [开通入口]({preset.signup_url})")

        b1, b2, b3 = st.columns(3, gap="large")
        with b1:
            if st.button("保存到本机配置", use_container_width=True, type="primary"):
                save_env(
                    {
                        "TRANSFORM_AGENT_MOCK": "0" if use_live and api_key.strip() else "1",
                        "LLM_PROVIDER": provider,
                        "OPENAI_API_KEY": api_key.strip(),
                        "OPENAI_API_BASE": api_base.strip().rstrip("/"),
                        "OPENAI_MODEL": model.strip(),
                        "TRANSFORM_AGENT_LLM_ASSEMBLE": "0",
                    }
                )
                st.success(f"已保存到本机。Key 预览：{mask_key(api_key)}（完整 Key 不会显示在日志里）")
                st.rerun()
        with b2:
            if st.button("测试连接", use_container_width=True):
                if not api_key.strip():
                    st.warning("请先填写 API Key")
                else:
                    from src.config import Settings as S

                    trial = S(
                        mock=False,
                        api_base=api_base.strip().rstrip("/"),
                        api_key=api_key.strip(),
                        model=model.strip(),
                        provider=provider,
                        llm_assemble=False,
                    )
                    try:
                        msg = chat_complete(
                            trial, "用中文简短回答。", "只回复：接口连通。", max_tokens=32
                        )
                        st.success(f"连通成功：{msg[:80]}")
                    except Exception as e:
                        st.error(f"连接失败：{e}")
        with b3:
            st.caption(f"模式：{'真模型' if not settings.mock else '示意模板'}")
            st.caption("思考流已内嵌为通用 Skill（与演示行业无关）")


def _run_analysis(data: EnterpriseInput) -> None:
    settings = load_settings()
    status = st.status("企析智体 CorpLens 正在生成…", expanded=True)
    with status:
        try:
            report = generate_multiseat(data, settings, mock_stagger_sec=0.12)
        except Exception as e:
            status.update(label="分析失败", state="error")
            st.error(str(e))
            return
        for key in ["market", "economy", "roadmap", "diagram"]:
            r = report.seats.get(key)
            st.write(f"{'✓' if r and r.ok else '✗'} {SEAT_META[key].title}")
        status.update(label="生成完成", state="complete")
    st.session_state["multi_report"] = report
    st.session_state["last_input"] = data


def _split_markdown_keep_mermaid(md: str) -> list[tuple[str, str]]:
    import re

    parts: list[tuple[str, str]] = []
    pattern = re.compile(r"```mermaid\s*([\s\S]*?)```", re.I)
    last = 0
    for m in pattern.finditer(md or ""):
        if m.start() > last:
            parts.append(("md", md[last : m.start()]))
        parts.append(("mermaid", m.group(1).strip()))
        last = m.end()
    if last < len(md or ""):
        parts.append(("md", md[last:]))
    return parts or [("md", md or "")]


def _zip_bundle(report) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{report.name}_转型需求分析书.md".replace(" ", "_"), report.assembled_markdown)
        if report.mermaid_png:
            zf.writestr("流程图.png", report.mermaid_png)
        if report.weight_png:
            zf.writestr("图_三柱加权根因.png", report.weight_png)
        for key, png in (report.chart_pngs or {}).items():
            names = {
                "optimization": "图_预估优化比例.png",
                "marginal": "图_边际效益对比.png",
                "combo": "图_抓手组合效益.png",
            }
            zf.writestr(names.get(key, f"{key}.png"), png)
    return buf.getvalue()


def _render_product(report, last_input: EnterpriseInput | None) -> None:
    st.markdown('<div class="sec-title">转型需求分析书（草案）</div>', unsafe_allow_html=True)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### 核心关键词")
    mm = report.market_meta
    components.html(keywords_circles_html(mm.keywords if mm else []), height=150)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    for kind, payload in _split_markdown_keep_mermaid(report.assembled_markdown):
        if kind == "md":
            if payload.strip():
                st.markdown(payload)
        else:
            st.markdown("##### 流程对照图")
            if report.mermaid_png:
                st.image(report.mermaid_png, use_container_width=True)
            else:
                components.html(mermaid_html(payload), height=460, scrolling=True)
            with st.expander("流程图源码"):
                st.code(payload, language="mermaid")
    st.markdown("</div>", unsafe_allow_html=True)

    if report.weight_png:
        st.markdown('<div class="block-card">', unsafe_allow_html=True)
        st.markdown("##### 品牌 / 技术 / 创新力 · 加权根因")
        st.image(report.weight_png, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    pngs = report.chart_pngs or {}
    if pngs:
        st.markdown('<div class="block-card">', unsafe_allow_html=True)
        st.markdown("##### 优化比例与经济边际效益")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            if pngs.get("optimization"):
                st.image(pngs["optimization"], use_container_width=True)
            if pngs.get("combo"):
                st.image(pngs["combo"], use_container_width=True)
        with c2:
            if pngs.get("marginal"):
                st.image(pngs["marginal"], use_container_width=True)
        st.caption("图中指数为相对推断，用于排序讨论。")
        st.markdown("</div>", unsafe_allow_html=True)

    d1, d2 = st.columns(2, gap="large")
    with d1:
        st.download_button(
            "下载需求分析书（Markdown）",
            data=report.assembled_markdown.encode("utf-8"),
            file_name=f"{report.name}_转型需求分析书.md".replace(" ", "_"),
            mime="text/markdown",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "下载完整包（文稿+图）",
            data=_zip_bundle(report),
            file_name=f"{report.name}_转型分析包.zip".replace(" ", "_"),
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )


def _render_market(report) -> None:
    from src.ui_viz import extract_market_meta

    st.markdown('<div class="sec-title">市场切入 · 分席细读</div>', unsafe_allow_html=True)
    r = report.seats.get("market")
    if not r or not r.ok:
        st.error((r.error if r else "无结果") or "失败")
        return
    mm = report.market_meta or extract_market_meta(r.content)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ① 关键词聚焦")
    components.html(keywords_circles_html(mm.keywords), height=150)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ② 计算方式与思考过程")
    components.html(weight_method_html(mm), height=220)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ③ 加权结果")
    if report.weight_png:
        st.image(report.weight_png, use_container_width=True)
    if mm.pillars:
        st.markdown(pillars_table_md(mm))
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ④ 框架正文")
    st.markdown(strip_json_blocks(r.content))
    with st.expander("机器数据 JSON（调试）"):
        if "```json" in r.content:
            st.code(r.content[r.content.find("```json") :], language="json")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_economy(report, last_input: EnterpriseInput | None) -> None:
    st.markdown('<div class="sec-title">经济效益 · 分席细读</div>', unsafe_allow_html=True)
    r = report.seats.get("economy")
    if not r or not r.ok:
        st.error((r.error if r else "无结果") or "失败")
        return
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ① 人力成本速算表")
    if last_input:
        st.markdown(
            economy_cost_table_md(last_input.headcount, last_input.salary_min, last_input.salary_max)
        )
    st.markdown("</div>", unsafe_allow_html=True)
    pngs = report.chart_pngs or {}
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ② 效益图")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        if pngs.get("optimization"):
            st.image(pngs["optimization"], use_container_width=True)
    with c2:
        if pngs.get("marginal"):
            st.image(pngs["marginal"], use_container_width=True)
    if pngs.get("combo"):
        st.image(pngs["combo"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ③ 框架正文")
    st.markdown(strip_json_blocks(r.content))
    st.markdown("</div>", unsafe_allow_html=True)


def _render_roadmap(report) -> None:
    st.markdown('<div class="sec-title">实现创新 · 分席细读</div>', unsafe_allow_html=True)
    r = report.seats.get("roadmap")
    if not r or not r.ok:
        st.error((r.error if r else "无结果") or "失败")
        return
    prios = parse_priority_blocks(r.content)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ① 优先级（P0–P3）")
    if prios:
        for p in prios:
            cls = {"P0": "prio-p0", "P1": "prio-p1", "P2": "prio-p2", "P3": "prio-p3"}.get(
                p["level"], "prio-p3"
            )
            st.markdown(
                f"<div class='{cls}'><b>{p['level']}</b>　{p['text']}</div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.markdown("##### ② 完整正文")
    st.markdown(r.content)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_report(report) -> None:
    last_input = st.session_state.get("last_input")
    st.success("已生成。默认看「需求分析书」；其余为分席细读。")
    tabs = st.tabs(["需求分析书", "市场切入", "经济效益", "实现创新"])
    with tabs[0]:
        _render_product(report, last_input)
    with tabs[1]:
        _render_market(report)
    with tabs[2]:
        _render_economy(report, last_input)
    with tabs[3]:
        _render_roadmap(report)


def _survey_form() -> None:
    st.markdown("#### 调查输入")
    st.caption("仅名称与状态手填，其余单选/多选。")
    st.text_input("企业/项目名称", key="name", placeholder="例如：邻里宠洗工作室")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.selectbox("行业", opt.INDUSTRY, key="industry")
        st.selectbox("业务形态（一句话）", opt.BUSINESS_FORM, key="business_form")
        st.selectbox("地理区域", opt.LOCATION_CITY, key="location_city")
        st.selectbox("点位场景", opt.LOCATION_SCENE, key="location_scene")
        st.multiselect("市场主体（可多选）", opt.ACTORS, key="actors_sel")
        st.selectbox("品牌年限 / 老字号", opt.BRAND_YEARS, key="brand_years")
    with c2:
        st.selectbox("在职人数", opt.HEADCOUNT, key="headcount_band")
        st.selectbox("薪资带", opt.SALARY_BAND, key="salary_band")
        st.multiselect("教育 / 岗位结构", opt.EDU_MIX, key="education_sel")
        st.multiselect("品牌与工艺资产", opt.BRAND_ASSETS, key="brand_assets")
        st.multiselect("政策关注点", opt.POLICY, key="policy_sel")
        st.selectbox("地方好感度 / 文化", opt.LOCAL_FAVOR, key="local_favor")
    st.text_area("当前状态描述", key="status", height=140, placeholder="痛点、人手、想守住的卖点…")


def main() -> None:
    st.title("企析智体")
    st.markdown(
        '<div class="brand-line">CorpLens · 企业转型需求分析智能体（公开演示版）</div>',
        unsafe_allow_html=True,
    )

    _api_panel()
    st.divider()

    settings = load_settings()
    if settings.mock:
        st.info("当前为示意模式。可在上方接入 API 后开启真模型，或直接点演示。")
    else:
        st.info(f"当前真模型：{settings.provider} / {settings.model}")

    with st.sidebar:
        st.header("CorpLens")
        st.markdown(
            "辩证思考流已内嵌为通用 Skill（`prompts/skills/`），"
            "演示行业是宠物洗护，与内部案例无关。"
        )
        st.caption("API Key 仅存本机 .env，切勿提交 GitHub。")

    b1, b2 = st.columns([2, 1], gap="large")
    with b1:
        demo = st.button("一键生成演示（邻里宠洗）", type="primary", use_container_width=True)
    with b2:
        clear = st.button("清空结果", use_container_width=True)

    if clear:
        st.session_state.pop("multi_report", None)
        st.session_state.pop("last_input", None)
        st.rerun()
    if demo:
        _apply_sample_to_state()
        _run_analysis(SAMPLE)
        st.rerun()

    st.divider()
    _survey_form()
    if st.button("根据上方调查生成", use_container_width=True):
        data = _collect_input_from_form()
        if not data.name.strip() and not data.status.strip():
            st.warning("请填写企业名称或状态描述。")
        else:
            _run_analysis(data)
            st.rerun()

    report = st.session_state.get("multi_report")
    if not report:
        st.divider()
        st.warning("尚未生成。请先演示，或接入 API 后调查生成。")
        return
    st.divider()
    _render_report(report)


if __name__ == "__main__":
    main()
