import pandas as pd
from generalities.function import load_csv, norm
import generalities.macro_generalities.deficit as df_g


def _keys(concepto: pd.Series, grupo: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Canonical concept keys + their immediate-parent keys. `Concepto` alone is not unique
    (the annual file has three 'Resto' rows), so repeated names are parent-qualified."""
    concept_key = concepto.str.rstrip("*").map(norm).replace(df_g.CONCEPT_ALIASES)
    parent_key = grupo.fillna("").str.rstrip("*").map(
        lambda g: norm(g.split(" > ")[-1]) if g else ""
    )
    dup = concept_key.duplicated(keep=False)
    key = concept_key.where(~dup, parent_key + " > " + concept_key)
    return key, parent_key


def load_deficit(path, *, dated: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Concepto-rows x date-columns -> (values, meta).

    values: index = int years (dated=False) or a DatetimeIndex (dated=True),
            one float column per canonical concept key, CSV row order preserved.
    meta:   index = concept key, columns = ['root', 'depth'] — 'root' is the row's
            top-level ancestor key (its own key when depth == 0), 'depth' is the number
            of ' > ' segments in Grupo. Drives the Group -> Concepts cascade.
    """
    raw = load_csv(path)
    key, _ = _keys(raw["Concepto"], raw["Grupo"])
    grupo = raw["Grupo"].fillna("")
    depth = grupo.map(lambda g: len(g.split(" > ")) if g else 0)
    root = pd.Series(
        [norm(g.split(" > ")[0]) if g else k for g, k in zip(grupo, key)], index=raw.index
    )

    assert key.is_unique, f"{path}: duplicate concept key after parent-qualification"

    meta = pd.DataFrame({"root": root, "depth": depth}).set_axis(key)

    values = raw.drop(columns=["Concepto", "Grupo"]).set_axis(key).T.astype(float)
    if dated:
        values.index = pd.to_datetime(values.index)
    else:
        values.index = values.index.astype(int)
        values.index.name = "Year"
    values = values.sort_index()

    return values, meta


def _quarter_index(values: pd.DataFrame) -> pd.Index:
    return (values.index.month - 1) // 3 + 1


def quarter_year_axis(values: pd.DataFrame, key: str, quarter: int) -> pd.DataFrame:
    """x = years, for one fixed quarter. Single column named after the concept key."""
    s = values[key][_quarter_index(values) == quarter]
    out = s.groupby(s.index.year).first().to_frame(name=key)
    out.index.name = "Year"
    return out


def quarter_axis(values: pd.DataFrame, key: str, years: list) -> pd.DataFrame:
    """x = Q1..Q4. One column per year, for one fixed concept."""
    s = values[key]
    quarter = _quarter_index(values)
    cols = {str(y): s[s.index.year == y].set_axis(quarter[s.index.year == y]) for y in years}
    table = pd.DataFrame(cols)
    table.index = [f"Q{q}" for q in table.index]
    table.index.name = "Quarter"
    return table


def quarter_concept_axis(values: pd.DataFrame, keys: list, year: int) -> pd.DataFrame:
    """x = Q1..Q4. One column per concept, for one fixed year (concept comparison)."""
    year_values = values[values.index.year == year]
    quarter = _quarter_index(year_values)
    table = year_values[keys].set_axis(quarter)
    table.index = [f"Q{q}" for q in table.index]
    table.index.name = "Quarter"
    return table
