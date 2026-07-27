import streamlit as st
from pages.helpers import charts as mc
from pages.helpers.poverty import poverty_functions as pvf
import generalities.poverty_generalities.poverty as pv
from generalities.function import load_csv, highlight_selectbox


def render_by_sex() -> None:
    st.title("Poverty by Sex")

    col1, col2 = st.columns(2)
    ptype = col1.selectbox("Type:", list(pv.PROFILE_TYPES.keys()))
    df = load_csv(pv.POVERTY_BASE / "sexo" / pv.PROFILE_TYPES[ptype])
    years = sorted(df["Fecha"].unique())
    year = col2.selectbox("Year:", years, index=len(years) - 1)

    labels = {pv.domain_label(col): col for col in df.columns[2:]}
    defaults = [pv.domain_label(d) for d in pv.AGGREGATE_DOMAINS]

    st.sidebar.header("Filters")
    chart_type = st.sidebar.selectbox("Chart Type:", ["Bar", "Line"])
    selected = st.sidebar.multiselect("Domain:", list(labels.keys()), default=defaults,
                                      key="pov_sex_domains")
    if not selected:
        selected = defaults

    series = pvf.sexo_pivot(df, [labels[s] for s in selected], year, pv.SEXO_EN)
    series.index = selected

    info = [f"Poverty Incidence — {ptype} · {year}", "Domain", "% of population"]
    highlight = highlight_selectbox(series)
    mc.render_chart(mc.line_or_bar(chart_type, series, info, highlight=highlight))
    st.caption("Source: DANE — Pobreza Monetaria")
