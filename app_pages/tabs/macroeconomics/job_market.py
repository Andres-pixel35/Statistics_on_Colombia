import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.macro import job_market_functions as mf
from app_pages.helpers import charts as dc
import generalities.macro_generalities.job_market as jm
from generalities.dictionaries import presidents, months
from generalities.i18n import t
from generalities.function import (to_datatime, load_csv, load_geojson, BASE_DIR,
                                   highlight_selectbox, find_key_by_value,
                                   get_valid_presidents, president_multiselect,
                                   cap as _cap, cap_one as _cap_one,
                                   series_year_axis, series_month_axis)

INFORMALITY_BASE = str(BASE_DIR / "data/dane/job_market/informalidad") + "/"
LABOR_FORCE_BASE = str(BASE_DIR / "data/dane/job_market/Mercado Laboral") + "/"
DEPT_BASE = str(BASE_DIR / "data/dane/job_market/Departamentos") + "/"
DEPT_GEOJSON_PATH = BASE_DIR / "data/dane/geo/colombia_departments.geojson"
DEPT_FEATURE_KEY = "properties.DPTO"
REGION_BASE = str(BASE_DIR / "data/dane/job_market/regiones") + "/"
CHILD_LABOR_BASE = str(BASE_DIR / "data/dane/job_market/infantil") + "/"
DESEST_UNEMPLOYMENT_PATH = str(BASE_DIR / "data/dane/job_market/desestacionalizado/total.csv")
REGION_GEOJSON_PATH = BASE_DIR / "data/dane/geo/colombia_regions.geojson"
REGION_FEATURE_KEY = "properties.region"


def _year_set(years_sel, presidents_sel, data_years):
    """Union explicit years with each president's years, dropping years the data lacks."""
    ys = set(years_sel)
    for name in presidents_sel:
        ys.update(set(presidents[name]) & set(data_years))
    return ys


def _draw(chart_type, series, info, *, labels=None, display_names=None):
    """Highlight picker + line/bar chart + render (the dataset-specific captions stay at the
    call site)."""
    highlight = highlight_selectbox(series, display_names=display_names)
    fig = mc.line_or_bar(chart_type, series, info, labels=labels or {}, highlight=highlight)
    mc.render_chart(fig)


def _age_count(band_sp: str, suffix: str) -> str:
    """edad.csv count Concepto: the band's population row, optionally narrowed by `suffix`
    (empty suffix -> the age-group total itself)."""
    return f"Población de {band_sp}" + (f" {suffix}" if suffix else "")


