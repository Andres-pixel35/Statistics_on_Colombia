import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_DELTA_COLORS = {True: ("#16a34a", "rgba(22,163,74,0.12)"), False: ("#dc2626", "rgba(220,38,38,0.12)"),
                  None: ("#6b7280", "rgba(107,114,128,0.12)")}


def sparkline(values: pd.Series, color: str) -> go.Figure:
    """Bare trend line: no axes, grid, legend, or margins."""
    fig = go.Figure(go.Scatter(y=values.to_numpy(), mode="lines", line=dict(color=color, width=1.5)))
    fig.update_layout(
        height=35, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def render_kpi_card(col, cfg: dict, key: str = None) -> None:
    """Render one KPI card. cfg keys: title, value, delta_text, delta_good, metadata, accent, spark.
    `key` disambiguates the sparkline when the same cfg is rendered more than once (e.g. headline + section)."""
    text_color, bg_color = _DELTA_COLORS[cfg["delta_good"]]
    with col, st.container(border=True):
        st.markdown(
            f'<span style="color:{cfg["accent"]};font-size:14px;font-weight:600;">{cfg["title"]}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div style="font-size:42px;font-weight:700;line-height:1.2;">{cfg["value"]}</div>',
                    unsafe_allow_html=True)
        if cfg["delta_text"]:
            st.markdown(
                f'<span style="color:{text_color};background:{bg_color};font-size:13px;'
                f'font-weight:600;padding:2px 8px;border-radius:999px;">{cfg["delta_text"]}</span>',
                unsafe_allow_html=True,
            )
        st.caption(cfg["metadata"])
        spark = cfg.get("spark")
        if spark is not None and len(spark) > 1:
            st.plotly_chart(sparkline(spark, cfg["accent"]), config={"displayModeBar": False},
                             width="stretch", key=key)


def render_kpi_grid(cfgs: list, per_row: int = 4, key_prefix: str = "grid") -> None:
    """Render KPI cards in rows of `per_row` columns."""
    for i in range(0, len(cfgs), per_row):
        row = cfgs[i:i + per_row]
        cols = st.columns(per_row)
        for j, (col, cfg) in enumerate(zip(cols, row)):
            render_kpi_card(col, cfg, key=f"{key_prefix}_{i + j}_{cfg['title']}")


def render_section(section: dict) -> None:
    """Topic section. section keys: title, description, cfgs, page (optional), expanded (default False)."""
    with st.expander(section["title"], expanded=section.get("expanded", False)):
        st.caption(section["description"])
        render_kpi_grid(section["cfgs"], key_prefix=section["title"])
        if section.get("page"):
            st.page_link(section["page"], label="View full dashboard")
