import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import job_market_functions as mf
from pages.helpers.demography import demography_charts as dc
import generalities.macro_generalities.job_market as jm
from generalities.macro_generalities.dictionaries import presidents, months
from generalities.function import (to_datatime, load_csv, load_geojson, BASE_DIR,
                                   highlight_selectbox, find_key_by_value,
                                   get_valid_presidents, president_multiselect)

INFORMALITY_BASE = str(BASE_DIR / "data/dane/job_market/informalidad") + "/"
LABOR_FORCE_BASE = str(BASE_DIR / "data/dane/job_market/Mercado Laboral") + "/"
DEPT_BASE = str(BASE_DIR / "data/dane/job_market/Departamentos") + "/"
DEPT_GEOJSON_PATH = BASE_DIR / "data/dane/geo/colombia_departments.geojson"
DEPT_FEATURE_KEY = "properties.DPTO"
REGION_BASE = str(BASE_DIR / "data/dane/job_market/regiones") + "/"
REGION_GEOJSON_PATH = BASE_DIR / "data/dane/geo/colombia_regions.geojson"
REGION_FEATURE_KEY = "properties.region"


def _cap(this, others):
    """Restrict peer multiselects to 1: if `this` dim grows to >=2 while another peer is already
    multi, keep only its newest pick. Editable + remembers the other dims (no reset, no lock)."""
    if len(st.session_state[this]) >= 2 and any(
            len(st.session_state.get(o, [])) >= 2 for o in others):
        st.session_state[this] = st.session_state[this][-1:]


def _cap_one(keys):
    """Trim each named multiselect in session_state to its newest pick (cap to 1)."""
    for k in keys:
        if len(st.session_state.get(k, [])) >= 2:
            st.session_state[k] = st.session_state[k][-1:]


