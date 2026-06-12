import pandas as pd
import streamlit as st
from pages.helpers.macro import macro_charts as mc
from generalities.macro_generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, president_multiselect, reshape_by_presidents, load_csv, BASE_DIR, highlight_selectbox
from generalities.macro_generalities.population import PREV_YEAR

POPULATION_PATH = BASE_DIR / "data/dane/population/nacional.csv"


def clean_gdp(df: pd.DataFrame, rows):
    gdp_local = df.copy()

    gdp_local = gdp_local.set_index("Concepto")

    if isinstance(rows, int):
        gdp_series = gdp_local.iloc[rows,:]
    else:
        gdp_series = gdp_local.loc[rows,:]

    gdp_series = gdp_series.T
    gdp_series = gdp_series.astype(float)

    if len(gdp_series) > 5:
        gdp_series.index = gdp_series.index.str.split("-").str[0]
        gdp_series = gdp_series.groupby(gdp_series.index).sum()

    return gdp_series

def generalities_spend_product(df: pd.DataFrame, terms: dict, variable: int|list, info: list) -> None:
    """
    General utilities used in several parts of this section.
    filters in the sidebar and the logic to plot the chart
    """
    with st.sidebar:
        st.header("Filters:")

        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

        quarter = st.selectbox("Quarter:", ["All", "I", "II", "III", "IV"])

        years = df.columns[1:].str.split("-").str[0].unique()

        tmp_years = years.str.replace("p|r", "", regex=True)
        tmp_years = tmp_years.astype(int)

        valid_presidents = get_valid_presidents(tmp_years)

        selected_presidents = president_multiselect(valid_presidents)
        comparing = len(selected_presidents) >= 2
        president = selected_presidents[0] if len(selected_presidents) == 1 else None

        if comparing:
            choice_year = []
        elif president:
            pres_years = [y for y, ty in zip(years, tmp_years) if ty in presidents[president]]
            choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
        else:
            choice_year = st.multiselect("Year:", sorted(years, reverse=True))

        tmp = st.multiselect("Variable:", terms.values())
        if tmp:
            variable = [k for k, v in terms.items() if v in tmp]

        per_capita = st.checkbox("GDP per Capita")

    if comparing:
        pattern = None
    elif choice_year:
        pattern = "|".join(choice_year)
    elif president:
        pattern = "|".join(pres_years)
    else:
        pattern = None

    if pattern:
        mask = df.columns.str.contains(pattern)
        mask[0] = True
        df = df.loc[:, mask]

    if quarter != "All":
        qmask = df.columns.str.contains(rf"-{quarter}$", regex=True)
        qmask = qmask | (df.columns == "Concepto")
        df = df.loc[:, qmask]
        info[0] = f"{info[0]} — Q{quarter}"

    # plot the chart
    gdp_series = clean_gdp(df, variable)

    if per_capita:
        pop_raw = load_csv(POPULATION_PATH)
        pop = pop_raw.set_index("AÑO")["Total"].astype(int)
        pop = pop[pop.index <= PREV_YEAR]            # exclude projected years
        clean_years = gdp_series.index.str.replace(r'\D+', '', regex=True).astype(int)
        pop_aligned = pd.Series(pop.reindex(clean_years).values, index=gdp_series.index)
        original_name = gdp_series.name if isinstance(gdp_series, pd.Series) else None
        gdp_series = gdp_series.div(pop_aligned, axis=0) * 1_000_000_000_000
        gdp_series = gdp_series.dropna()
        if original_name is not None:
            gdp_series.name = original_name
        info[2] = "COP per capita"

    if comparing:
        if isinstance(gdp_series, pd.Series):
            gdp_series = gdp_series.to_frame()
        gdp_series, info = reshape_by_presidents(gdp_series, selected_presidents, info, col_labels=terms)
        labels_arg = {}
    else:
        labels_arg = terms

    highlight = highlight_selectbox(gdp_series, [terms.get(c, c) for c in gdp_series.columns] if isinstance(gdp_series, pd.DataFrame) else None)

    fig = mc.line_or_bar(chart_type, gdp_series, info, labels=labels_arg, highlight=highlight)

    mc.render_chart(fig)
    st.caption(f"{info[3]}, base year 2015")
    st.caption("Source: DANE")
    st.info("\'p\' is provisional and \'pr\' is preliminary data.")

def clean_annual_growth(df: pd.DataFrame, year: list, president: str, index: int, quarter: str|None) -> tuple:
    df.columns = df.columns.str.strip()
    df[df.columns[index]] = df[df.columns[index]].astype(float)
    df_local = df.copy()

    df_local = df_local.set_index("Fecha")

    if quarter is not None:
        df_local = df_local[df_local.index.str.contains(f"-{quarter}$", regex=True)]

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

def _variable_levels(df: pd.DataFrame, concepto: str) -> pd.Series:
    df = df.copy()
    df.columns = df.columns.str.strip()

    row = df[df["Concepto"] == concepto]
    return row.drop(columns="Concepto").iloc[0].astype(float)

def quarter_over_quarter(df: pd.DataFrame, concepto: str = "Producto Interno Bruto") -> pd.DataFrame:
    series = _variable_levels(df, concepto)

    growth = (series.pct_change() * 100).dropna()
    growth = growth.to_frame(name="Growth")
    growth.index.name = "Quarter"

    return growth

def variable_growth(df: pd.DataFrame, concepto: str, mode: str) -> pd.DataFrame:
    series = _variable_levels(df, concepto)

    if mode == "annual":
        years = series.index.str.replace(r"\D+", "", regex=True)
        full = series.groupby(years).size() == 4
        annual = series.groupby(years).sum()[full].sort_index()
        growth = (annual.pct_change() * 100).dropna()
    else:
        labels = [f"{q.split('-')[0].rstrip('pr')}-{q.split('-')[1]}" for q in series.index]
        series.index = labels
        growth = (series.pct_change(4) * 100).dropna()

    growth = growth.rename("Growth").rename_axis("Fecha").reset_index()
    return growth
