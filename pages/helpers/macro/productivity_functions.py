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