def render_job_market(unemployment_df: pd.DataFrame) -> None:
    st.title("Job Market")

    dataset = st.sidebar.radio(
        "Dataset:", ["Unemployment", "Labor Force", "Departments", "Regions", "Informality"])

    if dataset == "Departments":
        render_departments()
        return

    if dataset == "Regions":
        render_regions()
        return

    if dataset == "Informality":
        render_informality()
        return

    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    if dataset == "Unemployment":
        unemp_local = to_datatime(unemployment_df, True)

        # Mutually-exclusive controls: read prior selections to gate them (Streamlit reruns
        # top-to-bottom, so the lock comes from last run's session_state).
        prev_months = st.session_state.get("unemp_months", [])
        prev_years = st.session_state.get("unemp_years", [])
        prev_pres = st.session_state.get("unemp_presidents", [])
        month_disabled = bool(prev_years or prev_pres)
        yearpres_disabled = bool(prev_months)

        year_options = sorted(unemp_local.index.year.unique())
        col1, col2 = st.columns(2)
        with col1:
            cur_years = st.multiselect(
                "Year:", year_options, key="unemp_years", disabled=yearpres_disabled
            )
        with col2:
            cur_month_labels = st.multiselect(
                "Month:", list(months.values()), key="unemp_months", disabled=month_disabled
            )

        selected_presidents, chart_type = mf.job_market_sidebar_filters(
            mf.unemployment_year_axis(unemp_local, []), top_placeholder, president_placeholder,
            president_disabled=yearpres_disabled, president_key="unemp_presidents",
        )

        # Null out disabled controls so a stale lock can't leak into mode resolution.
        month_nums = ([] if month_disabled
                      else [find_key_by_value(months, m) for m in cur_month_labels])
        years = [] if yearpres_disabled else cur_years
        presidents_sel = [] if yearpres_disabled else selected_presidents

        if years or presidents_sel:  # YEAR mode -> x = months
            year_set = set(years)
            for name in presidents_sel:
                year_set.update(presidents[name])
            series = mf.unemployment_month_axis(unemp_local, sorted(year_set))
            info = ["Unemployment rate by month", "Month", "Rate (%)"]
        else:  # MONTH mode (months selected) or DEFAULT -> x = years
            series = mf.unemployment_year_axis(unemp_local, month_nums)
            info = ["Unemployment rate", "Year", "Rate (%)"]

        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
        if not (years or presidents_sel or month_nums):
            st.caption("Showing the annual average across all months. "
                       "Pick month(s) to compare them across years, or year(s)/a president to see months.")
        st.caption("Source: Banco de la República")
        return

    # Labor Force
    col2, col3, col4 = st.columns(3)
    with col2:
        file_label = st.selectbox("Table:", list(jm.LABOR_FORCE_FILES.keys()))
    stem = jm.LABOR_FORCE_FILES[file_label]
    terms = jm.LABOR_FORCE_TERMS[stem]

    data = load_csv(f"{LABOR_FORCE_BASE}{stem}.csv")

    prev_compare = st.session_state.get("lf_gender_compare", False)
    with col3:
        gender = st.selectbox("Gender:", list(jm.GENDER.keys()), disabled=prev_compare)
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
            "Period:", ["Annual average"] + list(jm.PERIOD_EN.values()),
            key="lf_period", disabled=period_disabled,
        )

    # Concepts <-> Year peer cap via _cap (editable, remembers the other). Period/president stay
    # axis-exclusive via `disabled` above. Per-table concept key re-defaults on Table switch.
    concept_key = f"lf_concepts_{stem}"
    if prev_compare:                      # Compare charts one concept -> cap to one
        _cap_one([concept_key])
    concept_labels = st.sidebar.multiselect(
        "Concepts:", list(terms.values()), default=[next(iter(terms.values()))],
        key=concept_key, on_change=_cap, args=(concept_key, ["lf_years"]),
    )
    if not concept_labels:
        concept_labels = [next(iter(terms.values()))]
    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}

    president_disabled = period_active or prev_compare

    year_options = sorted(data["Fecha"].unique())
    cur_years = st.sidebar.multiselect(
        "Year:", year_options, key="lf_years", disabled=year_disabled,
        on_change=_cap, args=("lf_years", [concept_key]),
    )

    selected_presidents, chart_type = mf.job_market_sidebar_filters(
        mf.labor_force_pivot(data, gender_sp, None, concepts_sp),
        top_placeholder, president_placeholder,
        president_disabled=president_disabled, president_key="lf_presidents",
    )

    # Percentages only make sense for the Total table (only one with PET + rate rows).
    percent = stem == "total" and st.sidebar.checkbox("Show percentages", value=False)
    metric = "Share (%)" if percent else "People"

    compare_gender = st.sidebar.checkbox(
        "Compare men vs. women", value=False, key="lf_gender_compare"
    )

    # Null out disabled controls so a stale lock can't leak into mode resolution.
    years_sel = [] if year_disabled else cur_years
    presidents_sel = [] if president_disabled else selected_presidents
    year_set = set(years_sel)
    data_years = set(year_options)
    for name in presidents_sel:
        year_set.update(set(presidents[name]) & data_years)  # drop years the data lacks

    if compare_gender:  # Men vs Women for a single concept
        concept_sp = concepts_sp[0]
        if year_set:  # single year -> x = rolling windows
            year = sorted(year_set)[0]
            series = mf.labor_force_gender_period_axis(data, year, concept_sp, percent=percent)
            info = [f"{concept_labels[0]} — {file_label} (Men vs Women) · {year} by 3-month window",
                    "Period", metric]
        else:  # x = years (optional period filter)
            period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
            series = mf.labor_force_gender_pivot(data, period_sp, concept_sp, percent=percent)
            info = [f"{concept_labels[0]} — {file_label} (Men vs Women) · {period}", "Year", metric]
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
        if percent:
            st.caption("Each percentage is relative to that gender's own working-age population (PET), not the total.")
        st.caption("Source: DANE (GEIH)")
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
        info = [f"{title_subject} — {file_label} ({gender}) by 3-month window", "Period", metric]
        highlight = highlight_selectbox(
            series, display_names=list(eng_map.values()) if labels else None
        )
        fig = mc.line_or_bar(chart_type, series, info, labels=labels, highlight=highlight)
        mc.render_chart(fig)
        st.caption("Source: DANE (GEIH)")
        return

    # YEAR-axis mode (no years, no president)
    period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
    series = mf.labor_force_pivot(data, gender_sp, period_sp, concepts_sp, percent=percent)
    info = [f"Labor Force — {file_label} ({gender}) · {period}", "Year", metric]
    highlight = highlight_selectbox(series, display_names=list(eng_map.values()))
    fig = mc.line_or_bar(chart_type, series, info, labels=eng_map, highlight=highlight)
    mc.render_chart(fig)
    st.caption("Source: DANE (GEIH)")


