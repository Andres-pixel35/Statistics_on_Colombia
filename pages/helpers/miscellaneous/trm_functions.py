import pandas as pd
from generalities.macro_generalities.dictionaries import months


def trm_year_axis(df: pd.DataFrame, month_nums: list) -> pd.DataFrame:
    """x = years. Empty month_nums -> annual-average single column; else one column per month."""
    s = df["trm"].dropna()
    if not month_nums:
        return s.groupby(s.index.year).mean().to_frame(name="TRM")

    cols = {}
    for m in month_nums:
        sm = s[s.index.month == m]
        cols[months[m]] = sm.groupby(sm.index.year).mean()
    return pd.DataFrame(cols)


def trm_month_axis(df: pd.DataFrame, years: list) -> pd.DataFrame:
    """x = months (Jan-Dec). One column per year, values = that year's monthly average."""
    s = df["trm"].dropna()
    cols = {}
    for y in years:
        sy = s[s.index.year == y]
        cols[str(y)] = sy.groupby(sy.index.month).mean().reindex(range(1, 13))
    table = pd.DataFrame(cols)
    table.index = [months[m] for m in table.index]
    return table


def trm_day_axis(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """x = day of month. One column, TRM value each day of the chosen year/month."""
    s = df["trm"].dropna()
    sm = s[(s.index.year == year) & (s.index.month == month)]
    sm.index = sm.index.day
    return sm.sort_index().to_frame(name="TRM")


def trm_day_compare(df: pd.DataFrame, day: int, month: int) -> pd.DataFrame:
    """x = years. One column, TRM value on the chosen day/month across all years."""
    s = df["trm"].dropna()
    sm = s[(s.index.month == month) & (s.index.day == day)]
    sm.index = sm.index.year
    return sm.sort_index().to_frame(name="TRM")
