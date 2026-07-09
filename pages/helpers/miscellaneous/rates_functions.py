from typing import NamedTuple
import pandas as pd
from generalities.macro_generalities.dictionaries import months


class SeriesSpec(NamedTuple):
    value_col: str  # e.g. "trm" or "Tasa (%)"
    label: str       # e.g. "Exchange Rate" or "Monetary Policy Rate"


def rate_year_axis(df: pd.DataFrame, spec: SeriesSpec, month_nums: list) -> pd.DataFrame:
    """x = years. Empty month_nums -> annual-average single column; else one column per month."""
    s = df[spec.value_col].dropna()
    if not month_nums:
        return s.groupby(s.index.year).mean().to_frame(name=spec.label)

    cols = {}
    for m in month_nums:
        sm = s[s.index.month == m]
        cols[months[m]] = sm.groupby(sm.index.year).mean()
    return pd.DataFrame(cols)


def rate_month_axis(df: pd.DataFrame, spec: SeriesSpec, years: list) -> pd.DataFrame:
    """x = months (Jan-Dec). One column per year, values = that year's monthly average."""
    s = df[spec.value_col].dropna()
    cols = {}
    for y in years:
        sy = s[s.index.year == y]
        cols[str(y)] = sy.groupby(sy.index.month).mean().reindex(range(1, 13))
    table = pd.DataFrame(cols)
    table.index = [months[m] for m in table.index]
    return table


def rate_day_axis(df: pd.DataFrame, spec: SeriesSpec, year: int, month: int) -> pd.DataFrame:
    """x = day of month. One column, value each day of the chosen year/month."""
    s = df[spec.value_col].dropna()
    sm = s[(s.index.year == year) & (s.index.month == month)]
    sm.index = sm.index.day
    return sm.sort_index().to_frame(name=spec.label)


def rate_day_compare(df: pd.DataFrame, spec: SeriesSpec, day: int, month: int) -> pd.DataFrame:
    """x = years. One column, value on the chosen day/month across all years."""
    s = df[spec.value_col].dropna()
    sm = s[(s.index.month == month) & (s.index.day == day)]
    sm.index = sm.index.year
    return sm.sort_index().to_frame(name=spec.label)


def forward_fill_through(df: pd.DataFrame, end: pd.Timestamp) -> pd.DataFrame:
    """Extend a date-indexed df through `end`, forward-filling its values, so a hand-refreshed
    CSV that lags behind still has a data point up to that date."""
    full_index = pd.date_range(df.index.min(), max(df.index.max(), end), freq="D")
    full_index.name = df.index.name
    return df.reindex(full_index).ffill()
