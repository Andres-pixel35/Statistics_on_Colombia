import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.macro import debt_functions as dbf
import generalities.macro_generalities.debt as dg
from generalities.i18n import t
from generalities.dictionaries import presidents, months
from generalities.function import (highlight_selectbox, get_valid_presidents,
                                   president_multiselect, find_key_by_value, to_datatime, load_csv,
                                   cap as _cap, cap_one as _cap_one, SeriesSpec, series_year_axis, series_month_axis)


def _compare_series(build_fn) -> pd.DataFrame:
    """Internal vs External Debt as two columns, via the same build_fn used for the single-concept case."""
    cols = {}
    for label in ("Internal Debt", "External Debt"):
        spec = SeriesSpec(dg.CONCEPTS[label], label)
        cols[label] = build_fn(spec).iloc[:, 0]
    return pd.DataFrame(cols)


def _multi_series(build_fn, specs: list[SeriesSpec]) -> pd.DataFrame:
    """One column per spec, via the same build_fn used for the single-instrument case."""
    return pd.DataFrame({s.label: build_fn(s).iloc[:, 0] for s in specs})


def render_debt(df: pd.DataFrame) -> None:
    st.title(t("Debt"))
    dataset = st.sidebar.radio(
        t("Dataset:"), ["Balances", "Sources", "Rates", "Currency", "Perfil", "Indicators"], format_func=t
    )
    if dataset == "Sources":
        render_sources()
        return
    if dataset == "Rates":
        render_rates()
        return
    if dataset == "Currency":
        render_currency()
        return
    if dataset == "Perfil":
        render_perfil()
        return
    if dataset == "Indicators":
        render_indicators()
        return
    render_balances(df)


def render_balances(df: pd.DataFrame) -> None:
    local = to_datatime(df, False)
    years = sorted(local.index.year.unique())

    # Compare mode charts one concept-pair line per axis point, so it caps Year to 1 and
    # disables President entirely (mirrors job_market.py's "Compare men vs. women" pattern).
    prev_compare = st.session_state.get("debt_compare", False)
    if prev_compare:
        _cap_one(["debt_years"])

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar"], format_func=t)
    cur_years = st.sidebar.multiselect(t("Year:"), years, key="debt_years")

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(
            valid_presidents, key="debt_presidents", disabled=prev_compare
        )

    year_set = set(cur_years)
    if not prev_compare:
        for name in selected_presidents:
            year_set.update(set(presidents[name]) & set(years))

    month_labels = list(months.values())
    col1, col2 = st.columns(2)
    with col1:
        concept_label = st.selectbox(t("Concept:"), list(dg.CONCEPTS.keys()), disabled=prev_compare, format_func=t)
    with col2:
        month_label = st.selectbox(
            t("Month:"), month_labels, index=month_labels.index(months[12]), disabled=bool(year_set), format_func=t
        )

    compare = st.sidebar.checkbox(
        t("Compare internal vs. external debt"), value=False, key="debt_compare"
    )

    prev_gdp_pct = st.session_state.get("debt_gdp_pct", False)
    show_pct_total_visible = compare or concept_label != "Total Debt"
    prev_pct_total = show_pct_total_visible and st.session_state.get("debt_pct_total", False)
    show_gdp_pct = st.sidebar.checkbox(t("Show as % of GDP"), key="debt_gdp_pct", disabled=prev_pct_total)
    show_pct_total = False
    if show_pct_total_visible:
        show_pct_total = st.sidebar.checkbox(
            t("Show as % of Total Debt"), key="debt_pct_total", disabled=prev_gdp_pct
        )
    else:
        st.session_state["debt_pct_total"] = False

    if year_set:
        years_sorted = sorted(year_set)
        year = years_sorted[0]
        year_list = [year] if compare else years_sorted
        if compare:
            series = _compare_series(lambda spec: series_month_axis(local, spec, year_list))
            info = [f"{t('Internal vs. External Debt')} · {year}", "Month", "Trillion (COP)"]
        else:
            spec = SeriesSpec(dg.CONCEPTS[concept_label], concept_label)
            series = series_month_axis(local, spec, year_list)
            info = [concept_label, "Month", "Trillion (COP)"]
    else:
        month_num = find_key_by_value(months, month_label)
        if compare:
            series = _compare_series(lambda spec: series_year_axis(local, spec, [month_num]))
            info = [f"{t('Internal vs. External Debt')} · {t(month_label)}", "Year", "Trillion (COP)"]
        else:
            spec = SeriesSpec(dg.CONCEPTS[concept_label], concept_label)
            series = series_year_axis(local, spec, [month_num]).rename(columns={month_label: concept_label})
            info = [f"{t(concept_label)} · {t(month_label)}", "Year", "Trillion (COP)"]

    gdp_note = None
    if show_gdp_pct:
        gdp = dbf.gdp_millions(dg.NOMINAL_ANNUAL_PATH)
        pct_year = years_sorted[0] if (year_set and compare) else None
        missing = dbf.missing_gdp_years(series, gdp, year=pct_year)
        labels = dbf.gdp_pct_labels(series, pct_year)
        if missing and len(missing) == len(labels):
            gdp_note = t("No GDP data yet for {years} — showing Trillion (COP) instead.").format(years=", ".join(missing))
            show_gdp_pct = False
        else:
            if missing:
                gdp_note = t("No GDP data yet for {years} — shown as gaps.").format(years=", ".join(missing))
            series = dbf.to_gdp_pct(series, gdp, year=pct_year)
            info[2] = "% of GDP"

    elif show_pct_total:
        if year_set:
            total = series_month_axis(local, dg.TOTAL_SPEC, year_list)
            if compare:
                total = total.iloc[:, 0]
        else:
            total = series_year_axis(local, dg.TOTAL_SPEC, [month_num]).iloc[:, 0]
        series = dbf.to_total_pct(series, total)
        info[2] = "% of Total Debt"

    if not show_gdp_pct and not show_pct_total:
        series = series / 1_000_000  # COP millions -> Trillion (COP)

    if series.empty:
        st.warning(t("No data for selected filters."))
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
    if gdp_note:
        st.info(gdp_note)
    st.caption(t("Shows Central National Government Gross Debt"))
    st.caption(t("Source: Ministerio de Hacienda"))


