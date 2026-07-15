import pandas as pd
from generalities.function import SeriesSpec

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
