import pandas as pd
import streamlit as st
from app_pages.helpers import charts as mc
from generalities.dictionaries import presidents
from generalities.i18n import t
from generalities.function import get_valid_presidents, president_multiselect, reshape_by_presidents, load_csv, BASE_DIR, highlight_selectbox, PREV_YEAR, show_all_years

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
        years = gdp_series.index.str.split("-").str[0]
        counts = years.value_counts()
        complete = counts[counts == counts.max()].index
        mask = years.isin(complete)
        gdp_series = gdp_series[mask]
        gdp_series.index = years[mask]
        gdp_series = gdp_series.groupby(gdp_series.index).sum()

    return gdp_series

def load_banco_annual(path) -> pd.DataFrame:
    df = load_csv(path, dtype=str)
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y").dt.year.astype(str)
    df["Crecimiento"] = df["Crecimiento"].replace("-", "0")
    return df

def _population_by_year() -> pd.Series:
    pop_raw = load_csv(POPULATION_PATH)
    pop = pop_raw.set_index("AÑO")["Total"].astype(int)
    return pop[pop.index <= PREV_YEAR + 1]  # exclude projected years beyond the current year

def gdp_per_capita_growth(path) -> pd.Series:
    """Year(int)-indexed % growth of real GDP per capita."""
    annual = load_banco_annual(path).set_index("Fecha")
    pib = annual["PIB"].astype(float)
    pib.index = pib.index.astype(int)
    per_capita = pib / _population_by_year().reindex(pib.index)
    return (per_capita.pct_change() * 100).dropna()

def year_quarter_pivot(df: pd.DataFrame, rows, year: str) -> pd.Series | pd.DataFrame:
    gdp_local = df.set_index("Concepto")
    year_cols = gdp_local.columns[gdp_local.columns.str.startswith(f"{year}-")]
    gdp_local = gdp_local[year_cols]

    if isinstance(rows, int):
        gdp_series = gdp_local.iloc[rows, :]
    else:
        gdp_series = gdp_local.loc[rows, :]

    gdp_series = gdp_series.T.astype(float)
    gdp_series.index = gdp_series.index.str.split("-").str[1]
    gdp_series.index.name = "Quarter"
    return gdp_series

