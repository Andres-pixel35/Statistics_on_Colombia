import pandas as pd
from pages.helpers.macro.gdp_functions import load_banco_annual


def gdp_millions(nominal_annual_path) -> pd.Series:
    """Year-indexed (string year) nominal GDP in COP millions, from the Banco de la República annual CSV."""
    return load_banco_annual(nominal_annual_path).set_index("Fecha")["PIB"].astype(float) * 1000


def gdp_pct_labels(data, year: int | None = None) -> list[str]:
    """Year labels `data` would be divided by in to_gdp_pct (its index, columns, or the single `year`)."""
    if year is not None:
        return [str(year)]
    if data.index.inferred_type == "integer":
        return [str(y) for y in data.index]
    return list(data.columns)


def missing_gdp_years(data, gdp_millions: pd.Series, year: int | None = None) -> list[str]:
    """Year labels used by `data` that have no published nominal GDP yet."""
    return [y for y in gdp_pct_labels(data, year) if y not in gdp_millions.index]


def to_gdp_pct(data, gdp_millions: pd.Series, year: int | None = None):
    """Convert COP-millions data to % of nominal GDP. `year` is passed only when the
    frame has already lost its year axis (compare mode with a single selected year)."""
    if year is not None:
        return data / gdp_millions.loc[str(year)] * 100
    if data.index.inferred_type == "integer":  # index = years
        divisor = gdp_millions.reindex(data.index.astype(str))
        divisor.index = data.index
        return data.div(divisor, axis=0) * 100
    return data.div(gdp_millions.reindex(data.columns), axis=1) * 100  # columns = years


def to_total_pct(data, total):
    """Convert COP-millions data to % of Total Debt. `total` is either a Series aligned
    to `data`'s index (row-wise divide) or a DataFrame with matching columns (direct divide)."""
    if isinstance(total, pd.Series):
        return data.div(total, axis=0) * 100
    return data.div(total) * 100