def _render_debt_breakdown(config: dict) -> None:
    paths, terms_by_view, key_prefix = config["paths"], config["terms"], config["key_prefix"]
    noun, category = config["noun"], config["category"]

    col1, col2 = st.columns(2)
    with col1:
        view = st.selectbox(t("View:"), ["Internal", "External", "Total"], format_func=t)

    terms = terms_by_view[view]
    spanish = {v: k for k, v in terms.items()}
    local = to_datatime(dbf.load_fuente(paths[view]), False)
    years = sorted(local.index.year.unique())

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar"], key=f"{key_prefix}_chart_type", format_func=t)

    instr_key = f"{key_prefix}_instruments_{view}"
    years_key = f"{key_prefix}_years"
    instrument_labels = st.sidebar.multiselect(
        t("Instruments:"), list(terms.values()), default=list(terms.values())[:1],
        key=instr_key, on_change=_cap, args=(instr_key, [years_key]), format_func=t,
    )
    cur_years = st.sidebar.multiselect(
        t("Year:"), years, key=years_key, on_change=_cap, args=(years_key, [instr_key]),
    )
    single = len(instrument_labels) == 1

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(
            valid_presidents, key=f"{key_prefix}_presidents", disabled=not single
        )

    year_set = set(cur_years)
    if single:
        for name in selected_presidents:
            year_set.update(set(presidents[name]) & set(years))

    month_labels = list(months.values())
    with col2:
        month_label = st.selectbox(
            t("Month:"), month_labels, index=month_labels.index(months[12]), disabled=bool(year_set), format_func=t
        )

    if not instrument_labels:
        st.warning(t("No data for selected filters."))
        st.caption(t("Each {noun}'s share of {view} Debt (%).").format(noun=t(noun), view=t(view)))
        st.caption(t("Source: Ministerio de Hacienda"))
        return

    specs = [SeriesSpec(spanish[label], label) for label in instrument_labels]

    if year_set:
        years_sorted = sorted(year_set)
        year = years_sorted[0]
        if single:
            series = series_month_axis(local, specs[0], years_sorted)
            info = [specs[0].label, "Month", "%"]
        else:
            series = _multi_series(lambda spec: series_month_axis(local, spec, [year]), specs)
            info = [t("{view} Debt by {category}").format(view=t(view), category=t(category)) + f" · {year}", "Month", "%"]
    else:
        month_num = find_key_by_value(months, month_label)
        if single:
            series = series_year_axis(local, specs[0], [month_num]).rename(columns={month_label: specs[0].label})
            info = [f"{t(specs[0].label)} · {t(month_label)}", "Year", "%"]
        else:
            series = _multi_series(
                lambda spec: series_year_axis(local, spec, [month_num]).rename(columns={month_label: spec.label}),
                specs,
            )
            info = [t("{view} Debt by {category}").format(view=t(view), category=t(category)) + f" · {t(month_label)}", "Year", "%"]

    if series.empty:
        st.warning(t("No data for selected filters."))
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
    st.caption(t("Each {noun}'s share of {view} Debt (%).").format(noun=t(noun), view=t(view)))
    st.caption(t("Source: Ministerio de Hacienda"))


