import streamlit as st
from app_pages.helpers import charts as mc
from app_pages.helpers import charts as dc
from app_pages.helpers.demography import births_functions as bir
from app_pages.helpers.demography import deaths_functions as dth
from app_pages.helpers.demography import population_functions as pop
from generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, president_multiselect, reshape_by_presidents, load_csv, load_geojson, highlight_selectbox
from generalities.demography_generalities.deaths import DEATHS_PATHS, DEATHS_COMPARE, AREA_EN, AGE_EN as DEATHS_AGE_EN, AGE_MUNI_EN, MUNI_CAPTION
from generalities.demography_generalities.births import DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY
from generalities.demography_generalities.population import PYRAMID_MODES, POP_PATHS
from app_pages.tabs.demography._shared import _render_geo_bar_line, _render_pyramid_result
from generalities.i18n import t


def _exclude_other(other_key: str) -> None:
    st.session_state[other_key] = False


def render_deaths() -> None:
    st.title(t("Deaths"))

    compare_by = st.session_state.get("deaths_compare", DEATHS_COMPARE[0])

    with st.sidebar:
        st.header(t("Filters"))

    if compare_by == "Department":
        _render_deaths_department()
    elif compare_by == "Municipality":
        _render_deaths_municipality()
    elif compare_by == "Cause (Top 5)":
        _render_deaths_top_causes()
    elif compare_by == "Cause (Compare)":
        _render_deaths_cause_compare()
    else:
        _render_deaths_breakdown(compare_by)

    with st.sidebar:
        st.radio(t("Compare by:"), DEATHS_COMPARE, horizontal=True, key="deaths_compare", format_func=t)

    st.caption(t("Source: DANE"))


def _render_deaths_breakdown(compare_by: str) -> None:
    chart_options = ["Line", "Bar", "Table"] + (["Deaths pyramid"] if compare_by == "Age Group" else [])
    with st.sidebar:
        chart_type = st.selectbox(t("Chart Type:"), chart_options, format_func=t)

    if chart_type == "Deaths pyramid":
        _render_deaths_pyramid()
        return

    gender_cause = None
    dept_df = None
    age_cause = age_gender = None
    if compare_by == "Gender":
        cause_names = dth.deaths_cause_names(dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"]))
        with st.sidebar:
            gender_cause = st.selectbox(t("Cause:"), ["All causes"] + cause_names, format_func=t)
        if gender_cause == "All causes":
            df = load_csv(DEATHS_PATHS["total"])
        else:
            dept_df = dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"])
            df = dept_df
    elif compare_by == "Age Group":
        base_dept_df = dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"])
        cause_names = dth.deaths_cause_names(base_dept_df)
        dept_names = sorted(base_dept_df["Name"].dropna().unique())
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            age_gender = st.selectbox(t("Gender:"), ["Total", "Men", "Women"], format_func=t)
        with col2:
            age_cause = st.selectbox(t("Cause:"), ["All causes"] + cause_names, format_func=t)
        with col3:
            age_dept = st.selectbox(t("Department:"), ["All"] + dept_names, format_func=t)
        use_dept_source = age_cause != "All causes" or age_dept != "All"
        if not use_dept_source:
            df = load_csv(DEATHS_PATHS["area_age"])
        elif age_dept != "All":
            df = _deaths_dept_source()
            df = df[df["Name"] == age_dept]
        else:
            df = base_dept_df
    else:
        df = load_csv(DEATHS_PATHS["area_age"])

    years = sorted(df["Fecha"].unique().astype(int).tolist(), reverse=True)
    valid_presidents = get_valid_presidents(years)

    with st.sidebar:
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in years if y in presidents[president]] if president else years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect(t("Year:"), year_opts)

    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))

    if compare_by == "Gender":
        if gender_cause == "All causes":
            pivot, info = dth.deaths_gender_pivot(df)
        else:
            pivot, info = dth.deaths_gender_cause_pivot(dept_df, gender_cause)
    elif compare_by == "Area":
        col1, col2, col3 = st.columns(3)
        with col1:
            area_gender = st.selectbox(t("Gender:"), ["Total", "Men", "Women"], format_func=t)
        with col2:
            age_label = st.selectbox(t("Age group:"), ["All ages"] + age_labels, format_func=t)
        with col3:
            area_sel = st.selectbox(t("Area:"), ["All areas"] + list(AREA_EN.values()), format_func=t)
        pivot, info = dth.deaths_area_pivot(df, age_label, area_gender, area_sel)
    else:  # Age Group
        if not use_dept_source:
            with st.sidebar:
                area = st.selectbox(t("Area:"), ["Total"] + list(AREA_EN.values()), format_func=t)
            pivot, info = dth.deaths_age_pivot(df, age_gender, area)
        else:
            pivot, info = dth.deaths_age_cause_pivot(df, age_gender, age_cause)
            if age_dept != "All":
                info = [f"{info[0]} — {age_dept}", info[1], info[2]]
        with col4:
            chosen = st.multiselect(t("Age groups:"), list(pivot.columns), format_func=t)
        if chosen:
            pivot = pivot[chosen]

    if president:
        pivot = pivot[pivot.index.isin(presidents[president])]
    elif selected_years:
        pivot = pivot[pivot.index.isin(selected_years)]

    if comparing and not pivot.empty:
        pivot, info = reshape_by_presidents(pivot, selected_presidents, info)

    if pivot.empty:
        st.warning(t("No data for selected filters."))
        return

    highlight = highlight_selectbox(pivot)

    fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight)

    mc.render_chart(fig)


