import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import macro_functions as mf
from generalities.dictionaries import months, presidents
from generalities.function import find_key_by_value
import generalities.inflation as gi

def render_cpi(cpi_df: pd.DataFrame) -> None:
    cpi_local = cpi_df.copy()
    cpi_local["Fecha"] = pd.to_datetime(cpi_local["Fecha"])
    cpi_local = cpi_local.set_index("Fecha").sort_index()

    st.title("CPI")

    col1, col2, col3 = st.columns(3)

    cpi_info = ""

    all_years = cpi_local.index.year.unique().astype(int)
    president, chart_type = mf.cpi_sidebar_filters(all_years)

    with col1:
        method = st.selectbox("Method:", ["Headline Inflation", "Core Inflation (excluding 15 items)"])

    if method == "Headline Inflation":
        cats = gi.perspective_names
        with col2:
            perspective = st.selectbox("Perspective:", cats.values())

        perspective_column = find_key_by_value(cats, perspective)

        if perspective == "Annual":
            with col3:
                selected_month = st.multiselect("Month:", months.values(), default="December")

                if not selected_month:
                    selected_month = ["December"]

                number_months = [find_key_by_value(months, m) for m in selected_month]

                series_list = []
                for num, name in zip(number_months, selected_month):
                    s = cpi_local.loc[:, perspective_column].copy()
                    s = s[cpi_local.index.month == num].dropna()
                    s.index = s.index.year
                    s.name = name
                    series_list.append(s)

                cpi_series = pd.concat(series_list, axis=1)

            with st.sidebar:
                show_all = st.checkbox("Show all years", value=False)

            if not show_all and not president:
                cpi_series = cpi_series[cpi_series.index >= 2000]

            if president:
                cpi_series = cpi_series[cpi_series.index.isin(presidents[president])]

            cpi_info = [f"{method}", "Year", "%"]

        else:
            years = cpi_local.index.year.unique().astype(int)
            with col3:
                if president:
                    pres_years = [y for y in years if y in set(presidents[president])]
                    selected_year = st.multiselect("Year:", pres_years)
                    if not selected_year:
                        selected_year = pres_years
                else:
                    selected_year = st.multiselect("Year:", years, default=years[-1])
                    if not selected_year:
                        selected_year = [years[-1]]

        if not cpi_info:
            cpi_series, cpi_info = mf.build_yearly_table(cpi_local, selected_year, perspective_column, method)

        if chart_type == "Bar":
            fig = mc.bar_chart(cpi_series, cats, cpi_info)
        else:
            fig = mc.line_chart(cpi_series, cats, cpi_info)

        st.plotly_chart(fig)
        st.caption("Base 2018")
        st.caption("Source: DANE, Banco de la República")