def generalities_spend_product(df: pd.DataFrame, terms: dict, levels_cfg: dict, info: list) -> None:
    """
    General utilities used in several parts of this section.
    filters in the sidebar and the logic to plot the chart
    """
    variable = levels_cfg["variable"]
    banco_path = levels_cfg["banco_path"]

    in_year_view = st.session_state.get("gdp_in_year", False)

    if in_year_view:
        with st.sidebar:
            st.header(t("Filters:"))
            chart_type = st.selectbox(t("Chart Type:"), ["Line", "Bar", "Table"], format_func=t)

            dane_years = sorted(df.columns[1:].str.split("-").str[0].unique(), reverse=True)
            year = st.selectbox(t("Year:"), dane_years)

            tmp = st.multiselect(t("Variable:"), terms.values(), format_func=t)
            if tmp:
                variable = [k for k, v in terms.items() if v in tmp]

            per_capita = st.checkbox(t("GDP per Capita"))

            st.checkbox(t("In Year view"), key="gdp_in_year")

        gdp_series = year_quarter_pivot(df, variable, year) / 1000

        if per_capita:
            pop = _population_by_year()
            year_num = int("".join(c for c in year if c.isdigit()))
            pop_value = pop.get(year_num)
            if pop_value:
                original_name = gdp_series.name if isinstance(gdp_series, pd.Series) else None
                gdp_series = gdp_series / pop_value * 1_000_000_000_000
                if original_name is not None:
                    gdp_series.name = original_name
                info[2] = "COP per capita"
            else:
                st.info(t("No population data for {year} yet — showing absolute values.").format(year=year))

        year_info = [f"{t(info[0])} · {year}", "Quarter", info[2], info[3]]
        labels_arg = terms
        highlight = highlight_selectbox(gdp_series, [terms.get(c, c) for c in gdp_series.columns] if isinstance(gdp_series, pd.DataFrame) else None)
        fig = mc.line_or_bar(chart_type, gdp_series, year_info, labels=labels_arg, highlight=highlight)
        mc.render_chart(fig)
        st.caption(f"{t(info[3])}{t(', base year 2015')}")
        st.caption(t("Source: DANE"))
        st.info(t("'p' is provisional and 'pr' is preliminary data."))
        return

    with st.sidebar:
        st.header(t("Filters:"))

        chart_type = st.selectbox(t("Chart Type:"), ["Line", "Bar", "Table"], format_func=t)

        quarter = st.selectbox(t("Quarter:"), ["All", "I", "II", "III", "IV"], format_func=t)

        tmp = st.multiselect(t("Variable:"), terms.values(), format_func=t)
        if tmp:
            variable = [k for k, v in terms.items() if v in tmp]

        use_banco = banco_path is not None and quarter == "All" and not tmp

        if use_banco:
            years = pd.Index(sorted(load_banco_annual(banco_path)["Fecha"].unique()))
        else:
            all_years = df.columns[1:].str.split("-").str[0]
            if quarter == "All":
                counts = all_years.value_counts()
                years = counts[counts == counts.max()].index
            else:
                cols = df.columns[1:]
                qcols = cols[cols.str.contains(rf"-{quarter}$", regex=True)]
                years = qcols.str.split("-").str[0].unique()

        tmp_years = pd.Index(years).str.replace("p|r", "", regex=True).astype(int)

        valid_presidents = get_valid_presidents(tmp_years)

        selected_presidents = president_multiselect(valid_presidents)
        comparing = len(selected_presidents) >= 2
        president = selected_presidents[0] if len(selected_presidents) == 1 else None

        if comparing:
            choice_year = []
        elif president:
            pres_years = [y for y, ty in zip(years, tmp_years) if ty in presidents[president]]
            choice_year = st.multiselect(t("Year:"), sorted(pres_years, reverse=True))
        else:
            choice_year = st.multiselect(t("Year:"), sorted(years, reverse=True))

        per_capita = st.checkbox(t("GDP per Capita"))

        st.checkbox(t("In Year view"), key="gdp_in_year")

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
        info[0] = f"{t(info[0])} — Q{quarter}"

    # plot the chart
    if use_banco:
        banco = load_banco_annual(banco_path)
        gdp_series = banco.set_index("Fecha")["PIB"].astype(float) / 1000
        gdp_series.name = "Producto Interno Bruto"
        if not comparing:
            gdp_series.index = gdp_series.index.astype(int)
            gdp_series = show_all_years(gdp_series, president)
            gdp_series.index = gdp_series.index.astype(str)
        if pattern:
            gdp_series = gdp_series[gdp_series.index.str.contains(pattern)]
    else:
        gdp_series = clean_gdp(df, variable) / 1000

    if per_capita:
        pop = _population_by_year()
        clean_years = gdp_series.index.str.replace(r'\D+', '', regex=True).astype(int)
        pop_aligned = pd.Series(pop.reindex(clean_years).values, index=gdp_series.index)
        original_name = gdp_series.name if isinstance(gdp_series, pd.Series) else None
        gdp_series = gdp_series.div(pop_aligned, axis=0) * 1_000_000_000_000
        gdp_series = gdp_series.dropna()
        if original_name is not None:
            gdp_series.name = original_name
        info[2] = "COP per capita"

    force_bar = use_banco and len(gdp_series) == 1

    if comparing:
        if isinstance(gdp_series, pd.Series):
            gdp_series = gdp_series.to_frame()
        gdp_series, info = reshape_by_presidents(gdp_series, selected_presidents, info, col_labels=terms)
        labels_arg = {}
    else:
        labels_arg = terms

    highlight = highlight_selectbox(gdp_series, [terms.get(c, c) for c in gdp_series.columns] if isinstance(gdp_series, pd.DataFrame) else None)

    fig = mc.line_or_bar(chart_type, gdp_series, info, labels=labels_arg, highlight=highlight, force_bar=force_bar)

    mc.render_chart(fig)
    st.caption(f"{t(info[3])}{t(', base year 2015')}")
    st.caption(t("Source: DANE"))
    st.info(t("'p' is provisional and 'pr' is preliminary data."))

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
