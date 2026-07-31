import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.macro import deficit_functions as dff
import generalities.macro_generalities.deficit as dg
from generalities.i18n import t
from generalities.dictionaries import presidents, months
from generalities.function import (highlight_selectbox, get_valid_presidents,
                                   president_multiselect, find_key_by_value, show_all_years,
                                   reshape_by_presidents, cap as _cap, cap_one as _cap_one,
                                   SeriesSpec, series_year_axis, series_month_axis)


def _multi_series(build_fn, keys: list) -> pd.DataFrame:
    """One column per concept key, via the same build_fn used for the single-concept case."""
    return pd.DataFrame({k: build_fn(k).iloc[:, 0] for k in keys})


def render_deficit() -> None:
    st.title(t("Deficit"))

    col1, col2, col3 = st.columns(3)
    with col1:
        frequency = st.selectbox(t("Frequency:"), list(dg.FREQUENCIES), key="deficit_frequency", format_func=t)
    with col2:
        unit = st.selectbox(t("Unit:"), list(dg.UNITS), key="deficit_unit", format_func=t)

    freq_folder = dg.FREQUENCIES[frequency]
    terms = dg.TERMS[freq_folder]
    dated = frequency != "Annual"
    values, meta = dff.load_deficit(dg.DEFICIT_BASE / freq_folder / dg.UNITS[unit], dated=dated)
    if unit == "COP":
        values = values / dg.COP_SCALE
    years = sorted(values.index.year.unique()) if dated else sorted(values.index)

    # Compare mode disables Group/Concepts/President entirely (mirrors debt.py's "Compare
    # internal vs external"). It also caps Year to 1 for Monthly/Quarterly, which need a single
    # year to resolve the Month/Quarter-vs-Year axis duality — Annual has no such duality, so it
    # keeps every selected year and charts Revenue vs. Spending as a normal multi-year trend.
    prev_compare = st.session_state.get("deficit_compare", False)
    if prev_compare and frequency != "Annual":
        _cap_one(["deficit_years"])

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar", "Stacked bar"],
                                      key="deficit_chart_type", format_func=t)

    roots = [k for k in meta.index if meta.at[k, "depth"] == 0]
    group_key = st.sidebar.selectbox(
        t("Group:"), ["Headline"] + roots,
        format_func=lambda k: t("Headline") if k == "Headline" else t(terms.get(k, k)),
        key="deficit_group", disabled=prev_compare,
    )
    members = roots if group_key == "Headline" else [
        k for k in meta.index if meta.at[k, "root"] == group_key
    ]

    concepts_key = f"deficit_concepts_{freq_folder}"
    concepts = st.sidebar.multiselect(
        t("Concepts:"), members, default=members[:1],
        format_func=lambda k: ("· " * meta.at[k, "depth"]) + t(terms.get(k, k)),
        key=concepts_key, on_change=_cap, args=(concepts_key, ["deficit_years"]),
        disabled=prev_compare,
    )
    if not concepts:
        concepts = members[:1]
    single = len(concepts) == 1

    cur_years = st.sidebar.multiselect(
        t("Year:"), years, key="deficit_years",
        on_change=_cap, args=("deficit_years", [concepts_key]),
    )

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(
            valid_presidents, key="deficit_presidents", disabled=prev_compare or not single,
        )

    compare = st.sidebar.checkbox(t("Compare revenue vs. spending"), key="deficit_compare")

    year_set = set(cur_years)
    if not prev_compare and single:
        for name in selected_presidents:
            year_set.update(set(presidents[name]) & set(years))

    period_label = None
    with col3:
        if frequency == "Monthly":
            month_labels = list(months.values())
            period_label = st.selectbox(
                t("Month:"), month_labels, index=month_labels.index(months[12]),
                key="deficit_period", disabled=bool(year_set), format_func=t,
            )
        elif frequency == "Quarterly":
            period_label = st.selectbox(
                t("Quarter:"), ["Q1", "Q2", "Q3", "Q4"], index=3,
                key="deficit_period", disabled=bool(year_set),
            )

    # Annual has no Month/Quarter duality: an empty selection always means "every year",
    # gated the same way as everywhere else in the app.
    if frequency == "Annual" and not year_set:
        capped = show_all_years(pd.DataFrame(index=years), president=bool(selected_presidents))
        year_set = set(capped.index)

    years_sorted = sorted(year_set)
    group_title = t("Headline") if group_key == "Headline" else t(terms.get(group_key, group_key))

    if compare:
        rev_key, spend_key = dg.COMPARE_ROOTS[freq_folder]
        keys, labels = [rev_key, spend_key], ["Revenue", "Spending"]

        if frequency == "Annual":
            # No Month/Quarter duality to resolve, so Compare charts every selected year as a
            # normal multi-year trend instead of collapsing to one (see comment above).
            x_label = "Year"
            series = values.reindex(years_sorted)[keys].set_axis(labels, axis=1)
            title = t("Revenue vs. Spending")
            if len(years_sorted) == 1:
                title += f" · {years_sorted[0]}"
        else:
            year = years_sorted[0] if years_sorted else None
            if frequency == "Monthly":
                month_num = find_key_by_value(months, period_label)
                if year:
                    x_label = "Month"
                    series = _multi_series(lambda k: series_month_axis(values, SeriesSpec(k, k), [year]), keys)
                else:
                    x_label = "Year"
                    series = _multi_series(lambda k: series_year_axis(values, SeriesSpec(k, k), [month_num]), keys)
            else:  # Quarterly
                quarter_num = int(period_label[1])
                if year:
                    x_label = "Quarter"
                    series = dff.quarter_concept_axis(values, keys, year)
                else:
                    x_label = "Year"
                    series = _multi_series(lambda k: dff.quarter_year_axis(values, k, quarter_num), keys)
            series = series.set_axis(labels, axis=1)
            title = t("Revenue vs. Spending") + (f" · {year}" if year else "")

    else:
        labels = [t(terms.get(k, k)) for k in concepts]

        if frequency == "Annual":
            x_label = "Year"
            series = values.reindex(years_sorted)[concepts].set_axis(labels, axis=1)
            title = labels[0] if single else group_title
            if single and len(years_sorted) == 1:
                title += f" · {years_sorted[0]}"

        elif frequency == "Monthly":
            month_num = find_key_by_value(months, period_label)
            if years_sorted:
                x_label = "Month"
                if single:
                    series = series_month_axis(values, SeriesSpec(concepts[0], labels[0]), years_sorted)
                    title = labels[0]
                else:
                    year = years_sorted[0]
                    series = _multi_series(
                        lambda k: series_month_axis(values, SeriesSpec(k, k), [year]), concepts
                    ).set_axis(labels, axis=1)
                    title = f"{group_title} · {year}"
            else:
                x_label = "Year"
                if single:
                    series = series_year_axis(values, SeriesSpec(concepts[0], labels[0]), [month_num]).rename(
                        columns={months[month_num]: labels[0]})
                    title = f"{labels[0]} · {t(period_label)}"
                else:
                    series = _multi_series(
                        lambda k: series_year_axis(values, SeriesSpec(k, k), [month_num]), concepts
                    ).set_axis(labels, axis=1)
                    title = f"{group_title} · {t(period_label)}"

        else:  # Quarterly
            quarter_num = int(period_label[1])
            if years_sorted:
                x_label = "Quarter"
                if single:
                    series = dff.quarter_axis(values, concepts[0], years_sorted)
                    title = labels[0]
                else:
                    year = years_sorted[0]
                    series = dff.quarter_concept_axis(values, concepts, year).set_axis(labels, axis=1)
                    title = f"{group_title} · {year}"
            else:
                x_label = "Year"
                series = _multi_series(
                    lambda k: dff.quarter_year_axis(values, k, quarter_num), concepts
                ).set_axis(labels, axis=1)
                title = f"{labels[0] if single else group_title} · {t(period_label)}"

    info = [title, x_label, dg.UNIT_AXIS[unit]]
    if frequency == "Annual" and len(selected_presidents) >= 2:
        series, info = reshape_by_presidents(series, selected_presidents, info)

    if series.empty:
        st.warning(t("No data for selected filters."))
    else:
        highlight = highlight_selectbox(series)
        is_stacked = chart_type == "Stacked bar"
        fig = mc.line_or_bar("Bar" if is_stacked else chart_type, series, info, highlight=highlight,
                             barmode="stack" if is_stacked else "group")
        mc.render_chart(fig)

    st.caption(t("Shows the Central National Government (GNC) fiscal balance. A negative value is a deficit."))
    if unit == "% of GDP":
        st.caption(t("% of GDP is computed by the source against DANE nominal GDP."))
    if frequency == "Annual" and 2025 in years_sorted:
        st.caption(t("2025 figures are preliminary."))
    if chart_type == "Stacked bar":
        st.caption(t("Stacking is only meaningful within one group — mixing a total with its own "
                  "components double-counts."))
    st.caption(t("Source: Ministerio de Hacienda"))