def _render_deaths_pyramid() -> None:
    base_dept_df = dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"])
    cause_names = dth.deaths_cause_names(base_dept_df)
    dept_names = sorted(base_dept_df["Name"].dropna().unique())

    c0, c1, c2 = st.columns(3)
    with c0:
        cause = st.selectbox(t("Cause:"), ["All causes"] + cause_names, format_func=t)
    with c1:
        dept = st.selectbox(t("Department:"), ["All"] + dept_names, format_func=t)
    with c2:
        mode = st.selectbox(t("Display:"), PYRAMID_MODES, format_func=t)

    use_dept_source = cause != "All causes" or dept != "All"

    if not use_dept_source:
        df = load_csv(DEATHS_PATHS["area_age"])
        with st.sidebar:
            area = st.selectbox(t("Area:"), ["Total"] + list(AREA_EN.values()), format_func=t)
        men_pivot, _ = dth.deaths_age_pivot(df, "Men", area)
        women_pivot, _ = dth.deaths_age_pivot(df, "Women", area)
    else:
        if dept != "All":
            dept_df = _deaths_dept_source()
            dept_df = dept_df[dept_df["Name"] == dept]
        else:
            dept_df = base_dept_df
        men_pivot, _ = dth.deaths_age_cause_pivot(dept_df, "Men", cause)
        women_pivot, _ = dth.deaths_age_cause_pivot(dept_df, "Women", cause)

    years = sorted(men_pivot.index.tolist(), reverse=True)
    with st.sidebar:
        year = st.selectbox(t("Year:"), years)

    men = dth.deaths_pyramid_row(men_pivot.loc[year])
    women = dth.deaths_pyramid_row(women_pivot.loc[year])
    men.name, women.name = "Men", "Women"

    title = f"{year}"
    if cause != "All causes":
        title += f" — {t(cause)}"
    if dept != "All":
        title += f" — {dept}"
    _render_pyramid_result(men, women, mode, title)


def _deaths_dept_source():
    with st.sidebar:
        place = st.selectbox(t("Place:"), ["Occurrence", "Residence"], format_func=t)
    path = DEATHS_PATHS["dept_death"] if place == "Occurrence" else DEATHS_PATHS["dept_residence"]
    return dth.deaths_dept_prepared(path)


def _dept_population_pivot(codes: list):
    """Year x Code population pivot (Total gender/age), for department death-rate denominators."""
    pop_df = pop.dept_normalize(load_csv(POP_PATHS["departmental"]))
    return pop.geo_trend(pop_df, "Code", codes, "Total", "All ages")


