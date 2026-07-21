import pandas as pd
from generalities.dictionaries import months


def ise_long(df: pd.DataFrame) -> pd.DataFrame:
    """Wide (Fecha=year, Concepto, Rama, Enero..Diciembre) -> long (Fecha, Concepto, Rama, Mes, Valor).
    Mes is derived from each month column's position (Enero=1..Diciembre=12), not its name."""
    month_cols = list(df.columns[3:])
    long = df.melt(id_vars=["Fecha", "Concepto", "Rama"], value_vars=month_cols,
                   var_name="MesNombre", value_name="Valor").dropna(subset=["Valor"])
    mes_num = {name: i + 1 for i, name in enumerate(month_cols)}
    long["Mes"] = long["MesNombre"].map(mes_num)
    return long.drop(columns="MesNombre")


def ise_year_axis(long_df: pd.DataFrame, category_sp: str, activities_sp: list, month: int) -> pd.DataFrame:
    """x = years, for one fixed month. One column per activity (Rama)."""
    d = long_df[(long_df["Concepto"] == category_sp) & (long_df["Rama"].isin(activities_sp))
                & (long_df["Mes"] == month)]
    table = d.pivot_table(index="Fecha", columns="Rama", values="Valor").sort_index()
    table.index.name = "Year"
    return table


def ise_month_axis(long_df: pd.DataFrame, category_sp: str, activity_sp: str, years: list) -> pd.DataFrame:
    """x = months (Jan-Dec). One column per year, for one fixed activity."""
    d = long_df[(long_df["Concepto"] == category_sp) & (long_df["Rama"] == activity_sp)]
    cols = {}
    for y in years:
        cols[str(y)] = d[d["Fecha"] == y].set_index("Mes")["Valor"]
    table = pd.DataFrame(cols).reindex(range(1, 13))
    table.index = [months[m] for m in table.index]
    table.index.name = "Month"
    return table


def ise_activity_month_axis(long_df: pd.DataFrame, category_sp: str, activities_sp: list, year: int) -> pd.DataFrame:
    """x = months (Jan-Dec). One column per activity (Rama), for one fixed year (activity comparison)."""
    d = long_df[(long_df["Concepto"] == category_sp) & (long_df["Rama"].isin(activities_sp))
                & (long_df["Fecha"] == year)]
    table = d.pivot_table(index="Mes", columns="Rama", values="Valor").reindex(range(1, 13))
    table.index = [months[m] for m in table.index]
    table.index.name = "Month"
    return table


def ise_category_year_axis(long_df: pd.DataFrame, categories: list, month: int) -> pd.DataFrame:
    """x = years, for one fixed month. One column per (category, its own total Rama) pair (category comparison)."""
    cols = {}
    for category_sp, rama_sp in categories:
        d = long_df[(long_df["Concepto"] == category_sp) & (long_df["Rama"] == rama_sp)
                    & (long_df["Mes"] == month)]
        cols[category_sp] = d.set_index("Fecha")["Valor"]
    table = pd.DataFrame(cols).sort_index()
    table.index.name = "Year"
    return table


def ise_category_month_axis(long_df: pd.DataFrame, categories: list, year: int) -> pd.DataFrame:
    """x = months (Jan-Dec). One column per (category, its own total Rama) pair, for one fixed year."""
    cols = {}
    for category_sp, rama_sp in categories:
        d = long_df[(long_df["Concepto"] == category_sp) & (long_df["Rama"] == rama_sp)
                    & (long_df["Fecha"] == year)]
        cols[category_sp] = d.set_index("Mes")["Valor"]
    table = pd.DataFrame(cols).reindex(range(1, 13))
    table.index = [months[m] for m in table.index]
    table.index.name = "Month"
    return table
