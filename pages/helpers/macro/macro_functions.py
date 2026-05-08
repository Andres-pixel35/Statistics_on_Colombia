import pandas as pd
import streamlit as st
from pages.helpers.macro import macro_charts as mc
from generalities.presidents import presidents
from generalities.function import get_valid_presidents

def clean_gdp(df: pd.DataFrame, rows):
    gdp_local = df.copy()

    gdp_local = gdp_local.set_index("Concepto")
    gdp_local = gdp_local.apply(lambda col: col.str.replace(".", "", regex=False))

    if isinstance(rows, int):
        gdp_series = gdp_local.iloc[rows,:]
    else:
        gdp_series = gdp_local.loc[rows,:]

    gdp_series = gdp_series.T
    gdp_series = gdp_series.astype(int)

    if len(gdp_series) > 5:
        gdp_series.index = gdp_series.index.str.split("-").str[0]
        gdp_series = gdp_series.groupby(gdp_series.index).sum()

    return gdp_series

def generalities_spend_product(df: pd.DataFrame, terms: dict, variable: int|list, caption: str) -> None:
    """
    General utilities used in several parts of this section.
    filters in the sidebar and the logic to plot the chart
    """
    with st.sidebar: 
        st.header("Filters:")
        
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

        years =  df.columns[1:].str.split("-").str[0].unique()

        tmp_years = years.str.replace("p|r", "", regex=True)
        tmp_years = tmp_years.astype(int)

        valid_presidents = get_valid_presidents(tmp_years)

        president = st.selectbox("President:", valid_presidents, index=None)

        if president:
            pres_years = [y for y, ty in zip(years, tmp_years) if ty in presidents[president]]
            choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
        else:
            choice_year = st.multiselect("Year:", sorted(years, reverse=True))

        tmp = st.multiselect("Variable:", terms.values())
        if tmp:
            variable = [k for k, v in terms.items() if v in tmp]

        st.info("You may choose more than one option.")

    if choice_year:
        pattern = "|".join(choice_year)
    elif president:
        pattern = "|".join(pres_years)
    else:
        pattern = None

    if pattern:
        mask = df.columns.str.contains(pattern)
        mask[0] = True
        df = df.loc[:, mask]

    # plot the chart
    gdp_series = clean_gdp(df, variable)
    if chart_type == "Bar":
        fig = mc.total_gdp_bar(gdp_series, terms)
    else:
        fig = mc.total_gdp_line(gdp_series, terms)

    st.plotly_chart(fig)
    st.caption(f"{caption}, base year 2015")
    st.caption("Source: DANE")
    st.info("\'p\' is provisional and \'pr\' is preliminary data.")

def clean_annual_growth(df: pd.DataFrame, year: list, president: str, index: int, quarter: str|None) -> tuple:
    df.columns = df.columns.str.strip()
    df[df.columns[index]] = df[df.columns[index]].astype(float)
    df_local = df.copy()

    df_local = df_local.set_index("Fecha")  

    if quarter is not None:
        df_local = df_local[df_local.index.str.contains(f"-{quarter}$", regex=True)]

        df_local = df_local.drop(columns=["Variación Año Corrido"])

        if year:
            pattern = "|".join(map(str, year))
            df_local = df_local[df_local.index.str.contains(pattern)]

        if president:
            presidents_new = {k: [str(i) for i in v] for k, v in presidents.items()}

            pattern = "|".join(presidents_new[president])

            df_local = df_local[df_local.index.str.contains(pattern)]
    else:
        if year:
            df_local = df_local[df_local.index.isin(map(str, year))]

        if president:
            df_local.index = df_local.index.astype(int)

            df_local = df_local[df_local.index.isin(presidents[president])]

    return df, df_local