def _render_deaths_department() -> None:
    dept_df = _deaths_dept_source().rename(columns={"Fecha": "year"})

    all_years = sorted(dept_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))
    cause_names = dth.deaths_cause_names(dept_df)
    valid_presidents = get_valid_presidents(all_years)

    with st.sidebar:
        chart_type = st.selectbox(t("Chart Type:"), ["Map", "Line", "Bar", "Table"], format_func=t)
        cause = st.selectbox(t("Cause:"), ["All causes"] + cause_names, format_func=t)
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect(t("Year:"), year_opts)
        rate = st.checkbox(t("Show as rate per 1,000 population"), key="deaths_dept_rate_1k",
                            on_change=_exclude_other, args=("deaths_dept_rate_100k",))
        rate_100k = st.checkbox(t("Show as rate per 100,000 population"), key="deaths_dept_rate_100k",
                                 on_change=_exclude_other, args=("deaths_dept_rate_1k",))
        rate_factor = 1000 if rate else (100000 if rate_100k else None)
        is_rate = rate_factor is not None

    col1, col2, col3 = st.columns(3)
    selected_depts = []
    if chart_type != "Map":
        with col3:
            selected_depts = st.multiselect(t("Departments:"), dept_names)
    with col1:
        gender = st.selectbox(t("Gender:"), ["Total", "Men", "Women"], format_func=t)
    with col2:
        age_label = st.selectbox(t("Age:"), ["All ages"] + age_labels, format_func=t)

    if cause != "All causes":
        dept_df = dept_df[dept_df["cause"] == cause]

    dept_df["_val"] = dth.deaths_age_gender_value(dept_df, gender, age_label)
    col = "_val"
    noun = t("Deaths") if gender == "Total" else t(gender)
    if is_rate:
        noun = t("Death rate") if gender == "Total" else t("{gender} death rate").format(gender=t(gender))
    scope = t("all years") if not selected_years else ", ".join(map(str, sorted(selected_years)))
    if president and not selected_years:
        scope = president
    if age_label != "All ages":
        scope = t("{scope}, age {age}").format(scope=scope, age=t(age_label))
    if cause != "All causes":
        scope = f"{scope} — {t(cause)}"

    if chart_type == "Map":
        if comparing:
            st.info(t("Map can't compare presidents — pick a single president or switch to Line/Bar."))
            return
        map_years = selected_years or ([y for y in all_years if y in presidents[president]] if president else [])
        grouped = bir.births_department_data(dept_df, map_years, col)
        val_fmt = ",.0f"
        if is_rate:
            pop_pivot = _dept_population_pivot(grouped["Code"].tolist())
            pop_sum = pop_pivot.loc[pop_pivot.index.isin(map_years or all_years)].sum()
            grouped[col] = grouped[col] / grouped["Code"].map(pop_sum) * rate_factor
            val_fmt = ",.2f"
        info = [t("{noun} by {entity}").format(noun=noun, entity=t("department")) + f" — {scope}", "Department", noun]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = dc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, col, info, val_fmt=val_fmt)
        mc.render_chart(fig)
        if is_rate and not map_years:
            st.caption(t("No year selected: rate is deaths and population summed over all available years, not an annual rate."))
        return

    if not selected_depts:
        st.info(t("Select one or more departments."))
        return

    pivot = bir.births_geo_trend(dept_df, "departamento", selected_depts, selected_years, value_col=col)

    if is_rate:
        scoped = dept_df[dept_df["Name"].isin(selected_depts)]
        name_by_code = (
            scoped.assign(Code=scoped["departamento"].str.split(n=1).str[0])
            .drop_duplicates("Name")
            .set_index("Code")["Name"]
        )
        pop_pivot = _dept_population_pivot(list(name_by_code.index)).rename(columns=name_by_code)
        pivot = pivot.divide(pop_pivot.reindex(pivot.index)) * rate_factor

    if president:
        pivot = pivot[pivot.index.isin(presidents[president])]

    if comparing:
        info = [t("{noun} trend by {entity}").format(noun=noun, entity=t("department")), "Year", noun]
        if not pivot.empty:
            pivot, info = reshape_by_presidents(pivot, selected_presidents, info)
        if pivot.empty:
            st.warning(t("No data for selected filters."))
            return
        highlight = highlight_selectbox(pivot)
        fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight, bar_if_single=False)
        mc.render_chart(fig)
        return

    _render_geo_bar_line(pivot, chart_type, "department", scope, noun=noun)