def render_informality() -> None:
    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    col2, col3, col4 = st.columns(3)
    with col2:
        file_label = st.selectbox("Table:", list(jm.INFORMALITY_FILES.keys()))
    stem = jm.INFORMALITY_FILES[file_label]
    terms = jm.INFORMALITY_TERMS[stem]

    prev_compare = st.session_state.get("inf_gender_compare", False)
    with col3:
        gender = st.selectbox("Gender:", list(jm.GENDER.keys()), disabled=prev_compare)

    prev_years = st.session_state.get("inf_years", [])
    prev_period = st.session_state.get("inf_period", "Annual average")
    prev_pres = st.session_state.get("inf_presidents", [])

    period_active = prev_period not in (None, "Annual average")
    windows_active = bool(prev_years) or bool(prev_pres)
    period_disabled = windows_active
    year_disabled = period_active

    with col4:
        period = st.selectbox(
            "Period:", ["Annual average"] + list(jm.PERIOD_EN.values()),
            key="inf_period", disabled=period_disabled,
        )

    # Gender = Total -> total.csv; Men/Women -> sexo.csv filtered by Sexo column
    if gender == "Total":
        data = load_csv(f"{INFORMALITY_BASE}total.csv")
        data = data[data["Perspectiva"] == "Total nacional"].copy()
    else:
        sexo_sp = "Hombres" if gender == "Men" else "Mujeres"
        raw = load_csv(f"{INFORMALITY_BASE}sexo.csv")
        data = raw[(raw["Perspectiva"] == "Total nacional") & (raw["Sexo"] == sexo_sp)].copy()

    # sexo.csv (Total nacional) always needed for Compare men vs. women
    sexo_data = load_csv(f"{INFORMALITY_BASE}sexo.csv")
    sexo_data = sexo_data[sexo_data["Perspectiva"] == "Total nacional"].copy()

    concept_key = f"inf_concepts_{stem}"
    if prev_compare:
        _cap_one([concept_key])
    default_concept = terms[jm.INFORMALITY_DEFAULT_CONCEPT]
    concept_labels = st.sidebar.multiselect(
        "Concepts:", list(terms.values()), default=[default_concept],
        key=concept_key, on_change=_cap, args=(concept_key, ["inf_years"]),
    )
    if not concept_labels:
        concept_labels = [default_concept]
    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}

    president_disabled = period_active or prev_compare
    year_options = sorted(data["Fecha"].unique())
    cur_years = st.sidebar.multiselect(
        "Year:", year_options, key="inf_years", disabled=year_disabled,
        on_change=_cap, args=("inf_years", [concept_key]),
    )

    selected_presidents, chart_type = mf.job_market_sidebar_filters(
        mf.informality_pivot(data, None, concepts_sp),
        top_placeholder, president_placeholder,
        president_disabled=president_disabled, president_key="inf_presidents",
    )

    compare_gender = st.sidebar.checkbox(
        "Compare men vs. women", value=False, key="inf_gender_compare"
    )

    years_sel = [] if year_disabled else cur_years
    presidents_sel = [] if president_disabled else selected_presidents
    year_set = set(years_sel)
    data_years = set(year_options)
    for name in presidents_sel:
        year_set.update(set(presidents[name]) & data_years)

    if compare_gender:
        concept_sp = concepts_sp[0]
        if year_set:
            year = sorted(year_set)[0]
            series = mf.informality_gender_period_axis(sexo_data, year, concept_sp)
            info = [f"{concept_labels[0]} — {file_label} (Men vs Women) · {year} by 3-month window",
                    "Period", "People"]
        else:
            period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
            series = mf.informality_gender_pivot(sexo_data, period_sp, concept_sp)
            info = [f"{concept_labels[0]} — {file_label} (Men vs Women) · {period}", "Year", "People"]
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
        st.caption("Source: DANE (GEIH)")
        return

    if year_set:
        years_sorted = sorted(year_set)
        if len(concepts_sp) >= 2:
            years_sorted, labels = years_sorted[:1], eng_map
            title_subject = str(years_sorted[0])
        else:
            labels = {}
            title_subject = concept_labels[0]
        series = mf.informality_period_axis(data, years_sorted, concepts_sp)
        info = [f"{title_subject} — {file_label} ({gender}) by 3-month window", "Period", "People"]
        highlight = highlight_selectbox(
            series, display_names=list(eng_map.values()) if labels else None
        )
        fig = mc.line_or_bar(chart_type, series, info, labels=labels, highlight=highlight)
        mc.render_chart(fig)
        st.caption("Source: DANE (GEIH)")
        return

    period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
    series = mf.informality_pivot(data, period_sp, concepts_sp)
    info = [f"Informality — {file_label} ({gender}) · {period}", "Year", "People"]
    highlight = highlight_selectbox(series, display_names=list(eng_map.values()))
    fig = mc.line_or_bar(chart_type, series, info, labels=eng_map, highlight=highlight)
    mc.render_chart(fig)
    st.caption("Source: DANE (GEIH)")