def render_sources() -> None:
    _render_debt_breakdown({
        "paths": dg.FUENTE_PATHS, "terms": dg.FUENTE_TERMS, "key_prefix": "fuente",
        "noun": "instrument", "category": "Source",
    })


def render_rates() -> None:
    _render_debt_breakdown({
        "paths": dg.TASA_PATHS, "terms": dg.TASA_TERMS, "key_prefix": "tasa",
        "noun": "rate type", "category": "Rate",
    })


def render_currency() -> None:
    _render_debt_breakdown({
        "paths": dg.MONEDA_PATHS, "terms": dg.MONEDA_TERMS, "key_prefix": "moneda",
        "noun": "currency", "category": "Currency",
    })


def render_perfil() -> None:
    df = load_csv(dg.PERFIL_PATH)
    dates = sorted(df["Fecha"].unique())

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar"], key="perfil_chart_type", format_func=t)
    report_years = sorted({d[:4] for d in dates})
    col1, col2, col3 = st.columns(3)
    with col1:
        report_year = st.selectbox(t("Year:"), report_years, index=len(report_years) - 1)
    year_dates = [d for d in dates if d.startswith(report_year)]
    with col2:
        fecha = st.selectbox(t("Report Date:"), year_dates, index=len(year_dates) - 1)
    with col3:
        periodo_label = st.selectbox(t("Service period:"), list(dg.PERIODO_EN.values()), format_func=t)
    periodo = {v: k for k, v in dg.PERIODO_EN.items()}[periodo_label]

    series = dbf.perfil_series(df, fecha, periodo) / 1_000_000  # COP millions -> Trillion (COP)
    series.name = periodo_label
    info = [f"{t(periodo_label)} · {fecha}", "Maturity Year", "Trillion (COP)"]

    if series.empty:
        st.warning(t("No data for selected filters."))
    else:
        fig = mc.line_or_bar(chart_type, series, info)
        mc.render_chart(fig)
    st.caption(t("Projected debt-service schedule, as forecast from the report date."))
    st.caption(t("Source: Ministerio de Hacienda"))


def render_indicators() -> None:
    local = to_datatime(load_csv(dg.INDICADORES_PATH), False)
    years = sorted(local.index.year.unique())

    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox(t("Metric:"), list(dg.INDICADORES_TERMS.keys()), format_func=t)
    terms = dg.INDICADORES_TERMS[metric]
    unit = dg.INDICADORES_UNITS[metric]

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar"], key="indicadores_chart_type", format_func=t)

    splits_key = "indicadores_splits"
    years_key = "indicadores_years"
    split_labels = st.sidebar.multiselect(
        t("Split:"), list(terms.keys()), default=["Total"],
        key=splits_key, on_change=_cap, args=(splits_key, [years_key]), format_func=t,
    )
    cur_years = st.sidebar.multiselect(
        t("Year:"), years, key=years_key, on_change=_cap, args=(years_key, [splits_key]),
    )
    single = len(split_labels) == 1

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(
            valid_presidents, key="indicadores_presidents", disabled=not single
        )

    year_set = set(cur_years)
    if single:
        for name in selected_presidents:
            year_set.update(set(presidents[name]) & set(years))

    month_labels = list(months.values())
    with col2:
        month_label = st.selectbox(
            t("Month:"), month_labels, index=month_labels.index(months[12]), disabled=bool(year_set), format_func=t
        )

    if not split_labels:
        st.warning(t("No data for selected filters."))
        st.caption(t("Source: Ministerio de Hacienda"))
        return

    specs = [SeriesSpec(terms[label], label) for label in split_labels]

    if year_set:
        years_sorted = sorted(year_set)
        year = years_sorted[0]
        if single:
            series = series_month_axis(local, specs[0], years_sorted)
            info = [f"{t(metric)} · {t(specs[0].label)}", "Month", unit]
        else:
            series = _multi_series(lambda spec: series_month_axis(local, spec, [year]), specs)
            info = [f"{t(metric)} · {year}", "Month", unit]
    else:
        month_num = find_key_by_value(months, month_label)
        if single:
            series = series_year_axis(local, specs[0], [month_num]).rename(columns={month_label: specs[0].label})
            info = [f"{t(metric)} · {t(specs[0].label)} · {t(month_label)}", "Year", unit]
        else:
            series = _multi_series(
                lambda spec: series_year_axis(local, spec, [month_num]).rename(columns={month_label: spec.label}),
                specs,
            )
            info = [f"{t(metric)} · {t(month_label)}", "Year", unit]

    if series.empty:
        st.warning(t("No data for selected filters."))
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
    if metric == "Average Coupon":
        st.caption(t("Internal debt coupon is quoted in COP terms; external debt in USD terms."))
    st.caption(t("Source: Ministerio de Hacienda"))