def _render_deaths_municipality() -> None:
    dept_df = dth.deaths_muni_prepared(DEATHS_PATHS["muni_residence"]).rename(columns={"Fecha": "year"})

    all_years = sorted(dept_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    age_labels = list(dict.fromkeys(AGE_MUNI_EN.values()))
    valid_presidents = get_valid_presidents(all_years)

    with st.sidebar:
        chart_type = st.selectbox(t("Chart Type:"), ["Line", "Bar", "Table"], format_func=t)
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect(t("Year:"), year_opts)

    col1, col2, col3 = st.columns(3)
    with col1:
        dept = st.selectbox(t("Department:"), dept_names, format_func=t)
    with col2:
        gender = st.selectbox(t("Gender:"), ["Total", "Men", "Women"], format_func=t)
    with col3:
        age_label = st.selectbox(t("Age:"), ["All ages"] + age_labels, format_func=t)

    scoped = dept_df[dept_df["Name"] == dept].copy()
    muni_names = sorted(scoped["municipio"].str.split(n=1).str[1].dropna().unique())
    abroad = dept == "Abroad"

    with st.sidebar:
        selected_munis = st.multiselect(t("Countries:") if abroad else t("Municipalities:"), muni_names)

    cause_scope = scoped
    if selected_munis:
        cause_scope = scoped[scoped["municipio"].str.split(n=1).str[1].isin(selected_munis)]
    cause_names = dth.deaths_cause_names(cause_scope)

    with st.sidebar:
        cause = st.selectbox(t("Cause:"), ["All causes"] + cause_names, format_func=t)

    if cause != "All causes":
        scoped = scoped[scoped["cause"] == cause]

    scoped["_val"] = dth.deaths_age_gender_value(scoped, gender, age_label, AGE_MUNI_EN)
    col = "_val"
    noun = t("Deaths") if gender == "Total" else t(gender)
    entity = "country" if abroad else ("municipality" if selected_munis else "department")
    scope = t("all years") if not selected_years else ", ".join(map(str, sorted(selected_years)))
    if president and not selected_years:
        scope = president
    if age_label != "All ages":
        scope = t("{scope}, age {age}").format(scope=scope, age=t(age_label))
    if cause != "All causes":
        scope = f"{scope} — {t(cause)}"

    if selected_munis:
        pivot = bir.births_geo_trend(scoped, "municipio", selected_munis, selected_years, value_col=col)
    else:
        pivot = bir.births_geo_trend(scoped, "departamento", [], selected_years, value_col=col)

    if president:
        pivot = pivot[pivot.index.isin(presidents[president])]

    if comparing:
        info = [t("{noun} trend by {entity}").format(noun=noun, entity=t(entity)), "Year", noun]
        if not pivot.empty:
            pivot, info = reshape_by_presidents(pivot, selected_presidents, info)
        if pivot.empty:
            st.warning(t("No data for selected filters."))
            return
        highlight = highlight_selectbox(pivot)
        fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight, bar_if_single=False)
        mc.render_chart(fig)
        st.caption(t(MUNI_CAPTION))
        return

    _render_geo_bar_line(pivot, chart_type, entity, scope, noun=noun)
    if not pivot.empty:
        st.caption(t(MUNI_CAPTION))


def _render_deaths_top_causes() -> None:
    dept_df = _deaths_dept_source()

    all_years = sorted(dept_df["Fecha"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    valid_presidents = get_valid_presidents(all_years)
    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))

    with st.sidebar:
        selected_presidents = president_multiselect(valid_presidents)
        president = selected_presidents[0] if len(selected_presidents) == 1 else None
        year_opts = [y for y in all_years if y in presidents[president]] if president else all_years
        selected_years = [] if president else st.multiselect(t("Year:"), year_opts)

    col1, col2, col3 = st.columns(3)
    with col1:
        opts = ["All"] + dept_names
        saved = st.session_state.get("deaths_cause_dept", "All")
        idx = opts.index(saved) if saved in opts else 0
        dept = st.selectbox(t("Department:"), opts, index=idx, format_func=t)
        st.session_state["deaths_cause_dept"] = dept
    with col2:
        gender = st.selectbox(t("Gender:"), ["Total", "Men", "Women"], format_func=t)
    with col3:
        age_label = st.selectbox(t("Age:"), ["All ages"] + age_labels, format_func=t)

    dept_df["_val"] = dth.deaths_age_gender_value(dept_df, gender, age_label)
    series = dth.deaths_top_causes(dept_df, selected_years, dept, president, value_col="_val")

    if series.empty:
        st.warning(t("No data for selected filters."))
        return

    scope = ", ".join(map(str, sorted(selected_years))) if selected_years else (president or t("all years"))
    if age_label != "All ages":
        scope = t("{scope}, age {age}").format(scope=scope, age=t(age_label))
    place = dept if dept != "All" else "Colombia"
    g = "" if gender == "Total" else f" ({t(gender)})"
    info = [t("Top 5 causes of death{g} — {place}, {scope}").format(g=g, place=place, scope=scope), "Deaths", "Cause"]
    fig = mc.ranked_bar_chart(series, info)
    mc.render_chart(fig)