def render_job_market(unemployment_df: pd.DataFrame) -> None:
    st.title(t("Job Market"))

    dataset = st.sidebar.radio(
        t("Dataset:"), ["Unemployment", "Labor Force", "Departments", "Regions",
                     "Employment Formality", "Child Labor"], format_func=t)

    if dataset == "Departments":
        render_departments()
        return

    if dataset == "Regions":
        render_regions()
        return

    if dataset == "Employment Formality":
        render_informality()
        return

    if dataset == "Child Labor":
        render_child_labor()
        return

    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    if dataset == "Unemployment":
        unemp_local = to_datatime(unemployment_df, True)
        desest_local = mf.load_desestacionalizado_unemployment(DESEST_UNEMPLOYMENT_PATH)

        # Mutually-exclusive controls: read prior selections to gate them (Streamlit reruns
        # top-to-bottom, so the lock comes from last run's session_state).
        prev_months = st.session_state.get("unemp_months", [])
        prev_years = st.session_state.get("unemp_years", [])
        prev_pres = st.session_state.get("unemp_presidents", [])
        prev_compare = st.session_state.get("unemp_compare", False)
        month_disabled = bool(prev_years or prev_pres)
        yearpres_disabled = bool(prev_months)

        year_options = sorted(unemp_local.index.year.unique())
        col1, col2, col3 = st.columns(3)
        with col2:
            cur_years = st.multiselect(
                t("Year:"), year_options, key="unemp_years", disabled=yearpres_disabled
            )
        with col3:
            cur_month_labels = st.multiselect(
                t("Month:"), list(months.values()), key="unemp_months", disabled=month_disabled, format_func=t
            )
        with col1:
            series_choice = st.selectbox(
                t("Series:"), ["Original", "Seasonally Adjusted"],
                key="unemp_series", disabled=prev_compare, format_func=t,
            )
        active_df = desest_local if series_choice == "Seasonally Adjusted" else unemp_local

        selected_presidents, chart_type = mf.job_market_sidebar_filters(
            series_year_axis(active_df, mf.UNEMPLOYMENT_SPEC, []), top_placeholder, president_placeholder,
            president_disabled=yearpres_disabled, president_key="unemp_presidents",
        )

        compare = st.sidebar.checkbox(
            t("Compare seasonally adjusted vs. original"), value=False, key="unemp_compare"
        )

        # Null out disabled controls so a stale lock can't leak into mode resolution.
        month_nums = ([] if month_disabled
                      else [find_key_by_value(months, m) for m in cur_month_labels])
        years = [] if yearpres_disabled else cur_years
        presidents_sel = [] if yearpres_disabled else selected_presidents

        if compare:  # Original vs Seasonally Adjusted
            if years or presidents_sel:  # YEAR mode -> x = months, single year
                year_set = _year_set(years, presidents_sel, year_options)
                year = sorted(year_set)[0]
                cols = {}
                for label, df in (("Original", unemp_local), ("Seasonally Adjusted", desest_local)):
                    cols[label] = series_month_axis(df, mf.UNEMPLOYMENT_SPEC, [year]).iloc[:, 0]
                series = pd.DataFrame(cols)
                info = [f"{t('Unemployment rate — Original vs Seasonally Adjusted')} · {year}",
                        "Month", "Rate (%)"]
            else:  # MONTH mode (months selected) or DEFAULT -> x = years, single month (or annual avg)
                month = month_nums[:1]
                cols = {}
                for label, df in (("Original", unemp_local), ("Seasonally Adjusted", desest_local)):
                    cols[label] = series_year_axis(df, mf.UNEMPLOYMENT_SPEC, month).iloc[:, 0]
                series = pd.DataFrame(cols)
                suffix = f" · {t(months[month[0]])}" if month else t(" (annual average)")
                info = [f"{t('Unemployment rate — Original vs Seasonally Adjusted')}{suffix}", "Year", "Rate (%)"]
            _draw(chart_type, series, info)
            st.caption(t("Source: Banco de la República (Original) and DANE (GEIH, Seasonally Adjusted)"))
            return

        if years or presidents_sel:  # YEAR mode -> x = months
            year_set = _year_set(years, presidents_sel, year_options)
            series = series_month_axis(active_df, mf.UNEMPLOYMENT_SPEC, sorted(year_set))
            info = ["Unemployment rate by month", "Month", "Rate (%)"]
        else:  # MONTH mode (months selected) or DEFAULT -> x = years
            series = series_year_axis(active_df, mf.UNEMPLOYMENT_SPEC, month_nums)
            info = ["Unemployment rate", "Year", "Rate (%)"]

        _draw(chart_type, series, info)
        if not (years or presidents_sel or month_nums):
            st.caption(t("Showing the annual average across all months. "
                       "Pick month(s) to compare them across years, or year(s)/a president to see months."))
        st.caption(t("Source: DANE (GEIH)") if series_choice == "Seasonally Adjusted"
                   else t("Source: Banco de la República"))
        return

    # Labor Force
    col2, col3, col4 = st.columns(3)
    with col2:
        file_label = st.selectbox(t("Table:"), list(jm.LABOR_FORCE_FILES.keys()), format_func=t)
    stem = jm.LABOR_FORCE_FILES[file_label]
    terms = jm.LABOR_FORCE_TERMS[stem]
    if stem == "total" and not st.session_state.get("lf_percent", False):
        terms = {k: v for k, v in terms.items() if k != jm.TGP_CONCEPT}

    data = load_csv(f"{LABOR_FORCE_BASE}{stem}.csv")

    prev_compare = st.session_state.get("lf_gender_compare", False)
    with col3:
        gender = st.selectbox(t("Gender:"), list(jm.GENDER.keys()), disabled=prev_compare, format_func=t)
    gender_sp = jm.GENDER[gender]

    # Period (window) / Year / President are mutually-exclusive axes; gate on session_state.
    # Concepts vs Years are symmetrically capped: picking 2+ of one locks the other to 1.
    # Keyed widgets land in session_state before the rerun, so prev_* read here is current;
    # Concepts (keyless, re-defaults per Table) is rendered first below so its count is live.
    prev_years = st.session_state.get("lf_years", [])
    prev_period = st.session_state.get("lf_period", "Annual average")
    prev_pres = st.session_state.get("lf_presidents", [])

    period_active = prev_period not in (None, "Annual average")
    windows_active = bool(prev_years) or bool(prev_pres)

    period_disabled = windows_active
    year_disabled = period_active

    with col4:
        period = st.selectbox(
            t("Period:"), ["Annual average"] + list(jm.PERIOD_EN.values()),
            key="lf_period", disabled=period_disabled, format_func=t,
        )

    # Concepts <-> Year peer cap via _cap (editable, remembers the other). Period/president stay
    # axis-exclusive via `disabled` above. Per-table concept key re-defaults on Table switch.
    concept_key = f"lf_concepts_{stem}"
    if prev_compare:                      # Compare charts one concept, one year -> cap both
        _cap_one([concept_key, "lf_years"])
    if concept_key in st.session_state:   # drop TGP if percentages just got toggled off
        st.session_state[concept_key] = [v for v in st.session_state[concept_key] if v in terms.values()]
    concept_labels = st.sidebar.multiselect(
        t("Concepts:"), list(terms.values()), default=[next(iter(terms.values()))],
        key=concept_key, on_change=_cap, args=(concept_key, ["lf_years"]), format_func=t,
    )
    if not concept_labels:
        concept_labels = [next(iter(terms.values()))]
    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}

    president_disabled = period_active or prev_compare or len(concepts_sp) >= 2

    year_options = sorted(data["Fecha"].unique())
    cur_years = st.sidebar.multiselect(
        t("Year:"), year_options, key="lf_years", disabled=year_disabled,
        on_change=_cap, args=("lf_years", [concept_key]),
    )

    selected_presidents, chart_type = mf.job_market_sidebar_filters(
        mf.labor_force_pivot(data, gender_sp, None, concepts_sp),
        top_placeholder, president_placeholder,
        president_disabled=president_disabled, president_key="lf_presidents",
    )

    # Percentages only make sense for the Total table (only one with PET + rate rows).
    percent = stem == "total" and st.sidebar.checkbox(t("Show percentages"), value=False, key="lf_percent")
    metric = "Share (%)" if percent else "People"

    compare_gender = st.sidebar.checkbox(
        t("Compare men vs. women"), value=False, key="lf_gender_compare"
    )

    # Null out disabled controls so a stale lock can't leak into mode resolution.
    years_sel = [] if year_disabled else cur_years
    presidents_sel = [] if president_disabled else selected_presidents
    year_set = _year_set(years_sel, presidents_sel, year_options)

    if compare_gender:  # Men vs Women for a single concept
        concept_sp = concepts_sp[0]
        if year_set:  # single year -> x = rolling windows
            year = sorted(year_set)[0]
            series = mf.labor_force_gender_period_axis(data, year, concept_sp, percent=percent)
            info = [f"{t(concept_labels[0])} — {t(file_label)} ({t('Men vs Women')}) · {year}{t(' by 3-month window')}",
                    "Period", metric]
        else:  # x = years (optional period filter)
            period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
            series = mf.labor_force_gender_pivot(data, period_sp, concept_sp, percent=percent)
            info = [f"{t(concept_labels[0])} — {t(file_label)} ({t('Men vs Women')}) · {t(period)}", "Year", metric]
        _draw(chart_type, series, info)
        if percent:
            st.caption(t(jm.PET_PCT_NOTE))
        st.caption(t("Source: DANE (GEIH)"))
        return

    if year_set:  # WINDOWS mode -> x = rolling windows
        years_sorted = sorted(year_set)
        if len(concepts_sp) >= 2:  # concept priority -> single year (enforced by gating)
            years_sorted, labels = years_sorted[:1], eng_map
            title_subject = str(years_sorted[0])
        else:
            labels = {}
            title_subject = concept_labels[0]
        series = mf.labor_force_period_axis(data, gender_sp, years_sorted, concepts_sp, percent=percent)
        info = [f"{t(title_subject)} — {t(file_label)} ({t(gender)}){t(' by 3-month window')}", "Period", metric]
        _draw(chart_type, series, info, labels=labels,
              display_names=list(eng_map.values()) if labels else None)
        st.caption(t("Source: DANE (GEIH)"))
        return

    # YEAR-axis mode (no years, no president)
    period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
    series = mf.labor_force_pivot(data, gender_sp, period_sp, concepts_sp, percent=percent)
    info = [f"{t('Labor Force')} — {t(file_label)} ({t(gender)}) · {t(period)}", "Year", metric]
    _draw(chart_type, series, info, labels=eng_map,
          display_names=list(eng_map.values()))
    st.caption(t("Source: DANE (GEIH)"))


