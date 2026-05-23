import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import macro_functions as mf
from generalities.dictionaries import presidents, months
from generalities.function import find_key_by_value, to_datatime, reshape_by_presidents, load_csv, BASE_DIR
import generalities.inflation as gi

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

    st.title("CPI")

    col1, col2, col3, col4 = st.columns(4)

    # Placeholders reserve sidebar slots in order: selects on top, radio/checkbox below
    top_placeholder = st.sidebar.empty()
    city_cat_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    pers_names = gi.perspective_names
    meth_names = gi.method_names

    with col1:
        method = st.selectbox("Method:", meth_names)

    if method == meth_names[0]:
        with col2:
            view = st.selectbox("View:", ["Total", "Per City", "Per Category"])

        with col3:
            perspective = st.selectbox("Perspective:", pers_names.values())

        perspective_column = find_key_by_value(pers_names, perspective)

        cfg = VIEW_CONFIG.get(view)

        # Default time-unit per perspective; the comparison option pivots on the view label
        default_unit = "Month" if perspective == "Annual" else "Year"

        # Render radio first (need its value), but it appears below placeholders visually
        if cfg:
            with st.sidebar:
                compare_by = st.radio("Compare by:", [default_unit, cfg["label"]], horizontal=True)
        else:
            compare_by = default_unit

        comparing = cfg is not None and compare_by == cfg["label"]

        if cfg:
            display = list(cfg["items_dict"].values())
            if comparing:
                with city_cat_placeholder.container():
                    selected_items = st.multiselect(f"{cfg['label']}s:", display, default=[cfg["default"]])

                    if not selected_items:
                        selected_items = [cfg["default"]]

                sidebar_df = cpi_local
            else:
                with city_cat_placeholder.container():
                    selected_item = st.selectbox(cfg["label"] + ":", display, index=display.index(cfg["default"]))

                key = find_key_by_value(cfg["items_dict"], selected_item)
                data_df = to_datatime(load_csv(f"{cfg['base_path']}{key}.csv"), False)
                sidebar_df = data_df
        else:
            data_df = cpi_local
            sidebar_df = cpi_local

        selected_presidents, chart_type = mf.cpi_sidebar_filters(
            sidebar_df, top_placeholder, president_placeholder
        )
        president = selected_presidents[0] if len(selected_presidents) == 1 else None
        multi_pres = len(selected_presidents) >= 2

        subtitle = selected_item if (cfg and not comparing) else None

        if comparing:
            if perspective == "Annual":
                with col4:
                    selected_month = st.selectbox("Month:", list(months.values()), index=list(months.values()).index("December"))

                fixed_value = find_key_by_value(months, selected_month)

                compare_pres = multi_pres
                if compare_pres:
                    show_all = True
                else:
                    with st.sidebar:
                        show_all = st.checkbox("Show all years", value=False)
            else:
                years = cpi_local.index.year.unique().astype(int)
                with col4:
                    fixed_value = st.selectbox("Year:", sorted(years, reverse=True))

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
            years = data_df.index.year.unique().astype(int)
            with col4:
                if president:
                    pres_years = [y for y in years if y in set(presidents[president])]
                    selected_year = st.multiselect("Year:", sorted(pres_years, reverse=True))

                    if not selected_year:
                        selected_year = pres_years
                else:
                    selected_year = st.multiselect("Year:", sorted(years, reverse=True), default=years[-1])

                    if not selected_year:
                        selected_year = [years[-1]]

            cpi_series, cpi_info = mf.build_yearly_table(data_df, selected_year, perspective_column, method, subtitle=subtitle)
    else:
        with col2:
            core_items = st.selectbox("Exclude items:", [15, 20])

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

    highlight = None
    if len(cpi_series.columns) > 1:
        display_names = [str(col) for col in cpi_series.columns]
        with st.sidebar:
            highlight_choice = st.selectbox("Highlight variable:", ["—"] + display_names)
            highlight = None if highlight_choice == "—" else highlight_choice

    if chart_type == "Bar" or len(cpi_series) == 1:
        fig = mc.bar_chart(cpi_series, {}, cpi_info, highlight=highlight)
    else:
        fig = mc.line_chart(cpi_series, {}, cpi_info, highlight=highlight)

    st.plotly_chart(fig)
    st.caption("Base 2018")
    st.caption("Source: DANE, Banco de la República")
