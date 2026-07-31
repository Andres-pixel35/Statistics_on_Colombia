import streamlit as st
from app_pages.helpers import charts as mc
from app_pages.helpers.poverty import poverty_functions as pvf
import generalities.poverty_generalities.poverty as pv
from generalities.i18n import t
from generalities.function import load_csv, highlight_selectbox, find_key_by_value


def render_profile() -> None:
    st.title(t("Poverty by Household Profile"))

    col1, col2, col3 = st.columns(3)
    table = col1.selectbox(t("Table:"), list(pv.PROFILE_FILES.keys()), format_func=t)
    ptype = col2.selectbox(t("Type:"), list(pv.PROFILE_TYPES.keys()), format_func=t)
    df = load_csv(pv.POVERTY_BASE / pv.PROFILE_FILES[table] / pv.PROFILE_TYPES[ptype])
    df["Categoria"] = df["Categoria"].fillna("Total")   # the Total group has no category

    domains = list(df.columns[3:])
    domain = col3.selectbox(t("Domain:"), [pv.domain_label(d) for d in domains],
                            index=domains.index(pv.DEFAULT_DOMAIN), format_func=t)
    domain_sp = find_key_by_value({d: pv.domain_label(d) for d in domains}, domain)

    grupos = list(dict.fromkeys(df["Grupo"]))
    st.sidebar.header(t("Filters"))
    grupo = st.sidebar.selectbox(t("Characteristic:"), [pv.GRUPO_EN.get(g, g) for g in grupos], format_func=t)
    grupo_sp = find_key_by_value({g: pv.GRUPO_EN.get(g, g) for g in grupos}, grupo)
    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Bar", "Line"], format_func=t)
    years = sorted(df["Fecha"].unique())
    # Default to the two most recent years; the picker still offers every year in the file,
    # so added years show up without defaulting into an ever-wider chart.
    sel_years = st.sidebar.multiselect(t("Year:"), years, default=years[-2:], key="pov_profile_years")
    if not sel_years:
        sel_years = years[-2:]

    series = pvf.profile_pivot(df, grupo_sp, domain_sp, sel_years)
    series.index = [pv.CATEGORIA_EN.get(c, c) for c in series.index]

    info = [f"{t(grupo)} — {t(table)}, {t(ptype)} · {t(domain)}", "Category", "% of population"]
    highlight = highlight_selectbox(series)
    mc.render_chart(mc.line_or_bar(chart_type, series, info, highlight=highlight))
    st.caption(t("Source: DANE — Pobreza Monetaria"))