def _inf_prep(df: pd.DataFrame) -> pd.DataFrame:
    """Total-nacional rows with footnote markers (^/*) stripped and DANE relabels collapsed
    so each concept's series stays whole."""
    df = df[df["Perspectiva"] == "Total nacional"].copy()
    df["Concepto"] = (df["Concepto"].str.replace(r"[\^*]+$", "", regex=True)
                      .str.strip().replace(jm.INFORMALITY_CONCEPT_FIXES))
    return df


def _inf_total_load(stem: str, cfg: dict, sexo_sp: str = None) -> pd.DataFrame:
    """Load a total-like informality file, keep Total-nacional rows (case-insensitive) and,
    when `cfg["miles"]`, the absolute "(en miles)" Grupo. `sexo_sp` filters the Sexo column."""
    df = load_csv(f"{INFORMALITY_BASE}{stem}.csv")
    df = df[df["Perspectiva"].str.lower() == "total nacional"].copy()
    if cfg["miles"]:
        df = df[df["Grupo"].str.contains("en miles")]
    return df if sexo_sp is None else df[df["Sexo"] == sexo_sp]


def render_informality() -> None:
    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    col2, col3, col4 = st.columns(3)
    with col2:
        file_label = st.selectbox(t("Table:"), list(jm.INFORMALITY_FILES.keys()), format_func=t)
    stem = jm.INFORMALITY_FILES[file_label]
    terms = jm.INFORMALITY_TERMS[stem]
    is_total_like = stem in jm.INFORMALITY_TOTAL_LIKE

    # Per-table swap: total-like tables -> Gender + Compare men vs. women (<stem>.csv/<sexo>.csv);
    # the grouped tables -> Group (Grupo) + Compare formal vs. informal (no gender data).
    compare_key = "inf_gender_compare" if is_total_like else "inf_group_compare"
    prev_compare = st.session_state.get(compare_key, False)
    with col3:
        if is_total_like:
            scope = st.selectbox(t("Gender:"), list(jm.GENDER.keys()), disabled=prev_compare, format_func=t)
        else:
            scope = st.selectbox(t("Group:"), list(jm.INFORMALITY_GROUP.keys()), disabled=prev_compare, format_func=t)

    prev_years = st.session_state.get("inf_years", [])
    prev_period = st.session_state.get("inf_period", "Annual average")
    prev_pres = st.session_state.get("inf_presidents", [])

    period_active = prev_period not in (None, "Annual average")
    windows_active = bool(prev_years) or bool(prev_pres)
    period_disabled = windows_active
    year_disabled = period_active

    with col4:
        period = st.selectbox(
            t("Period:"), ["Annual average"] + list(jm.PERIOD_EN.values()),
            key="inf_period", disabled=period_disabled, format_func=t,
        )

    if is_total_like:
        cfg = jm.INFORMALITY_TOTAL_LIKE[stem]
        # Gender = Total -> <stem>.csv; Men/Women -> <sexo>.csv filtered by Sexo column
        if scope == "Total":
            data = _inf_total_load(stem, cfg)
        else:
            data = _inf_total_load(cfg["sexo"], cfg, "Hombres" if scope == "Men" else "Mujeres")
        # <sexo>.csv (all genders) always needed for Compare men vs. women
        compare_df = _inf_total_load(cfg["sexo"], cfg)
        denom_sp = "Población ocupada"
    else:
        grouped = _inf_prep(load_csv(f"{INFORMALITY_BASE}{stem}.csv"))
        group_sp = jm.INFORMALITY_GROUP[scope]
        data = grouped[grouped["Grupo"] == group_sp]
        compare_df = grouped              # group-compare helper filters per Grupo
        denom_sp = group_sp
        # Reused dicts carry rollups + concepts from other groups; keep only this group's breakdown.
        rollups = set(jm.INFORMALITY_GROUP.values())
        present = set(data["Concepto"])
        terms = {k: v for k, v in terms.items() if k in present and k not in rollups}

    concept_key = f"inf_concepts_{stem}"
    if prev_compare:                      # Compare charts one concept, one year -> cap both
        _cap_one([concept_key, "inf_years"])
    default_concept = terms[cfg["default"]] if is_total_like else next(iter(terms.values()))
    concept_labels = st.sidebar.multiselect(
        t("Concepts:"), list(terms.values()), default=[default_concept],
        key=concept_key, on_change=_cap, args=(concept_key, ["inf_years"]), format_func=t,
    )
    if not concept_labels:
        concept_labels = [default_concept]
    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}

    president_disabled = period_active or prev_compare or len(concepts_sp) >= 2
    year_options = sorted(data["Fecha"].unique())
    cur_years = st.sidebar.multiselect(
        t("Year:"), year_options, key="inf_years", disabled=year_disabled,
        on_change=_cap, args=("inf_years", [concept_key]),
    )

    selected_presidents, chart_type = mf.job_market_sidebar_filters(
        mf.informality_pivot(data, None, concepts_sp),
        top_placeholder, president_placeholder,
        president_disabled=president_disabled, president_key="inf_presidents",
    )

    percent = st.sidebar.checkbox(t("Show percentages"), value=False)
    metric = "Share (%)" if percent else "People"

    compare_label = "Compare men vs. women" if is_total_like else "Compare formal vs. informal"
    compare = st.sidebar.checkbox(t(compare_label), value=False, key=compare_key)

    years_sel = [] if year_disabled else cur_years
    presidents_sel = [] if president_disabled else selected_presidents
    year_set = _year_set(years_sel, presidents_sel, year_options)

    pct_note = ("Each value is a share of the occupied population." if is_total_like
                else "Each value is a share of that group's total.")

    if compare:
        concept_sp = concepts_sp[0]
        comp_pivot = mf.informality_gender_pivot if is_total_like else mf.informality_group_pivot
        comp_axis = mf.informality_gender_period_axis if is_total_like else mf.informality_group_period_axis
        comp_subtitle = "Men vs Women" if is_total_like else "Formal vs Informal"
        if year_set:
            year = sorted(year_set)[0]
            series = comp_axis(compare_df, year, concept_sp, percent=percent)
            info = [f"{t(concept_labels[0])} — {t(file_label)} ({t(comp_subtitle)}) · {year}{t(' by 3-month window')}",
                    "Period", metric]
        else:
            period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
            series = comp_pivot(compare_df, period_sp, concept_sp, percent=percent)
            info = [f"{t(concept_labels[0])} — {t(file_label)} ({t(comp_subtitle)}) · {t(period)}", "Year", metric]
        _draw(chart_type, series, info)
        if percent:
            st.caption(t(pct_note))
        st.caption(t("Source: DANE (GEIH)"))
        return

    if year_set:
        years_sorted = sorted(year_set)
        if len(concepts_sp) >= 2:
            years_sorted, labels = years_sorted[:1], eng_map
            title_subject = str(years_sorted[0])
        else:
            labels = {}
            title_subject = concept_labels[0]
        series = mf.informality_period_axis(data, years_sorted, concepts_sp,
                                            percent=percent, denom_sp=denom_sp)
        info = [f"{t(title_subject)} — {t(file_label)} ({t(scope)}){t(' by 3-month window')}", "Period", metric]
        _draw(chart_type, series, info, labels=labels,
              display_names=list(eng_map.values()) if labels else None)
        if percent:
            st.caption(t(pct_note))
        st.caption(t("Source: DANE (GEIH)"))
        return

    period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
    series = mf.informality_pivot(data, period_sp, concepts_sp, percent=percent, denom_sp=denom_sp)
    info = [f"{t('Employment Formality')} — {t(file_label)} ({t(scope)}) · {t(period)}", "Year", metric]
    _draw(chart_type, series, info, labels=eng_map,
          display_names=list(eng_map.values()))
    if percent:
        st.caption(t(pct_note))
    st.caption(t("Source: DANE (GEIH)"))