def render_departments() -> None:
    chart_type = st.sidebar.selectbox("Chart Type:", ["Map", "Line", "Bar"])

    col1, col2, col3 = st.columns(3)
    with col1:
        table = st.selectbox("Table:", ["Total", "By Activity Branch"])
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
            concept_label = st.selectbox("Concept:", labels, index=labels.index(default))
        concept_labels = [concept_label]
    else:
        with col2:
            concept_labels = st.multiselect(
                "Concepts:", labels, default=[default], key=ckey,
                on_change=_cap, args=(ckey, ["dept_depts", "dept_years"]),
            )
        if not concept_labels:
            concept_labels = [default]
        concept_label = concept_labels[0]
    concept_sp = find_key_by_value(terms, concept_label)

    gender = "Total"
    if not branch:
        with col3:
            gender = st.selectbox("Gender:", list(jm.DEPT_GENDER_FILES.keys()),
                                  disabled=prev_compare)
    stem = "ramas_actividad" if branch else jm.DEPT_GENDER_FILES[gender]
    df = load_csv(f"{DEPT_BASE}{stem}.csv")
    years = sorted(df["Fecha"].unique())

    if chart_type == "Map":
        year = st.sidebar.selectbox("Year:", years, index=len(years) - 1)
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        grouped = mf.dept_jm_map_data(df[df["Fecha"] == year], concept_sp, geojson, denom_sp=denom_sp)
        label = "Share (%)" if branch else "Rate (%)"
        info = [f"{concept_label} by department — {year}", "Department", label]
        fig = dc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, "value", info, val_fmt=",.1f")
        mc.render_chart(fig)
        st.caption("Departments in grey have no data for the selected year.")
        st.caption("Source: DANE (GEIH)")
        return

    # Line / Bar: only one of {concepts, years, departments} may be multi (peer cap via _cap).
    dept_names = sorted(df["Departamentos"].unique())
    depts = st.sidebar.multiselect("Departments:", dept_names, key="dept_depts",
                                   on_change=_cap, args=("dept_depts", [ckey, "dept_years"]))
    sel_years = st.sidebar.multiselect("Year:", years, key="dept_years",
                                       on_change=_cap, args=("dept_years", [ckey, "dept_depts"]))
    with st.sidebar:
        selected_presidents = president_multiselect(
            get_valid_presidents(years), key="dept_presidents")
    percent = (not branch) and st.sidebar.checkbox("Show percentages", value=False)
    compare = (not branch) and st.sidebar.checkbox(
        "Compare men vs. women", value=False, key="dept_compare")
    metric = "Share (%)" if percent else "People"

    if not depts:
        st.info("Select one or more departments.")
        return

    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}

    presidents_sel = selected_presidents
    data_years = set(years)
    year_set = set(sel_years)
    for name in presidents_sel:
        year_set.update(set(presidents[name]) & data_years)  # drop years the data lacks

    scope = ", ".join(presidents_sel) if presidents_sel else (
        ", ".join(map(str, sorted(year_set))) if year_set else "all years")

    def _filter(frame):
        f = frame[frame["Departamentos"].isin(depts)]
        return f[f["Fecha"].isin(year_set)] if year_set else f

    if compare:  # Men vs Women for one concept, departments summed
        cols = {}
        for lbl, g in (("Men", "hombres"), ("Women", "mujeres")):
            gdf = _filter(load_csv(f"{DEPT_BASE}{g}.csv"))
            cols[lbl] = mf.dept_jm_pivot(gdf, [concept_sp], denom_sp, percent=percent).iloc[:, 0]
        series = pd.DataFrame(cols)
        info = [f"{concept_label} (Men vs Women) — {scope}", "Year", metric]
        labels_arg = None
    elif len(depts) >= 2:  # series = departments
        series = mf.dept_jm_dept_pivot(_filter(df), concept_sp, denom_sp, percent=percent)
        info = [f"{concept_label} by department — {scope}", "Year", metric]
        labels_arg = None
    else:  # series = concepts
        series = mf.dept_jm_pivot(_filter(df), concepts_sp, denom_sp, percent=percent)
        info = [f"{table} ({gender}) · {depts[0]} — {scope}", "Year", metric]
        labels_arg = eng_map

    highlight = highlight_selectbox(
        series, display_names=list(eng_map.values()) if labels_arg else None)
    fig = mc.line_or_bar(chart_type, series, info, labels=labels_arg or {}, highlight=highlight)
    mc.render_chart(fig)
    if compare and percent:
        st.caption("Each percentage is relative to that gender's own working-age population (PET), not the total.")
    st.caption("Source: DANE (GEIH)")


