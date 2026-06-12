import streamlit as st
from pages.helpers.macro import macro_charts as mc
from pages.helpers.demography import demography_charts as dc
from pages.helpers.demography import population_functions as pop
from generalities.macro_generalities.dictionaries import presidents
from generalities.function import highlight_selectbox
from generalities.demography_generalities.population import PREV_YEAR

PROJECTED_NOTE = ("Projected data is based on the 2018 National Population and Housing Census (CNPV), "
                  "updated with information following the COVID-19 pandemic.")


def _render_pyramid(df, scope_label: str) -> None:
    years = sorted(df["AÑO"].unique().astype(int), reverse=True)
    default = years.index(PREV_YEAR) if PREV_YEAR in years else 0

    with st.sidebar:
        year = st.selectbox("Year:", years, index=default)

    men, women = pop.pyramid_rows(df[df["AÑO"] == year])

    if men.sum() == 0 and women.sum() == 0:
        st.warning("No data for selected filters.")
        return

    title = f"Population pyramid — {scope_label}, {year}"
    fig = dc.population_pyramid(men, women, [title], projected=year > PREV_YEAR)
    mc.render_chart(fig)
    if year > PREV_YEAR:
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