def render_departments() -> None:
    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Map", "Line", "Bar", "Table"], format_func=t)

    col1, col2, col3 = st.columns(3)
    with col1:
        table = st.selectbox(t("Table:"), ["Total", "By Activity Branch"], format_func=t)
    branch = table == "By Activity Branch"
    terms = jm.dept_ramas_terms if branch else jm.total_terms
    denom_sp = "Total ocupados" if branch else jm.PET_CONCEPT
    labels = list(terms.values())
    default = labels[0] if branch else terms[jm.DEPT_DEFAULT_CONCEPT]

    # Symmetric cap via _cap (not disabled/max_selections): only one of {Concepts, Years,
    # Departments} may be multi; the restricted two stay editable (cap 1) and remember their value.
    # Per-table concept key re-defaults on Table switch.
    prev_compare = st.session_state.get("dept_compare", False)
    ckey = f"dept_concepts_{'ramas' if branch else 'total'}"
    if prev_compare and not branch:       # Compare charts one concept, one department -> cap both
        _cap_one([ckey, "dept_depts"])

    if chart_type == "Map":
        with col2:
            concept_label = st.selectbox(t("Concept:"), labels, index=labels.index(default), format_func=t)
        concept_labels = [concept_label]
    else:
        with col2:
            concept_labels = st.multiselect(
                t("Concepts:"), labels, default=[default], key=ckey,
                on_change=_cap, args=(ckey, ["dept_depts", "dept_years"]), format_func=t,
            )
        if not concept_labels:
            concept_labels = [default]
        concept_label = concept_labels[0]
    concept_sp = find_key_by_value(terms, concept_label)

    gender = "Total"
    if not branch:
        with col3:
            gender = st.selectbox(t("Gender:"), list(jm.DEPT_GENDER_FILES.keys()),
                                  disabled=prev_compare, format_func=t)
    stem = "ramas_actividad" if branch else jm.DEPT_GENDER_FILES[gender]
    df = load_csv(f"{DEPT_BASE}{stem}.csv")
    years = sorted(df["Fecha"].unique())

    if chart_type == "Map":
        year = st.sidebar.selectbox(t("Year:"), years, index=len(years) - 1)
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        grouped = mf.dept_jm_map_data(df[df["Fecha"] == year], concept_sp, geojson, denom_sp=denom_sp)
        label = "Share (%)" if branch else "Rate (%)"
        info = [f"{t(concept_label)} {t('by department')} — {year}", "Department", label]
        fig = dc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, "value", info, val_fmt=",.1f")
        mc.render_chart(fig)
        st.caption(t("Departments in grey have no data for the selected year."))
        st.caption(t("Source: DANE (GEIH)"))
        return

    # Line / Bar: only one of {concepts, years, departments} may be multi (peer cap via _cap).
    dept_names = sorted(df["Departamentos"].unique())
    depts = st.sidebar.multiselect(t("Departments:"), dept_names, key="dept_depts",
                                   on_change=_cap, args=("dept_depts", [ckey, "dept_years"]))
    sel_years = st.sidebar.multiselect(t("Year:"), years, key="dept_years",
                                       on_change=_cap, args=("dept_years", [ckey, "dept_depts"]))
    with st.sidebar:
        selected_presidents = president_multiselect(
            get_valid_presidents(years), key="dept_presidents")
    percent = (not branch) and st.sidebar.checkbox(t("Show percentages"), value=False)
    compare = (not branch) and st.sidebar.checkbox(
        t("Compare men vs. women"), value=False, key="dept_compare")
    metric = "Share (%)" if percent else "People"

    if not depts:
        st.info(t("Select one or more departments."))
        return

    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}

    presidents_sel = selected_presidents
    year_set = _year_set(sel_years, presidents_sel, years)

    scope = ", ".join(presidents_sel) if presidents_sel else (
        ", ".join(map(str, sorted(year_set))) if year_set else t("all years"))

    def _filter(frame):
        f = frame[frame["Departamentos"].isin(depts)]
        return f[f["Fecha"].isin(year_set)] if year_set else f

    if compare:  # Men vs Women for one concept, departments summed
        cols = {}
        for lbl, g in (("Men", "hombres"), ("Women", "mujeres")):
            gdf = _filter(load_csv(f"{DEPT_BASE}{g}.csv"))
            cols[lbl] = mf.dept_jm_pivot(gdf, [concept_sp], denom_sp, percent=percent).iloc[:, 0]
        series = pd.DataFrame(cols)
        info = [f"{t(concept_label)} ({t('Men vs Women')}) — {scope}", "Year", metric]
        labels_arg = None
    elif len(depts) >= 2:  # series = departments
        series = mf.dept_jm_dept_pivot(_filter(df), concept_sp, denom_sp, percent=percent)
        info = [f"{t(concept_label)} {t('by department')} — {scope}", "Year", metric]
        labels_arg = None
    else:  # series = concepts
        series = mf.dept_jm_pivot(_filter(df), concepts_sp, denom_sp, percent=percent)
        info = [f"{t(table)} ({t(gender)}) · {depts[0]} — {scope}", "Year", metric]
        labels_arg = eng_map

    _draw(chart_type, series, info, labels=labels_arg,
          display_names=list(eng_map.values()) if labels_arg else None)
    if compare and percent:
        st.caption(t(jm.PET_PCT_NOTE))
    st.caption(t("Source: DANE (GEIH)"))


