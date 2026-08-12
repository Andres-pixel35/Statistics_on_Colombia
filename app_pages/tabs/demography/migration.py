import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers import charts as dc
from app_pages.helpers.demography import migration_functions as mig
from generalities.dictionaries import presidents, months
from generalities.function import get_valid_presidents, find_key_by_value, president_multiselect, reshape_by_presidents, load_csv, BASE_DIR, highlight_selectbox
from generalities.demography_generalities.migration import COUNTRY_EN, METRIC_LABEL, COL_MAP
from generalities.i18n import t

MIGRATION_PATH = BASE_DIR / "data/datos_abiertos/migration.csv"


def render_migration() -> None:
    migration_df = load_csv(MIGRATION_PATH)
    migration_df["Fecha"] = pd.to_datetime(migration_df["Fecha"])

    st.title(t("Migration"))

    with st.sidebar:
        st.header(t("Filters"))
        chart_type = st.selectbox(t("Chart Type:"), ["Map", "Line", "Bar", "Table"], format_func=t)

    all_years = sorted(migration_df["Fecha"].dt.year.unique().tolist(), reverse=True)
    valid_pres = get_valid_presidents(all_years)

    if chart_type == "Map":
        _render_map(migration_df, all_years)
    else:
        _render_line_bar(migration_df, chart_type, all_years, valid_pres)

    st.caption(t("Inbound is foreing people coming into Colombia. Outbound is colombians leaving the country."))
    st.caption(t("Source: Migración Colombia"))


def _render_map(migration_df, all_years):
    col1, col2, col3 = st.columns(3)

    with col1:
        direction = st.selectbox(t("Direction:"), ["Inbound", "Outbound"], format_func=t)
    with col2:
        metric = st.selectbox(t("Gender:"), ["Total", "Female", "Male"], format_func=t)
    with col3:
        year_sel = st.selectbox(t("Year:"), ["All"] + all_years, index=0,
                                format_func=lambda o: t(o) if isinstance(o, str) else str(o))
        year = None if year_sel == "All" else year_sel

    data_col = COL_MAP[(direction, metric)]
    label = METRIC_LABEL[metric]
    meta = [direction, metric, label]

    with st.sidebar:
        month_opts = ["All"] + list(months.values())
        month_name = st.selectbox(t("Month:"), month_opts, index=0, format_func=t)

    grouped, title = mig.build_migration_map_data(migration_df, year, month_name, data_col, meta)

    if grouped.empty:
        st.warning(t("No data for selected filters."))
    else:
        fig = dc.choropleth_map(grouped, data_col, [title, "Country", label])
        mc.render_chart(fig)


def _render_line_bar(migration_df, chart_type, all_years, valid_pres):
    compare_by = st.session_state.get("mig_compare", "Countries")

    with st.sidebar:
        selected_presidents = president_multiselect(valid_pres)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    pres_compare = comparing and compare_by in ("Countries", "Direction", "Gender")

    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    direction = "Inbound"
    metric = "Total"

    c1, c2, c3 = st.columns(3)

    if compare_by == "Direction":
        with c1:
            metric = st.selectbox(t("Gender:"), ["Total", "Female", "Male"], format_func=t)
        with c2:
            selected_years = [] if pres_compare else st.multiselect(t("Year:"), year_opts)
    elif compare_by == "Gender":
        with c1:
            direction = st.selectbox(t("Direction:"), ["Inbound", "Outbound"], format_func=t)
        with c2:
            selected_years = [] if pres_compare else st.multiselect(t("Year:"), year_opts)
    else:  # Countries or Year
        with c1:
            direction = st.selectbox(t("Direction:"), ["Inbound", "Outbound"], format_func=t)
        with c2:
            metric = st.selectbox(t("Gender:"), ["Total", "Female", "Male"], format_func=t)
        with c3:
            if compare_by == "Year":
                selected_years = st.multiselect(t("Year:"), year_opts)
            else:
                selected_years = [] if pres_compare else st.multiselect(t("Year:"), year_opts)

    label = METRIC_LABEL[metric]
    data_col = COL_MAP[(direction, metric)]
    meta = [direction, metric, label]

    df_f = migration_df.copy()

    if president:
        df_f = df_f[df_f["Fecha"].dt.year.isin(presidents[president])]
    if selected_years:
        df_f = df_f[df_f["Fecha"].dt.year.isin(selected_years)]

    if compare_by == "Year":
        all_countries_es = [c for c in sorted(df_f["País"].unique()) if c in COUNTRY_EN]
        all_countries_en = sorted([COUNTRY_EN[c] for c in all_countries_es])

        with st.sidebar:
            country_en = st.selectbox(t("Country:"), ["All"] + all_countries_en, key="mig_country", format_func=t)

        if country_en != "All":
            country_es = find_key_by_value(COUNTRY_EN, country_en)
            df_f = df_f[df_f["País"] == country_es]
            meta = [direction, metric, label, country_en]

        pivot, info = mig.migration_year_pivot(df_f, data_col, meta)
        force_bar = False
    else:
        annual_mode = len(selected_years) != 1

        if annual_mode:
            df_f = df_f.copy()
            df_f["Period"] = df_f["Fecha"].dt.year.astype(str)
            period_label = "Year"
        else:
            df_f = df_f[df_f["Fecha"].dt.year == selected_years[0]].copy()
            df_f["Period"] = df_f["Fecha"].dt.strftime("%Y-%m")
            period_label = "Month"

        all_countries_es = [c for c in sorted(migration_df["País"].unique()) if c in COUNTRY_EN]
        all_countries_en = sorted([COUNTRY_EN[c] for c in all_countries_es])

        if compare_by == "Countries":
            pivot, info = mig.migration_countries_pivot(df_f, all_countries_en, data_col, period_label, meta)
        else:  # Direction or Gender
            pivot, info = mig.migration_single_pivot(df_f, all_countries_en, compare_by, meta, period_label)

        force_bar = not annual_mode and len(pivot) == 1 if pivot is not None else False

    if pres_compare and pivot is not None and not pivot.empty:
        pivot, info = reshape_by_presidents(pivot, selected_presidents, info)

    highlight = highlight_selectbox(pivot)

    compare_placeholder = st.sidebar.empty()

    if pivot is None or pivot.empty:
        with compare_placeholder:
            st.radio(
                t("Compare by:"), ["Countries", "Direction", "Gender", "Year"],
                horizontal=True, key="mig_compare", format_func=t,
            )
        return

    if pivot.empty:
        st.warning(t("No data for selected filters."))
        st.stop()

    fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight, force_bar=force_bar)

    mc.render_chart(fig)

    with compare_placeholder:
        st.radio(
            t("Compare by:"), ["Countries", "Direction", "Gender", "Year"],
            horizontal=True, key="mig_compare", format_func=t,
        )
