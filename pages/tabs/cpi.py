import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import macro_functions as mf
from generalities.dictionaries import presidents
from generalities.function import find_key_by_value
import generalities.inflation as gi

cpi_15_path = "./data/banco_republica/CPI/inflacion_15.csv" 

def render_cpi(cpi_df: pd.DataFrame) -> None:
    cpi_local = cpi_df.copy()
    cpi_local["Fecha"] = pd.to_datetime(cpi_local["Fecha"])
    cpi_local = cpi_local.set_index("Fecha").sort_index()

    st.title("CPI")

    col1, col2, col3 = st.columns(3)

    cpi_info = "" 
    cats = gi.perspective_names

    with col1:
        method = st.selectbox("Method:", ["Headline Inflation", "Core Inflation (excluding 15 items)"])

    if method == "Headline Inflation":
        all_years = cpi_local.index.year.unique().astype(int)
        president, chart_type = mf.cpi_sidebar_filters(all_years)
 
        with col2:
            perspective = st.selectbox("Perspective:", cats.values())

        perspective_column = find_key_by_value(cats, perspective)

        if perspective == "Annual":
            with col3:
                cpi_series, cpi_info = mf.build_cpi_series(cpi_local, perspective_column, president, method)
        else:
            years = cpi_local.index.year.unique().astype(int)
            with col3:
                if president:
                    pres_years = [y for y in years if y in set(presidents[president])]
                    selected_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
                    if not selected_year:
                        selected_year = pres_years
                else:
                    selected_year = st.multiselect("Year:", sorted(years, reverse=True), default=years[-1])
                    if not selected_year:
                        selected_year = [years[-1]]

        if not cpi_info:
            cpi_series, cpi_info = mf.build_yearly_table(cpi_local, selected_year, perspective_column, method)  
    else:
        cpi_15 = pd.read_csv(cpi_15_path, encoding="utf-8")
        cpi_15["Fecha"] = pd.to_datetime(cpi_15["Fecha"], dayfirst=True)
        cpi_15 = cpi_15.set_index("Fecha")

        all_years = cpi_15.index.year.unique().astype(int)
        president, chart_type = mf.cpi_sidebar_filters(all_years)

        with col2:
            cpi_series, cpi_info = mf.build_cpi_series(cpi_15, "Inflación", president, method)

    highlight = None
    if len(cpi_series.columns) > 1:
        display_names = [str(col) for col in cpi_series.columns]
        with st.sidebar:
            highlight_choice = st.selectbox("Highlight variable:", ["—"] + display_names)
            highlight = None if highlight_choice == "—" else highlight_choice

    if chart_type == "Bar" or len(cpi_series) == 1:
        fig = mc.bar_chart(cpi_series, cats, cpi_info, highlight=highlight)
    else:
        fig = mc.line_chart(cpi_series, cats, cpi_info, highlight=highlight)

    st.plotly_chart(fig)
    st.caption("Base 2018")
    st.caption("Source: DANE, Banco de la República")