def render_regions() -> None:
    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Map", "Line", "Bar", "Table"], format_func=t)

    terms = jm.region_terms
    denom_sp = jm.REGION_PET_CONCEPT
    labels = list(terms.values())
    default = terms[jm.REGION_DEFAULT_CONCEPT]

    # Period (semester) / Year / President are mutually-exclusive axes (mirror Labor Force);
    # Concepts / Regions / Years peer-cap via _cap (only one multi); Compare caps concept + region.
    prev_years = st.session_state.get("region_years", [])
    prev_pres = st.session_state.get("region_presidents", [])
    prev_period = st.session_state.get("region_period", "Annual average")
    prev_compare = st.session_state.get("region_compare", False)

    period_active = prev_period not in (None, "Annual average")
    windows_active = bool(prev_years) or bool(prev_pres)

    col1, col2, col3 = st.columns(3)
    with col1:
        period = st.selectbox(
            t("Period:"), ["Annual average"] + list(jm.REGION_PERIOD_EN.values()),
            key="region_period", disabled=(chart_type != "Map") and windows_active, format_func=t,
        )
    period_sp = None if period == "Annual average" else find_key_by_value(jm.REGION_PERIOD_EN, period)

    ckey = "region_concepts"
    if prev_compare:                       # Compare charts one concept, one region -> cap both
        _cap_one([ckey, "region_regions"])
    if chart_type == "Map":
        with col2:
            concept_label = st.selectbox(t("Concept:"), labels, index=labels.index(default), format_func=t)
        concept_labels = [concept_label]
    else:
        with col2:
            concept_labels = st.multiselect(
                t("Concepts:"), labels, default=[default], key=ckey,
                on_change=_cap, args=(ckey, ["region_regions", "region_years"]), format_func=t,
            )
        if not concept_labels:
            concept_labels = [default]
        concept_label = concept_labels[0]
    concept_sp = find_key_by_value(terms, concept_label)

    with col3:
        gender = st.selectbox(t("Gender:"), list(jm.REGION_GENDER.keys()), disabled=prev_compare, format_func=t)
    gender_sx = jm.REGION_GENDER[gender]

    compare = chart_type != "Map" and prev_compare  # widget rendered at the bottom of the sidebar

    # Total -> total.csv (no Sexo column); Men / Women / Compare -> sexo.csv.
    df = mf.region_norm(load_csv(f"{REGION_BASE}{'sexo' if gender_sx or compare else 'total'}.csv"))
    if gender_sx and not compare:
        df = df[df["Sexo"] == gender_sx]
    years = sorted(df["Fecha"].unique())

    if chart_type == "Map":
        year = st.sidebar.selectbox(t("Year:"), years, index=len(years) - 1)
        geojson = load_geojson(REGION_GEOJSON_PATH)
        mdf = df[df["Fecha"] == year]
        if period_sp:
            mdf = mdf[mdf["Periodo"] == period_sp]
        grouped = mf.region_jm_map_data(mdf, concept_sp, denom_sp=denom_sp)
        suffix = f" · {t(period)}" if period_sp else ""
        info = [f"{t(concept_label)} {t('by region')} — {year}{suffix}", "Region", "Rate (%)"]
        fig = dc.colombia_choropleth(grouped, geojson, REGION_FEATURE_KEY, "value", info, val_fmt=",.1f")
        mc.render_chart(fig)
        st.caption(t("Source: DANE (GEIH)"))
        return

    # Line / Bar: only one of {concepts, regions, years} may be multi (peer cap via _cap).
    region_names = sorted(df["Perspectiva"].unique())
    sel_regions = st.sidebar.multiselect(t("Regions:"), region_names, key="region_regions",
                                         format_func=lambda r: t(jm.REGION_EN.get(r, r)),
                                         on_change=_cap, args=("region_regions", [ckey, "region_years"]))
    sel_years = st.sidebar.multiselect(t("Year:"), years, key="region_years", disabled=period_active,
                                       on_change=_cap, args=("region_years", [ckey, "region_regions"]))
    with st.sidebar:
        selected_presidents = president_multiselect(
            get_valid_presidents(years), disabled=period_active or len(concept_labels) >= 2,
            key="region_presidents")
    percent = st.sidebar.checkbox(t("Show percentages"), value=False)
    st.sidebar.checkbox(t("Compare men vs. women"), value=False, key="region_compare")
    metric = "Share (%)" if percent else "People"

    if not sel_regions:
        st.info(t("Select one or more regions."))
        return

    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}
    rmap = {r: jm.REGION_EN[r] for r in sel_regions}

    # Null out period-locked controls so a stale lock can't leak into mode resolution.
    years_sel = [] if period_active else sel_years
    presidents_sel = [] if (period_active or len(concept_labels) >= 2) else selected_presidents
    year_set = _year_set(years_sel, presidents_sel, years)

    scope = ", ".join(presidents_sel) if presidents_sel else (
        ", ".join(map(str, sorted(year_set))) if year_set else t("all years"))
    region_series = len(sel_regions) >= 2

    def _filter(frame):
        f = frame[frame["Perspectiva"].isin(sel_regions)]
        return f[f["Fecha"].isin(year_set)] if year_set else f

    if compare:  # Men vs Women for one concept, one region
        region = sel_regions[0]
        cdf = df[df["Perspectiva"] == region]
        if len(year_set) == 1:  # single year -> x = semesters
            year = sorted(year_set)[0]
            series = mf.region_jm_gender_period_axis(cdf, year, concept_sp, region, percent=percent)
            info = [f"{t(concept_label)} · {t(rmap[region])} ({t('Men vs Women')}) — {year}{t(' by semester')}", "Period", metric]
        else:  # x = years
            cdf = cdf[cdf["Fecha"].isin(year_set)] if year_set else cdf
            series = mf.region_jm_gender_pivot(cdf, period_sp, concept_sp, percent=percent)
            info = [f"{t(concept_label)} · {t(rmap[region])} ({t('Men vs Women')}) — {scope}", "Year", metric]
        labels_arg = None
    elif year_set:  # year(s) selected -> x = semesters, one line per multi dim (mirror Labor Force)
        series = mf.region_jm_period_axis(_filter(df), sorted(year_set), concepts_sp, sel_regions, percent=percent)
        if region_series:                       # one line per region
            info = [f"{t(concept_label)} {t('by region')} — {scope}{t(' by semester')}", "Period", metric]
            labels_arg = rmap
        elif len(concepts_sp) >= 2:             # one line per concept
            info = [f"{t(rmap[sel_regions[0]])} — {scope}{t(' by semester')}", "Period", metric]
            labels_arg = eng_map
        else:                                   # one line per year (columns are year strings)
            info = [f"{t(concept_label)} · {t(rmap[sel_regions[0]])} — {scope}{t(' by semester')}", "Period", metric]
            labels_arg = None
    elif region_series:  # no years -> year axis, series = regions
        series = mf.region_jm_region_pivot(_filter(df), concept_sp, period_sp, percent=percent)
        info = [f"{t(concept_label)} {t('by region')} — {scope}", "Year", metric]
        labels_arg = rmap
    else:  # no years -> year axis, series = concepts (one region)
        series = mf.region_jm_pivot(_filter(df), concepts_sp, period_sp, percent=percent)
        info = [f"{t(rmap[sel_regions[0]])} ({t(gender)}) — {scope}", "Year", metric]
        labels_arg = eng_map

    _draw(chart_type, series, info, labels=labels_arg,
          display_names=list(labels_arg.values()) if labels_arg else None)
    if compare and percent:
        st.caption(t(jm.PET_PCT_NOTE))
    st.caption(t("Source: DANE (GEIH)"))


