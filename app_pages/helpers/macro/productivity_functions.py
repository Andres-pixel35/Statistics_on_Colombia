import pandas as pd


def productivity_pivot(df: pd.DataFrame, concept_cols: dict, year_set: set | None = None) -> pd.DataFrame:
    """Year x concept. concept_cols: {English label: Spanish column name}. Direct column
    select+rename since the source CSV is already wide (one row per year)."""
    out = df.set_index("año")[list(concept_cols.values())]
    out.columns = list(concept_cols.keys())
    if year_set:
        out = out[out.index.isin(year_set)]
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out.sort_index()


def productivity_activity_pivot(df: pd.DataFrame, activities: list, concept_cols: dict,
                                 year_set: set | None = None, *,
                                 activity_col: str = "Actividad Económica") -> pd.DataFrame:
    """>=2 activities -> Year x Activity for the first concept in concept_cols. 1 activity ->
    Year x Concept, scoped to that activity (mirrors productivity_pivot)."""
    d = df[df[activity_col].isin(activities)]
    if year_set:
        d = d[d["año"].isin(year_set)]
    if len(activities) >= 2:
        concept_sp = list(concept_cols.values())[0]
        out = d.pivot_table(index="año", columns=activity_col, values=concept_sp)
    else:
        out = d.set_index("año")[list(concept_cols.values())]
        out.columns = list(concept_cols.keys())
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out.sort_index()
