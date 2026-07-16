import streamlit as st
import pandas as pd
from pages.helpers import charts as mc
from pages.helpers import charts as dc
from pages.helpers.demography import population_functions as pop
from generalities.dictionaries import presidents
from generalities.function import highlight_selectbox
from generalities.demography_generalities.population import PREV_YEAR, MEN_COLOR, WOMEN_COLOR, PROJECTED_NOTE, PYRAMID_MODES


def _share_card(col, label: str, pct: float, color: str) -> None:
    col.markdown(
        f"<div style='text-align:center;font-size:0.875rem;opacity:0.6'>{label}</div>"
        f"<div style='text-align:center;font-size:2.25rem;font-weight:600;color:{color}'>{pct:.1f}%</div>",
        unsafe_allow_html=True,
    )


def _render_pyramid_result(men: pd.Series, women: pd.Series, mode: str, title: str) -> bool:
    if men.sum() == 0 and women.sum() == 0:
        st.warning("No data for selected filters.")
        return False

    total_men, total_women = men.sum(), women.sum()
    total = total_men + total_women

    _, c_men, c_women, _ = st.columns([1, 2, 2, 1])
    _share_card(c_men, f"{men.name} share", total_men / total * 100, MEN_COLOR)
    _share_card(c_women, f"{women.name} share", total_women / total * 100, WOMEN_COLOR)

    men_name, women_name = men.name, women.name
    if mode == "% within age group":
        bucket = (men + women).replace(0, 1)
        men, women = men / bucket * 100, women / bucket * 100
        value_label, valueformat = "Share within age group (%)", ".1f"
    elif mode == "% of total population":
        men, women = men / total * 100, women / total * 100
        value_label, valueformat = "Share of total population (%)", ".2f"
    else:
        value_label, valueformat = "People", ",.0f"
    men.name, women.name = men_name, women_name

    fig = dc.population_pyramid(men, women, [title, value_label, valueformat])
    mc.render_chart(fig)
    return True


def _render_pyramid(df, scope_label: str = None, entity: dict = None) -> None:
    if entity:
        c0, c1 = st.columns(2)
        with c0:
            sel = st.selectbox(f"{entity['label']}:", entity["options"])
        with c1:
            mode = st.selectbox("Display:", PYRAMID_MODES)
        df = df[df[entity["column"]] == sel]
        scope_label = sel
    else:
        mode = st.selectbox("Display:", PYRAMID_MODES)

    years = sorted(df["AÑO"].unique().astype(int), reverse=True)
    default = years.index(PREV_YEAR) if PREV_YEAR in years else 0

    with st.sidebar:
        year = st.selectbox("Year:", years, index=default)

    men, women = pop.pyramid_rows(df[df["AÑO"] == year])
    projected = year > PREV_YEAR
    title = f"Population pyramid — {scope_label}, {year}" + (" — projected" if projected else "")

    if not _render_pyramid_result(men, women, mode, title):
        return

    if projected:
        st.caption("Projected (expected) data.")
        st.caption(PROJECTED_NOTE)
    st.caption("Source: DANE")


def _render_pop_geo_chart(pivot, chart_type, entity, noun, president) -> None:
    if president:
        pivot = pivot[pivot.index.isin(presidents[president])]

    if pivot.empty:
        st.warning("No data for selected filters.")
        return

    info = [f"{noun} by {entity}", "Year", noun]
    highlight = highlight_selectbox(pivot)
    if len(pivot) == 1:
        fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight)
    elif chart_type == "Bar":
        fig = mc.bar_chart(pivot, {}, info, highlight=highlight)
    else:
        fig = dc.projection_line(pivot, info, split_year=PREV_YEAR, highlight=highlight)
    mc.render_chart(fig)


def _render_geo_bar_line(pivot, chart_type: str, entity: str, scope: str, noun: str = "Births") -> None:
    if pivot.empty:
        st.warning("No data for selected filters.")
        return

    if chart_type == "Bar" or len(pivot) == 1:
        info = [f"Total {noun.lower()} by {entity} — {scope}", noun, entity.capitalize()]
        fig = mc.ranked_bar_chart(pivot.sum(axis=0), info)
    else:
        highlight = highlight_selectbox(pivot)
        info = [f"{noun} trend by {entity}", "Year", noun]
        fig = mc.line_chart(pivot, {}, info, highlight=highlight)

    mc.render_chart(fig)
