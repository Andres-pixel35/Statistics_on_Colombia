import pandas as pd


def domain_pivot(df: pd.DataFrame, domains: list, year_set=None) -> pd.DataFrame:
    """Year x domain. Shape-A CSVs are already wide, so this is a select + filter."""
    out = df.set_index("Fecha")[list(domains)]
    if year_set:
        out = out[out.index.isin(year_set)]
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out.sort_index()


def map_data(df: pd.DataFrame, year, city_dpto: dict) -> pd.DataFrame:
    """One row per capital city: DANE dept code + that year's value. Cities with no value
    for the year are kept with NaN so the choropleth greys them."""
    row = df[df["Fecha"] == year].iloc[0]
    return pd.DataFrame({"Code": list(city_dpto.values()),
                         "Name": list(city_dpto),
                         "value": [row.get(city) for city in city_dpto]})


def profile_pivot(df: pd.DataFrame, grupo: str, domain: str, years: list) -> pd.DataFrame:
    """Categoria x Year for one Grupo and one domain column."""
    d = df[(df["Grupo"] == grupo) & (df["Fecha"].isin(years))]
    out = d.pivot(index="Categoria", columns="Fecha", values=domain)
    out.columns = [str(c) for c in out.columns]
    out.index.name = "Category"
    return out.reindex(d["Categoria"].unique())   # keep DANE's meaningful row order


def sexo_pivot(df: pd.DataFrame, domains: list, year, sexo_en: dict) -> pd.DataFrame:
    """Domain x Sexo for one year."""
    d = df[df["Fecha"] == year].set_index("Sexo")[list(domains)]
    return d.T.rename(columns=sexo_en).rename_axis("Domain")
