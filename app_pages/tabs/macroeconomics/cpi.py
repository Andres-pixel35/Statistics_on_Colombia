import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.macro import cpi_functions as mf
from generalities.dictionaries import presidents, months
from generalities.function import find_key_by_value, to_datatime, reshape_by_presidents, load_csv, BASE_DIR, highlight_selectbox
import generalities.macro_generalities.inflation as gi
from generalities.i18n import t

CPI_15_PATH = BASE_DIR / "data/banco_republica/CPI/inflacion_15.csv"
CPI_20_PATH = BASE_DIR / "data/banco_republica/CPI/inflacion_20.csv"
CITY_BASE   = str(BASE_DIR / "data/banco_republica/CPI/city") + "/"
CAT_BASE    = str(BASE_DIR / "data/banco_republica/CPI/spend_category") + "/"

VIEW_CONFIG = {
    "Per City": {
        "items_dict": gi.city_files,
        "base_path": CITY_BASE,
        "default": "Bogotá, D.C",
        "label": "City",
    },
    "Per Category": {
        "items_dict": gi.spend_category_names,
        "base_path": CAT_BASE,
        "default": "Education",
        "label": "Category",
    },
}

def render_cpi(cpi_df: pd.DataFrame) -> None:
    cpi_local = to_datatime(cpi_df, False)

    st.title(t("CPI"))

    col1, col2, col3, col4 = st.columns(4)

    # Placeholders reserve sidebar slots in order: selects on top, radio/checkbox below
    top_placeholder = st.sidebar.empty()
    city_cat_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    pers_names = gi.perspective_names
    meth_names = gi.method_names

    with col1:
        method = st.selectbox(t("Method:"), meth_names, format_func=t)

    if method == meth_names[0]:
        with col2:
            view = st.selectbox(t("View:"), ["Total", "Per City", "Per Category"], format_func=t)

        with col3:
            perspective = st.selectbox(t("Perspective:"), pers_names.values(), format_func=t)

        perspective_column = find_key_by_value(pers_names, perspective)

        cfg = VIEW_CONFIG.get(view)

        # Default time-unit per perspective; the comparison option pivots on the view label
        default_unit = "Month" if perspective == "Annual" else "Year"

        # Render radio first (need its value), but it appears below placeholders visually
        if cfg:
            comparing_dim = st.session_state.get("cpi_comparing_dim", False)
            options = [default_unit, cfg["label"]]
            with st.sidebar:
                compare_by = st.radio(
                    t("Compare by:"), options, horizontal=True,
                    index=1 if comparing_dim else 0, format_func=t,
                )
            st.session_state["cpi_comparing_dim"] = compare_by == cfg["label"]
        else:
            compare_by = default_unit

        comparing = cfg is not None and compare_by == cfg["label"]

        if cfg:
            display = list(cfg["items_dict"].values())
            if comparing:
                with city_cat_placeholder.container():
                    selected_items = st.multiselect(t(f"{cfg['label']}s:"), display, default=[cfg["default"]], format_func=t)

                    if not selected_items:
                        selected_items = [cfg["default"]]

                sidebar_df = pd.concat([
                    to_datatime(load_csv(f"{cfg['base_path']}{find_key_by_value(cfg['items_dict'], name)}.csv"), False)
                    for name in selected_items
                ])
            else:
                with city_cat_placeholder.container():
                    selected_item = st.selectbox(t(cfg["label"] + ":"), display, index=display.index(cfg["default"]), format_func=t)

                key = find_key_by_value(cfg["items_dict"], selected_item)
                data_df = to_datatime(load_csv(f"{cfg['base_path']}{key}.csv"), False)
                sidebar_df = data_df
        else:
            data_df = cpi_local
            sidebar_df = cpi_local

        if perspective != "Annual" and cfg is not None and comparing:
            pres_mode = "hidden"
        elif perspective != "Annual":
            pres_mode = "single"
        else:
            pres_mode = "multi"

        selected_presidents, chart_type = mf.cpi_sidebar_filters(
            sidebar_df, top_placeholder, president_placeholder, pres_mode
        )
        president = selected_presidents[0] if len(selected_presidents) == 1 else None
        multi_pres = len(selected_presidents) >= 2

        subtitle = selected_item if (cfg and not comparing) else None

        if comparing:
            if perspective == "Annual":
                with col4:
                    selected_month = st.selectbox(t("Month:"), list(months.values()), index=list(months.values()).index("December"), format_func=t)

                fixed_value = find_key_by_value(months, selected_month)

                compare_pres = multi_pres
                if compare_pres:
                    show_all = True
                else:
                    has_pre_2000 = sidebar_df[perspective_column].dropna().index.year.min() < 2000
                    if has_pre_2000:
                        with st.sidebar:
                            show_all = st.checkbox(t("Show all years"), value=False)
                    else:
                        show_all = False
            else:
                year_set = set(sidebar_df[perspective_column].dropna().index.year.astype(int))
                years = sorted(year_set, reverse=True)
                with col4:
                    fixed_value = st.selectbox(t("Year:"), years)

                show_all = False
                compare_pres = False

            cpi_series, cpi_info = mf.build_comparison_series(
                selected_items, cfg["items_dict"], cfg["base_path"], perspective_column,
                perspective, fixed_value, None if compare_pres else president, show_all, method,
            )
            if compare_pres:
                cpi_series, cpi_info = reshape_by_presidents(cpi_series, selected_presidents, cpi_info)
        elif perspective == "Annual":
            compare_pres = multi_pres
            with col4:
                cpi_series, cpi_info = mf.build_cpi_series(
                    data_df, cpi_local,
                    [perspective_column, None if compare_pres else president, method],
                    subtitle=subtitle,
                    flags=[view == "Per Category", view != "Total"],
                    comparing=compare_pres,
                )
            if compare_pres:
                cpi_series, cpi_info = reshape_by_presidents(cpi_series, selected_presidents, cpi_info)
        else:
            years = data_df[perspective_column].dropna().index.year.unique().astype(int)
            with col4:
                if president:
                    pres_years = [y for y in years if y in set(presidents[president])]
                    selected_year = st.multiselect(t("Year:"), sorted(pres_years, reverse=True))

                    if not selected_year:
                        selected_year = pres_years
                else:
                    selected_year = st.multiselect(t("Year:"), sorted(years, reverse=True), default=years[-1])

                    if not selected_year:
                        selected_year = [years[-1]]

            cpi_series, cpi_info = mf.build_yearly_table(data_df, selected_year, perspective_column, method, subtitle=subtitle)
    else:
        with col2:
            core_items = st.selectbox(t("Exclude items:"), [15, 20])

        path = CPI_15_PATH if core_items == 15 else CPI_20_PATH
        cpi_core = load_csv(path)
        cpi_core = to_datatime(cpi_core, True)

        selected_presidents, chart_type = mf.cpi_sidebar_filters(cpi_core, top_placeholder, president_placeholder)
        president = selected_presidents[0] if len(selected_presidents) == 1 else None
        multi_pres = len(selected_presidents) >= 2

        with col3:
            cpi_series, cpi_info = mf.build_cpi_series(
                cpi_core, cpi_local,
                ["Inflación", None if multi_pres else president, method],
                flags=[False, True], comparing=multi_pres,
            )
        if multi_pres:
            cpi_series, cpi_info = reshape_by_presidents(cpi_series, selected_presidents, cpi_info)

    highlight = highlight_selectbox(cpi_series)

    fig = mc.line_or_bar(chart_type, cpi_series, cpi_info, highlight=highlight)

    mc.render_chart(fig)
    st.caption(t("Base 2018"))
    st.caption(t("Source: DANE, Banco de la República"))
