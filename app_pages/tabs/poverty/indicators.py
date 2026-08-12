import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers import charts as dc
from app_pages.helpers.poverty import poverty_functions as pvf
import generalities.poverty_generalities.poverty as pv
from generalities.i18n import t
from generalities.dictionaries import presidents
from generalities.function import (load_csv, load_geojson, highlight_selectbox,
                                   get_valid_presidents, president_multiselect,
                                   reshape_by_presidents, cap_one as _cap_one)


def render_indicators() -> None:
    st.title(t("Poverty Indicators"))

    st.sidebar.header(t("Filters"))
    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar", "Table", "Map"], format_func=t)
    is_map = chart_type == "Map"

    col1, col2 = st.columns(2)
    metric = col1.selectbox(t("Metric:"), list(pv.METRICS.keys()), format_func=t)
    cfg = pv.METRICS[metric]
    types = list(cfg["paths"].keys())
    # Gini / Per-capita Income have a single type: no selectbox, nothing to compare.
    comparing_types = (not is_map) and len(types) > 1 and st.session_state.get("pov_compare", False)
    ptype = types[0] if len(types) == 1 else col2.selectbox(
        t("Type:"), types, disabled=comparing_types, format_func=t)

    df = load_csv(pv.POVERTY_BASE / cfg["paths"][ptype])
    labels = {pv.domain_label(col): col for col in df.columns[1:]}
    years = sorted(df["Fecha"].unique())
    title_base = t(metric) if len(types) == 1 else f"{t(metric)} — {t(ptype)}"

    if is_map:
        # The map shows all 23 capital cities at once, so Domain is ignored and the year
        # is single-select (a choropleth is one year by definition).
        year = st.sidebar.selectbox(t("Year:"), years, index=len(years) - 1)
        geojson = load_geojson(pv.DEPT_GEOJSON_PATH)
        data = pvf.map_data(df, year, pv.CITY_DPTO)
        data["value"] = data["value"] / cfg.get("scale", 1)
        info = [f"{title_base} · {year}", "Capital city", cfg["unit"]]
        fig = dc.colombia_choropleth(data, geojson, pv.DEPT_FEATURE_KEY, "value", info,
                                     val_fmt=cfg["fmt"])
        mc.render_chart(fig)
        st.caption(t("Values are measured for the **capital city**, drawn on its department's "
                   "shape — they are not department-wide figures. Departments in grey have no "
                   "surveyed capital for the selected year."))
        st.caption(t("Source: DANE — Pobreza Monetaria"))
        return

    if comparing_types:
        _cap_one(["pov_domains"])
    selected = st.sidebar.multiselect(t("Domain:"), list(labels.keys()),
                                      default=[pv.domain_label(pv.DEFAULT_DOMAIN)],
                                      key="pov_domains", format_func=t)
    if not selected:
        selected = [pv.domain_label(pv.DEFAULT_DOMAIN)]
    domains = [labels[label] for label in selected]
    cur_years = st.sidebar.multiselect(t("Year:"), years, key="pov_years")
    with st.sidebar:
        selected_presidents = president_multiselect(get_valid_presidents(years),
                                                    key="pov_presidents")
        if len(types) > 1:
            st.checkbox(t("Compare monetary vs. extreme"), key="pov_compare")

    year_set = set(cur_years)
    for name in selected_presidents:
        year_set.update(set(presidents[name]) & set(years))

    if comparing_types:
        series = pd.concat(
            {t: pvf.domain_pivot(load_csv(pv.POVERTY_BASE / rel), domains, year_set)[domains[0]]
             for t, rel in cfg["paths"].items()}, axis=1)
        title = f"{t(metric)} · {t(selected[0])}"
    else:
        series = pvf.domain_pivot(df, domains, year_set).rename(
            columns={v: k for k, v in labels.items()})
        title = title_base

    series = series / cfg.get("scale", 1)
    info = [title, "Year", cfg["unit"]]
    if len(selected_presidents) >= 2:
        series, info = reshape_by_presidents(series, selected_presidents, info)
    elif len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    highlight = highlight_selectbox(series)
    mc.render_chart(mc.line_or_bar(chart_type, series, info, highlight=highlight))
    st.caption(t("Source: DANE — Pobreza Monetaria"))
