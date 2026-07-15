import streamlit as st
import pandas as pd
from pages.helpers.macro import gdp_functions as mf
from pages.helpers import charts as mc
import generalities.macro_generalities.gdp_spend as t
from generalities.macro_generalities.gdp_production import production_summarize_terms as p
from generalities.macro_generalities.gdp_income import income_summarize_terms as income
from generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, find_key_by_value, show_all_years, president_multiselect, reshape_by_presidents, load_csv, BASE_DIR

REAL_ANNUAL_PATH    = BASE_DIR / "data/banco_republica/GDP/real_annual.csv"
NOMINAL_ANNUAL_PATH = BASE_DIR / "data/banco_republica/GDP/nominal_annual.csv"
POPULATION_PATH     = BASE_DIR / "data/dane/population/nacional.csv"
QUARTER_GROWTH_PATH = BASE_DIR / "data/banco_republica/GDP/quarter_growth.csv"
PRODUCTION_PATH     = BASE_DIR / "data/dane/GDP/production/summarize.csv"
INCOME_PATH         = BASE_DIR / "data/dane/GDP/income/summarize.csv"
SPEND_BASE_PATH     = str(BASE_DIR / "data/dane/GDP/spend") + "/"

def render_gdp(gdp_df: pd.DataFrame) -> None:
    gdp_local = gdp_df.copy()
 
    st.title("GDP")

    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.selectbox("Method:", ["Total Values", "Growth"]) 

    if method == "Total Values":
        with col2:
            perspective = st.selectbox("Perspective:", ["Spend", "Production", "Income"])

        if perspective == "Spend":
            cats = t.spend_categories
            with col3:
                category = st.selectbox("Category:", cats.values())

            filename = find_key_by_value(cats, category)
            selected_terms = t.spend_terms_map.get(filename)

            if category != "Summarize":
                path = f"{SPEND_BASE_PATH}{filename}.csv"
                gdp_local = load_csv(path, dtype=str).copy()
                variable = 0
                banco_path = None
            else:
                variable = -1
                banco_path = REAL_ANNUAL_PATH

            gdp_info = ["Real GDP per Year", "Year", "Trillion (COP)", "Chained volume series"]
            mf.generalities_spend_product(gdp_local, selected_terms, {"variable": variable, "banco_path": banco_path}, gdp_info)
        elif perspective == "Production":
            gdp_local = load_csv(PRODUCTION_PATH, dtype=str)

            with col3:
                category = st.selectbox("Category:", ["Summarize"])

            variable = -1

            gdp_info = ["Real GDP per Year", "Year", "Trillion (COP)", "Chained volume series"]
            mf.generalities_spend_product(gdp_local, p, {"variable": variable, "banco_path": REAL_ANNUAL_PATH}, gdp_info)
        else:
            gdp_local = load_csv(INCOME_PATH, dtype=str)

            with col3:
                category = st.selectbox("Category:", ["Summarize"])

            variable = -1

            gdp_info = ["GDP per Year", "Year", "Trillion (COP)", "Current Prices"]
            mf.generalities_spend_product(gdp_local, income, {"variable": variable, "banco_path": NOMINAL_ANNUAL_PATH}, gdp_info)
    else:
        with col2:
            source = st.selectbox("Source:", ["Spend", "Production", "Income"])
        with col3:
            growth_type = st.selectbox("Growth:", ["Annual", "Annual per Quarter", "Quarter over Quarter"])

        with st.sidebar:
            st.title("Filters")

            if source == "Spend":
                category = st.selectbox("Category:", t.spend_categories.values())
                filename = find_key_by_value(t.spend_categories, category)
                terms = t.spend_terms_map[filename]
            elif source == "Production":
                terms = p
            else:
                terms = income

            var_labels = list(terms.values())
            default = var_labels.index("Gross Domestic Product") if "Gross Domestic Product" in var_labels else 0
            var_label = st.selectbox("Variable:", var_labels, index=default)
            chart_type = st.selectbox("Chart:", ["Line", "Bar"])

        if source == "Spend":
            level_df = gdp_df if filename == "summarize" else load_csv(f"{SPEND_BASE_PATH}{filename}.csv", dtype=str)
        elif source == "Production":
            level_df = load_csv(PRODUCTION_PATH, dtype=str)
        else:
            level_df = load_csv(INCOME_PATH, dtype=str)

        concepto = find_key_by_value(terms, var_label)

        is_total  = concepto == "Producto Interno Bruto"
        use_banco = is_total and (source in ("Spend", "Production") or (source == "Income" and growth_type == "Annual"))
        nominal   = source == "Income"
        title     = f"{'' if nominal else 'Real '}{var_label} Growth"

        if growth_type == "Quarter over Quarter":
            qoq = mf.quarter_over_quarter(level_df, concepto)
            labels = list(qoq.index)

            with st.sidebar:
                start = st.selectbox("From:", labels, index=len(labels) - 20)
                end   = st.selectbox("To:", labels, index=len(labels) - 1)

            i, j = labels.index(start), labels.index(end)
            if i > j:
                i, j = j, i
            window = qoq.iloc[i:j + 1]

            info = [f"Quarter-over-Quarter {title}", "Quarter", "Growth (%)"]
            fig = mc.line_or_bar(chart_type, window, info)
            mc.render_chart(fig)
            st.caption("Source: DANE")
            if nominal:
                st.caption("Current prices (nominal)")
            return

        if growth_type == "Annual":
            quarter = None
            if use_banco:
                path = NOMINAL_ANNUAL_PATH if nominal else REAL_ANNUAL_PATH
                gdp_local = mf.load_banco_annual(path)[["Fecha", "Crecimiento"]].copy()
            else:
                gdp_local = mf.variable_growth(level_df, concepto, "annual")
        else:
            quarter = "I"
            gdp_local = load_csv(QUARTER_GROWTH_PATH, dtype=str).copy() if use_banco \
                        else mf.variable_growth(level_df, concepto, "quarter")

        years = gdp_local[gdp_local.columns[0]].str.split("-").str[0].unique()

        tmp_years = years.astype(int)

        valid_presidents = get_valid_presidents(tmp_years)

        comparing = False
        president = None

        with st.sidebar:
            selected_presidents = president_multiselect(valid_presidents)

            comparing = len(selected_presidents) >= 2
            president = selected_presidents[0] if len(selected_presidents) == 1 else None

            if comparing and quarter is not None:
                st.info("President comparison is only available in Annual mode.")
                comparing = False
                president = selected_presidents[0]

            if quarter is not None:
                quarter = st.selectbox("Quarter:", ["I", "II", "III", "IV"])

            if comparing:
                choice_year = []
            elif president:
                pres_years = [y for y in tmp_years if y in presidents[president]]
                choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
            else:
                choice_year = st.multiselect("Year:", sorted(years, reverse=True))

            if quarter is None and not comparing:
                gdp_local.index = tmp_years

                if use_banco:
                    gdp_local = show_all_years(gdp_local, president)

                gdp_local = gdp_local.reset_index(drop=True)

                st.info("If you want to choose a year prior to 2000, make sure you click \'Show all years\'")

        if comparing:
            growth = gdp_local.copy()
            growth.columns = growth.columns.str.strip()
            growth = growth.set_index("Fecha")
            growth.index = growth.index.astype(int)
            growth = growth.rename(columns={growth.columns[0]: "Growth"})
            growth["Growth"] = growth["Growth"].astype(float)
            growth, growth_info = reshape_by_presidents(
                growth[["Growth"]], selected_presidents,
                [title, "Year", "Growth (%)"],
            )
            fig = mc.line_or_bar(chart_type, growth, growth_info)
        else:
            fig = mc.gdp_growth(gdp_local, choice_year, president, 1, quarter, title, chart_type)

        mc.render_chart(fig)
        if use_banco:
            st.caption("Spliced series, base 2015")
        st.caption("Source: DANE")
        if nominal:
            st.caption("Current prices (nominal)")