def render_child_labor() -> None:
    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    col2, col3 = st.columns(2)
    with col2:
        file_label = st.selectbox(t("Table:"), list(jm.CHILD_LABOR_FILES.keys()), format_func=t)
    stem = jm.CHILD_LABOR_FILES[file_label]

    # Both-sexes 5–17 minor count from total.csv: gender-share denom (Total) AND horas denom.
    tot = load_csv(f"{CHILD_LABOR_BASE}total.csv")
    all_minors = tot[(tot["Perspectiva"] == "Total nacional")
                     & (tot["Concepto"] == jm.CHILD_LABOR_ALL_MINORS)].set_index("Fecha")["Valor"]
    total_pop = tot[(tot["Perspectiva"] == "Total nacional")
                    & (tot["Concepto"] == jm.CHILD_TOTAL_POP)].set_index("Fecha")["Valor"]

    # Per-table scope selector + data load + concept options. edad/horas have no Sexo column.
    scope = None
    if stem == "total":
        compare_key = "cl_gender_compare"
        prev_compare = st.session_state.get(compare_key, False)
        with col3:
            gender = st.selectbox(t("Gender:"), list(jm.REGION_GENDER.keys()), disabled=prev_compare, format_func=t)
        gender_sx = jm.REGION_GENDER[gender]
        scope = gender
        # Total -> total.csv; Men/Women/Compare -> sexo.csv (gender-prefixed concepts).
        use_sexo = bool(gender_sx) or prev_compare
        df = load_csv(f"{CHILD_LABOR_BASE}{'sexo' if use_sexo else 'total'}.csv")
        df = df[df["Perspectiva"] == "Total nacional"]
        if gender_sx and not prev_compare:
            df = df[df["Sexo"] == gender_sx]
        concept_options = list(jm.CHILD_LABOR_CONCEPTS)
    elif stem == "edad":
        compare_key = "cl_age_compare"
        prev_compare = st.session_state.get(compare_key, False)
        with col3:
            group = st.selectbox(t("Group:"), list(jm.CHILD_AGE_GROUPS.keys()), disabled=prev_compare)
        band_sp = jm.CHILD_AGE_GROUPS[group]
        scope = group
        df = load_csv(f"{CHILD_LABOR_BASE}edad.csv")
        df = df[df["Perspectiva"] == "Total nacional"]
        concept_options = list(jm.CHILD_AGE_CONCEPTS)
    elif stem == "horas":
        compare_key = None
        df = load_csv(f"{CHILD_LABOR_BASE}horas.csv")
        df = df[df["Perspectiva"] == "Total nacional"]
        concept_options = list(jm.CHILD_HOURS_CONCEPTS)
    elif stem == "asistencia_escolar":
        compare_key = None
        df = load_csv(f"{CHILD_LABOR_BASE}asistencia_escolar.csv")
        df = df[(df["Perspectiva"] == "Total nacional")
                & (df["Grupo"] == jm.CHILD_ASISTENCIA_GROUP)]
        concept_options = list(jm.CHILD_ASISTENCIA_CONCEPTS)
    elif stem == "ingreso":
        compare_key = None
        df = load_csv(f"{CHILD_LABOR_BASE}ingreso.csv")
        df = df[df["Perspectiva"] == "Total nacional"]
        concept_options = list(jm.CHILD_INGRESO_CONCEPTS)
    elif stem == "razon":
        compare_key = None
        df = load_csv(f"{CHILD_LABOR_BASE}razon.csv")
        df = df[df["Perspectiva"] == "Total nacional"]
        concept_options = list(jm.CHILD_RAZON_CONCEPTS)
    elif stem == "rama_actividad":
        compare_key = None
        df = load_csv(f"{CHILD_LABOR_BASE}rama_actividad.csv")
        df = df[df["Perspectiva"] == "Total nacional"]
        concept_options = list(jm.CHILD_RAMA_CONCEPTS)
    elif stem == "actividades_sexo":  # gender via Sexo column (mirror total)
        compare_key = "cl_act_compare"
        prev_compare = st.session_state.get(compare_key, False)
        with col3:
            gender = st.selectbox(t("Gender:"), list(jm.REGION_GENDER.keys()), disabled=prev_compare, format_func=t)
        gender_sx = jm.REGION_GENDER[gender]   # None / Hombres / Mujeres
        scope = gender
        df = load_csv(f"{CHILD_LABOR_BASE}actividades_sexo.csv")
        if not prev_compare:                   # compare needs all sexes
            df = df[df["Sexo"] == (gender_sx or "Total")]
        concept_options = list(jm.CHILD_ACT_CONCEPTS)
    else:  # posicion
        compare_key = None
        df = load_csv(f"{CHILD_LABOR_BASE}posicion.csv")
        df = df[df["Perspectiva"] == "Total nacional"]
        concept_options = list(jm.CHILD_POSICION_CONCEPTS)

    years = sorted(df["Fecha"].unique())

    # Concepts (per-stem key so sets don't collide across tables); Compare caps to one concept.
    concept_key = f"cl_concepts_{stem}"
    if compare_key and st.session_state.get(compare_key, False):
        _cap_one([concept_key])
    concept_labels = st.sidebar.multiselect(
        t("Concepts:"), concept_options, default=[concept_options[0]], key=concept_key, format_func=t)
    if not concept_labels:
        concept_labels = [concept_options[0]]

    cur_years = st.sidebar.multiselect(t("Year:"), years, key="cl_years")

    # (label, count_sp, rate_sp) specs + the % denominator series per table.
    if stem == "total":
        specs = [(lbl, jm.CHILD_LABOR_CONCEPTS[lbl][gender], jm.CHILD_LABOR_CONCEPTS[lbl]["rate"])
                 for lbl in concept_labels]
        pivot_df, denom = df, all_minors
    elif stem == "edad":
        pivot_df = df[df["Grupo"] == band_sp]
        denom = total_pop  # breakdowns use CSV rates; only the age-group total uses this denom
        specs = [(lbl, _age_count(band_sp, jm.CHILD_AGE_CONCEPTS[lbl]["suffix"]),
                  jm.CHILD_AGE_CONCEPTS[lbl]["rate"]) for lbl in concept_labels]
    elif stem == "horas":  # horas: buckets have no CSV rate -> share of working 5–17 (in horas.csv)
        specs = [(lbl, jm.CHILD_HOURS_CONCEPTS[lbl], None) for lbl in concept_labels]
        pivot_df = df
        denom = df[df["Concepto"] == jm.CHILD_HOURS_DENOM].set_index("Fecha")["Valor"]
    elif stem == "asistencia_escolar":  # % = concept / working total (in asistencia_escolar.csv)
        specs = [(lbl, jm.CHILD_ASISTENCIA_CONCEPTS[lbl], None) for lbl in concept_labels]
        pivot_df = df
        denom = df[df["Concepto"] == jm.CHILD_HOURS_DENOM].set_index("Fecha")["Valor"]
    elif stem == "ingreso":  # ingreso: % = bracket / working total (in ingreso.csv)
        specs = [(lbl, jm.CHILD_INGRESO_CONCEPTS[lbl], None) for lbl in concept_labels]
        pivot_df = df
        denom = df[df["Concepto"] == jm.CHILD_HOURS_DENOM].set_index("Fecha")["Valor"]
    elif stem == "razon":  # razon: % = reason / working total (in razon.csv)
        specs = [(lbl, jm.CHILD_RAZON_CONCEPTS[lbl], None) for lbl in concept_labels]
        pivot_df = df
        denom = df[df["Concepto"] == jm.CHILD_HOURS_DENOM].set_index("Fecha")["Valor"]
    elif stem == "rama_actividad":  # % = branch / working total (in rama_actividad.csv)
        specs = [(lbl, jm.CHILD_RAMA_CONCEPTS[lbl], None) for lbl in concept_labels]
        pivot_df = df
        denom = df[df["Concepto"] == jm.CHILD_HOURS_DENOM].set_index("Fecha")["Valor"]
    elif stem == "actividades_sexo":  # % = task / domestic-care total of the selected gender
        specs = [(lbl, jm.CHILD_ACT_CONCEPTS[lbl], None) for lbl in concept_labels]
        pivot_df = df
        denom = df[df["Concepto"] == jm.CHILD_ACT_DENOM].set_index("Fecha")["Valor"]
    else:  # posicion: % = position / working total (in posicion.csv)
        specs = [(lbl, jm.CHILD_POSICION_CONCEPTS[lbl], None) for lbl in concept_labels]
        pivot_df = df
        denom = df[df["Concepto"] == jm.CHILD_HOURS_DENOM].set_index("Fecha")["Valor"]

    _cap_one(["cl_presidents"])               # one president at a time (no year accumulation)
    selected_presidents, chart_type = mf.job_market_sidebar_filters(
        mf.child_labor_pivot(pivot_df, specs, denom),
        top_placeholder, president_placeholder, president_key="cl_presidents")

    percent = st.sidebar.checkbox(t("Show percentages"), value=False)
    metric = "Share (%)" if percent else "People"
    if compare_key == "cl_gender_compare":
        compare = st.sidebar.checkbox(t("Compare men vs. women"), value=False, key=compare_key)
    elif compare_key == "cl_age_compare":
        compare = st.sidebar.checkbox(t("Compare 5–14 vs 15–17"), value=False, key=compare_key)
    elif compare_key == "cl_act_compare":
        compare = st.sidebar.checkbox(t("Compare men vs. women"), value=False, key=compare_key)
    else:
        compare = False

    year_set = _year_set(cur_years, selected_presidents, years)

    def _filter(frame):
        return frame[frame["Fecha"].isin(year_set)] if year_set else frame

    if compare and stem == "total":
        lbl = concept_labels[0]
        cfg = jm.CHILD_LABOR_CONCEPTS[lbl]
        spec = ({"Men": cfg["Men"], "Women": cfg["Women"]}, cfg["rate"])
        series = mf.child_labor_gender_pivot(_filter(df), spec, all_minors, percent=percent)
        info = [f"{t(lbl)} — {t('Child Labor')} ({t('Men vs Women')})", "Year", metric]
    elif compare and stem == "edad":  # one concept, series = the two age bands
        lbl = concept_labels[0]
        suffix = jm.CHILD_AGE_CONCEPTS[lbl]["suffix"]
        rate_sp = jm.CHILD_AGE_CONCEPTS[lbl]["rate"]
        cols = {}
        for g_label, g_sp in jm.CHILD_AGE_GROUPS.items():
            bdf = _filter(df[df["Grupo"] == g_sp])
            s = mf.child_labor_pivot(bdf, [(g_label, _age_count(g_sp, suffix), rate_sp)],
                                     total_pop, percent=percent)
            cols[g_label] = s.iloc[:, 0] if not s.empty else pd.Series(dtype=float)
        series = pd.DataFrame(cols)
        info = [f"{t(lbl)} — {t('Child Labor')} (5–14 vs 15–17)", "Year", metric]
    elif compare and stem == "actividades_sexo":  # one task, series = Men vs Women, within-gender %
        lbl = concept_labels[0]
        concept_sp = jm.CHILD_ACT_CONCEPTS[lbl]
        cols = {}
        for g_label, g_sp in (("Men", "Hombres"), ("Women", "Mujeres")):
            gdf = _filter(df[df["Sexo"] == g_sp])
            gden = gdf[gdf["Concepto"] == jm.CHILD_ACT_DENOM].set_index("Fecha")["Valor"]
            s = mf.child_labor_pivot(gdf, [(g_label, concept_sp, None)], gden, percent=percent)
            cols[g_label] = s.iloc[:, 0] if not s.empty else pd.Series(dtype=float)
        series = pd.DataFrame(cols)
        info = [f"{t(lbl)} — {t('Child Labor')} ({t('Men vs Women')})", "Year", metric]
    else:
        series = mf.child_labor_pivot(_filter(pivot_df), specs, denom, percent=percent)
        info = [f"{t('Child Labor')} — {t(file_label)}" + (f" ({t(scope)})" if scope else ""), "Year", metric]

    if len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    _draw(chart_type, series, info)
    if percent and stem == "total" and compare:
        st.caption(t("Each percentage is relative to that gender's own total population, not the total."))
    elif percent and stem == "edad":
        st.caption(t("Breakdowns use the official DANE rates (TTI / TTIAD / TTIADC); the age-group total is its share of the whole population."))
    elif percent and stem in ("horas", "asistencia_escolar", "ingreso", "razon", "posicion",
                              "rama_actividad"):
        st.caption(t("Each percentage is a share of all working children aged 5–17."))
    elif percent and stem == "actividades_sexo":
        st.caption(t("Each percentage is a share of children aged 5–17 doing unpaid domestic & "
                   "care work, within the selected gender."))
    st.caption(t("Source: DANE (GEIH)"))
