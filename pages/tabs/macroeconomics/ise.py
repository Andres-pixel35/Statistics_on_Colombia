import streamlit as st
import pandas as pd
from pages.helpers import charts as mc
from pages.helpers.macro import ise_functions as isf
import generalities.macro_generalities.ise as ig
from generalities.dictionaries import presidents, months
from generalities.function import (highlight_selectbox, get_valid_presidents,
                                   president_multiselect, find_key_by_value, load_csv,
                                   cap_one as _cap_one)

CATEGORY_GROUPS = ["Actividades primarias", "Actividades secundarias", "Actividades terciarias"]


def render_ise(df: pd.DataFrame) -> None:
    st.title("ISE")

    dataset_col, metric_col, month_col = st.columns(3)
    with dataset_col:
        dataset = st.selectbox("Dataset:", list(ig.DATASETS.keys()))

    paths = ig.ise_paths(dataset)
    units = ig.ise_units(dataset)
    growth_label = next(iter(paths))
    with metric_col:
        metric = st.selectbox("Metric:", list(paths.keys()))

    raw = df if dataset == "Original" and metric == growth_label else load_csv(paths[metric])
    long_df = isf.ise_long(raw)
    unit = units[metric]

    # Read before the checkbox itself is drawn (at the bottom of the sidebar) so the
    # widgets above can already be disabled/capped on the same run.
    compare_categories = st.session_state.get("ise_compare_categories", False)
    if compare_categories:
        _cap_one(["ise_years"])

    category_label = st.sidebar.selectbox(
        "Category:", list(ig.CATEGORY_EN.values()), disabled=compare_categories
    )
    category_sp = find_key_by_value(ig.CATEGORY_EN, category_label)

    activity_dict = ig.ACTIVITY_EN[category_sp]
    # Tertiary Activities has 9 branches -> let the user compare several at once.
    if category_sp == "Actividades terciarias" and not compare_categories:
        activity_labels = st.sidebar.multiselect(
            "Activity:", list(activity_dict.values()),
            default=[next(iter(activity_dict.values()))], key="ise_activities",
        )
    else:
        activity_labels = [st.sidebar.selectbox(
            "Activity:", list(activity_dict.values()), disabled=compare_categories
        )]

    comparing_activities = not compare_categories and len(activity_labels) >= 2
    if comparing_activities:
        _cap_one(["ise_years"])
    activities_sp = [find_key_by_value(activity_dict, label) for label in activity_labels]

    chart_type = st.sidebar.selectbox("Chart Type:", ["Line", "Bar"])

    years = sorted(long_df["Fecha"].unique())
    cur_years = st.sidebar.multiselect("Year:", years, key="ise_years")

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(
            valid_presidents, key="ise_presidents",
            disabled=comparing_activities or compare_categories,
        )
        st.checkbox("Compare Primary vs Secondary vs Tertiary", key="ise_compare_categories")

    year_set = set(cur_years)
    if not comparing_activities and not compare_categories:
        for name in selected_presidents:
            year_set.update(set(presidents[name]) & set(years))

    month_labels = list(months.values())
    with month_col:
        month_label = st.selectbox(
            "Month:", month_labels, index=month_labels.index(months[12]), disabled=bool(year_set)
        )

    if compare_categories:
        # First key in each category's ACTIVITY_EN dict is always its own total Rama.
        categories = [(sp, next(iter(ig.ACTIVITY_EN[sp]))) for sp in CATEGORY_GROUPS]
        if year_set:
            year = sorted(year_set)[0]
            series = isf.ise_category_month_axis(long_df, categories, year).rename(columns=ig.CATEGORY_EN)
            info = [f"Primary vs Secondary vs Tertiary · {year}", "Month", unit]
        else:
            month_num = find_key_by_value(months, month_label)
            series = isf.ise_category_year_axis(long_df, categories, month_num).rename(columns=ig.CATEGORY_EN)
            info = [f"Primary vs Secondary vs Tertiary · {month_label}", "Year", unit]
    elif not activities_sp:
        st.info("Select at least one activity.")
        return
    elif year_set:
        years_sorted = sorted(year_set)
        if comparing_activities:
            year = years_sorted[0]
            series = isf.ise_activity_month_axis(long_df, category_sp, activities_sp, year)
            series = series.rename(columns=activity_dict)
            title = f"{category_label} · {year}"
        else:
            series = isf.ise_month_axis(long_df, category_sp, activities_sp[0], years_sorted)
            # Multiple years -> each line is a year, so the title needs the activity name;
            # a single year's line is already named after that year, so it doesn't.
            if len(years_sorted) >= 1 and activity_labels[0] != category_label:
                title = f"{category_label} — {activity_labels[0]}"
            else:
                title = category_label
        info = [title, "Month", unit]
    else:
        month_num = find_key_by_value(months, month_label)
        series = isf.ise_year_axis(long_df, category_sp, activities_sp, month_num).rename(columns=activity_dict)
        info = [f"{category_label} · {month_label}", "Year", unit]

    if series.empty:
        st.warning("No data for selected filters.")
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)

    if metric == "Index":
        st.caption(f"Metric: {metric} ({unit})")
    st.caption("Source: DANE — Indicador de Seguimiento a la Economía (ISE), 9-actividades breakdown")