def _render_deaths_cause_compare() -> None:
    dept_df = _deaths_dept_source()

    all_years = sorted(dept_df["Fecha"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    valid_presidents = get_valid_presidents(all_years)
    cause_names = dth.deaths_cause_names(dept_df)
    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))

    col1, col2, col3 = st.columns(3)
    with col1:
        opts = ["All"] + dept_names
        saved = st.session_state.get("deaths_cause_dept", "All")
        idx = opts.index(saved) if saved in opts else 0
        dept = st.selectbox(t("Department:"), opts, index=idx, format_func=t)
        st.session_state["deaths_cause_dept"] = dept
    with col2:
        gender = st.selectbox(t("Gender:"), ["Total", "Men", "Women"], format_func=t)
    with col3:
        age_label = st.selectbox(t("Age:"), ["All ages"] + age_labels, format_func=t)

    with st.sidebar:
        chart_type = st.selectbox(t("Chart Type:"), ["Line", "Bar", "Table"], format_func=t)
        selected_causes = st.multiselect(t("Causes (max 5):"), ["All causes"] + cause_names, format_func=t)
        selected_presidents = president_multiselect(valid_presidents)

    if not selected_causes:
        st.info(t("Select one or more causes to compare."))
        return
    if len(selected_causes) > 5:
        st.warning(t("Select at most 5 causes."))
        return

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect(t("Year:"), year_opts)
        rate = st.checkbox(t("Show as rate per 1,000 population"), key="deaths_cause_rate_1k",
                            on_change=_exclude_other, args=("deaths_cause_rate_100k",))
        rate_100k = st.checkbox(t("Show as rate per 100,000 population"), key="deaths_cause_rate_100k",
                                 on_change=_exclude_other, args=("deaths_cause_rate_1k",))
        rate_factor = 1000 if rate else (100000 if rate_100k else None)
        is_rate = rate_factor is not None

    dept_df["_val"] = dth.deaths_age_gender_value(dept_df, gender, age_label)
    real_causes = [c for c in selected_causes if c != "All causes"]
    full_pivot = dth.deaths_cause_pivot(dept_df, cause_names, selected_years, president, value_col="_val", dept_name=dept)
    pivot = full_pivot[real_causes] if real_causes else full_pivot.iloc[:, 0:0]
    if "All causes" in selected_causes:
        pivot = pivot.assign(**{"All causes": full_pivot.sum(axis=1)})

    if is_rate and not pivot.empty:
        if dept == "All":
            denom = pop.national_total_series(load_csv(POP_PATHS["national"]))
        else:
            code = dept_df.loc[dept_df["Name"] == dept, "departamento"].iloc[0].split(" ", 1)[0]
            denom = _dept_population_pivot([code]).iloc[:, 0]
        pivot = pivot.divide(denom.reindex(pivot.index), axis=0) * rate_factor

    place = dept if dept != "All" else "Colombia"
    label = t("Death rate") if is_rate else t("Deaths")
    title = (t("{label} by cause — {place}").format(label=label, place=place) if gender == "Total"
             else t("{label} by cause ({gender}) — {place}").format(label=label, gender=t(gender), place=place))
    if age_label != "All ages":
        title = t("{title} (age {age})").format(title=title, age=t(age_label))
    info = [title, "Year", "Rate per 1,000" if rate else "Rate per 100,000" if rate_100k else "Deaths"]

    if comparing and not pivot.empty:
        pivot, info = reshape_by_presidents(pivot, selected_presidents, info)

    if pivot.empty:
        st.warning(t("No data for selected filters."))
        return

    highlight = highlight_selectbox(pivot)

    fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight)

    mc.render_chart(fig)