def render_regions() -> None:
    chart_type = st.sidebar.selectbox("Chart Type:", ["Map", "Line", "Bar"])

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
            "Period:", ["Annual average"] + list(jm.REGION_PERIOD_EN.values()),
            key="region_period", disabled=(chart_type != "Map") and windows_active,
        )
    period_sp = None if period == "Annual average" else find_key_by_value(jm.REGION_PERIOD_EN, period)

    ckey = "region_concepts"
    if prev_compare:                       # Compare charts one concept, one region -> cap both
        _cap_one([ckey, "region_regions"])
    if chart_type == "Map":
        with col2:
            concept_label = st.selectbox("Concept:", labels, index=labels.index(default))
        concept_labels = [concept_label]
    else:
        with col2:
            concept_labels = st.multiselect(
                "Concepts:", labels, default=[default], key=ckey,
                on_change=_cap, args=(ckey, ["region_regions", "region_years"]),
            )
        if not concept_labels:
            concept_labels = [default]
        concept_label = concept_labels[0]
    concept_sp = find_key_by_value(terms, concept_label)

    with col3:
        gender = st.selectbox("Gender:", list(jm.REGION_GENDER.keys()), disabled=prev_compare)
    gender_sx = jm.REGION_GENDER[gender]

    compare = chart_type != "Map" and prev_compare  # widget rendered at the bottom of the sidebar

    # Total -> total.csv (no Sexo column); Men / Women / Compare -> sexo.csv.
    df = mf.region_norm(load_csv(f"{REGION_BASE}{'sexo' if gender_sx or compare else 'total'}.csv"))
    if gender_sx and not compare:
        df = df[df["Sexo"] == gender_sx]
    years = sorted(df["Fecha"].unique())

    if chart_type == "Map":
        year = st.sidebar.selectbox("Year:", years, index=len(years) - 1)
        geojson = load_geojson(REGION_GEOJSON_PATH)
        mdf = df[df["Fecha"] == year]
        if period_sp:
            mdf = mdf[mdf["Periodo"] == period_sp]
        grouped = mf.region_jm_map_data(mdf, concept_sp, denom_sp=denom_sp)
        suffix = f" · {period}" if period_sp else ""
        info = [f"{concept_label} by region — {year}{suffix}", "Region", "Rate (%)"]
        fig = dc.colombia_choropleth(grouped, geojson, REGION_FEATURE_KEY, "value", info, val_fmt=",.1f")
        mc.render_chart(fig)
        st.caption("Source: DANE (GEIH)")
        return

    # Line / Bar: only one of {concepts, regions, years} may be multi (peer cap via _cap).
    region_names = sorted(df["Perspectiva"].unique())
    sel_regions = st.sidebar.multiselect("Regions:", region_names, key="region_regions",
                                         format_func=lambda r: jm.REGION_EN.get(r, r),
                                         on_change=_cap, args=("region_regions", [ckey, "region_years"]))
    sel_years = st.sidebar.multiselect("Year:", years, key="region_years", disabled=period_active,
                                       on_change=_cap, args=("region_years", [ckey, "region_regions"]))
    with st.sidebar:
        selected_presidents = president_multiselect(
            get_valid_presidents(years), disabled=period_active, key="region_presidents")
    percent = st.sidebar.checkbox("Show percentages", value=False)
    st.sidebar.checkbox("Compare men vs. women", value=False, key="region_compare")
    metric = "Share (%)" if percent else "People"

    if not sel_regions:
        st.info("Select one or more regions.")
        return

    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}
    rmap = {r: jm.REGION_EN[r] for r in sel_regions}

    # Null out period-locked controls so a stale lock can't leak into mode resolution.
    years_sel = [] if period_active else sel_years
    presidents_sel = [] if period_active else selected_presidents
    data_years = set(years)
    year_set = set(years_sel)
    for name in presidents_sel:
        year_set.update(set(presidents[name]) & data_years)  # drop years the data lacks

    scope = ", ".join(presidents_sel) if presidents_sel else (
        ", ".join(map(str, sorted(year_set))) if year_set else "all years")
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
            info = [f"{concept_label} · {rmap[region]} (Men vs Women) — {year} by semester", "Period", metric]
        else:  # x = years
            cdf = cdf[cdf["Fecha"].isin(year_set)] if year_set else cdf
            series = mf.region_jm_gender_pivot(cdf, period_sp, concept_sp, percent=percent)
            info = [f"{concept_label} · {rmap[region]} (Men vs Women) — {scope}", "Year", metric]
        labels_arg = None
    elif year_set:  # year(s) selected -> x = semesters, one line per multi dim (mirror Labor Force)
        series = mf.region_jm_period_axis(_filter(df), sorted(year_set), concepts_sp, sel_regions, percent=percent)
        if region_series:                       # one line per region
            info = [f"{concept_label} by region — {scope} by semester", "Period", metric]
            labels_arg = rmap
        elif len(concepts_sp) >= 2:             # one line per concept
            info = [f"{rmap[sel_regions[0]]} — {scope} by semester", "Period", metric]
            labels_arg = eng_map
        else:                                   # one line per year (columns are year strings)
            info = [f"{concept_label} · {rmap[sel_regions[0]]} — {scope} by semester", "Period", metric]
            labels_arg = None
    elif region_series:  # no years -> year axis, series = regions
        series = mf.region_jm_region_pivot(_filter(df), concept_sp, period_sp, percent=percent)
        info = [f"{concept_label} by region — {scope}", "Year", metric]
        labels_arg = rmap
    else:  # no years -> year axis, series = concepts (one region)
        series = mf.region_jm_pivot(_filter(df), concepts_sp, period_sp, percent=percent)
        info = [f"{rmap[sel_regions[0]]} ({gender}) — {scope}", "Year", metric]
        labels_arg = eng_map

    highlight = highlight_selectbox(
        series, display_names=list(labels_arg.values()) if labels_arg else None)
    fig = mc.line_or_bar(chart_type, series, info, labels=labels_arg or {}, highlight=highlight)
    mc.render_chart(fig)
    if compare and percent:
        st.caption("Each percentage is relative to that gender's own working-age population (PET), not the total.")
    st.caption("Source: DANE (GEIH)")
