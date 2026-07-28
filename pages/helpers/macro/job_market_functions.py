import pandas as pd
import streamlit as st
from generalities.function import get_valid_presidents, president_multiselect, norm, SeriesSpec, load_csv
import generalities.macro_generalities.job_market as jm

UNEMPLOYMENT_SPEC = SeriesSpec("Tasa de desempleo", "Unemployment rate")
MONTH_ABBR_ES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
                 "Jul": 7, "Ago": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12}


def load_desestacionalizado_unemployment(path: str) -> pd.DataFrame:
    """Seasonally-adjusted unemployment rate (DANE), reshaped to match UNEMPLOYMENT_SPEC's
    date-indexed shape so it's a drop-in for series_year_axis/series_month_axis."""
    df = load_csv(path)
    df = df[df["Concepto"] == "Tasa de Desocupación (TD)"].copy()
    df["Fecha"] = pd.to_datetime(dict(
        year=df["Fecha"], month=df["Periodo"].map(MONTH_ABBR_ES), day=1))
    return (df.set_index("Fecha").sort_index()
            .rename(columns={"Valor": UNEMPLOYMENT_SPEC.value_col}))


def job_market_sidebar_filters(df: pd.DataFrame, placeholder, president_placeholder,
                               president_disabled: bool = False, president_key=None) -> tuple:
    """Render Chart Type + president multiselect for a year-indexed frame; returns (presidents, chart_type)."""
    years = df.index.unique().astype(int)

    with placeholder.container():
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

    valid_presidents = get_valid_presidents(years)
    with president_placeholder.container():
        selected_presidents = president_multiselect(
            valid_presidents, disabled=president_disabled, key=president_key
        )

    return selected_presidents, chart_type


def _to_percent(table: pd.DataFrame, pet_concept: str, rate_concepts: dict) -> pd.DataFrame:
    """Per-concept %: reuse the CSV rate column if present, else value / PET * 100."""
    pet = table[pet_concept]
    out = {}
    for concept, rate in rate_concepts.items():
        if rate and rate in table.columns:
            out[concept] = table[rate]
        elif concept in table.columns:
            out[concept] = table[concept] / pet * 100
    return pd.DataFrame(out)


def labor_force_pivot(df: pd.DataFrame, gender_sp: str, period_sp, concepts_sp: list,
                      *, percent: bool = False) -> pd.DataFrame:
    """Year x Concepto pivot (people, values x1000). period_sp None -> mean across the 12 windows.
    percent -> per-concept shares (no x1000) via _to_percent."""
    d = df[df["Perspectiva"] == gender_sp].replace({"Concepto": jm.CONCEPT_ALIASES})
    if period_sp is not None:
        d = d[d["Periodo"] == period_sp]

    table = d.pivot_table(index="Fecha", columns="Concepto", values="Valor", aggfunc="mean")
    if percent:
        return _to_percent(table, jm.PET_CONCEPT, jm.RATE_CONCEPTS).reindex(columns=concepts_sp).dropna(how="all")
    return (table.reindex(columns=concepts_sp) * 1000).dropna(how="all")


def labor_force_period_axis(df: pd.DataFrame, gender_sp: str, years: list, concepts_sp: list,
                            *, percent: bool = False) -> pd.DataFrame:
    """x = rolling 3-month windows. >=2 concepts -> single year, one col per concept;
    else one col per year for the single concept. Columns: Spanish concept (concept-priority)
    or str(year) (year-priority). percent -> per-concept shares (no x1000) via _to_percent."""
    d = df[df["Perspectiva"] == gender_sp].replace({"Concepto": jm.CONCEPT_ALIASES})
    scale = 1000
    if percent:
        wide = d.pivot_table(index=["Fecha", "Periodo"], columns="Concepto", values="Valor", aggfunc="mean")
        d = _to_percent(wide, jm.PET_CONCEPT, jm.RATE_CONCEPTS).rename_axis(columns="Concepto").stack().rename("Valor").reset_index()
        scale = 1
    cols = {}
    if len(concepts_sp) >= 2:                      # concept priority -> lock to 1 year
        dy = d[d["Fecha"] == years[0]]
        for c in concepts_sp:
            cols[c] = dy[dy["Concepto"] == c].set_index("Periodo")["Valor"]
    else:
        dc = d[d["Concepto"] == concepts_sp[0]]
        for y in years:
            cols[str(y)] = dc[dc["Fecha"] == y].set_index("Periodo")["Valor"]
    table = pd.DataFrame(cols).reindex(list(jm.PERIOD_EN)) * scale
    table.index = [jm.PERIOD_EN[p] for p in table.index]
    return table


def dept_code_lookup(geojson: dict) -> dict:
    """{norm(department name): DANE 2-digit code} from the choropleth geojson."""
    return {norm(f["properties"]["NOMBRE_DPT"]): f["properties"]["DPTO"]
            for f in geojson["features"]}


def dept_jm_map_data(df: pd.DataFrame, concept_sp: str, geojson: dict,
                     *, denom_sp: str) -> pd.DataFrame:
    """Per-department percentage of `concept_sp` (mean across `df`'s years), keyed to DANE code.
    Total table reuses the matching rate row when present, else value / denom * 100;
    branch table is branch / denom (`Total ocupados`) * 100. Returns one row per geojson
    department (Code, Name, value) — departments without data carry value NaN (grey)."""
    rate = jm.RATE_CONCEPTS.get(concept_sp)
    if rate and rate in df["Concepto"].values:                      # ready-made rate row
        pct = df[df["Concepto"] == rate].set_index(["Fecha", "Departamentos"])["Valor"]
    else:                                                           # compute share vs denom
        num = df[df["Concepto"] == concept_sp].set_index(["Fecha", "Departamentos"])["Valor"]
        den = df[df["Concepto"] == denom_sp].set_index(["Fecha", "Departamentos"])["Valor"]
        pct = num / den * 100
    code_by_norm = dept_code_lookup(geojson)
    grouped = pct.groupby("Departamentos").mean().reset_index(name="value")
    grouped["Code"] = grouped["Departamentos"].map(lambda n: code_by_norm.get(norm(n)))

    full = pd.DataFrame([(f["properties"]["DPTO"], f["properties"]["NOMBRE_DPT"].title())
                         for f in geojson["features"]], columns=["Code", "Name"])
    out = full.merge(grouped[["Code", "value", "Departamentos"]], on="Code", how="left")
    out["Name"] = out["Departamentos"].fillna(out["Name"])          # prefer the data's spelling
    return out[["Code", "Name", "value"]]


def dept_jm_pivot(df: pd.DataFrame, concepts_sp: list, denom_sp: str,
                  *, percent: bool = False) -> pd.DataFrame:
    """Year x Concepto pivot for the departments in `df` (summed). percent -> per-concept
    share concept / denom * 100; else people counts x1000. Caller pre-filters depts/years."""
    table = df.pivot_table(index="Fecha", columns="Concepto", values="Valor", aggfunc="sum")
    if percent:
        out = {}
        for c in concepts_sp:                       # reuse the CSV rate row when present
            rate = jm.RATE_CONCEPTS.get(c)
            if rate and rate in table.columns:
                out[c] = table[rate]
            elif c in table.columns:
                out[c] = table[c] / table[denom_sp] * 100
        pivot = pd.DataFrame(out)
    else:
        pivot = table.reindex(columns=concepts_sp) * 1000
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot.dropna(how="all")


def dept_jm_dept_pivot(df: pd.DataFrame, concept_sp: str, denom_sp: str,
                       *, percent: bool = False) -> pd.DataFrame:
    """Year x Department pivot of one concept. percent -> per-department concept / denom * 100;
    else people counts x1000. Caller pre-filters depts/years."""
    rate = jm.RATE_CONCEPTS.get(concept_sp)
    if percent and rate and rate in df["Concepto"].values:   # reuse the CSV rate row
        pivot = df[df["Concepto"] == rate].pivot_table(
            index="Fecha", columns="Departamentos", values="Valor", aggfunc="mean")
    else:
        num = df[df["Concepto"] == concept_sp].pivot_table(
            index="Fecha", columns="Departamentos", values="Valor", aggfunc="mean")
        if percent:
            den = df[df["Concepto"] == denom_sp].pivot_table(
                index="Fecha", columns="Departamentos", values="Valor", aggfunc="mean")
            pivot = num / den * 100
        else:
            pivot = num * 1000
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot.dropna(how="all")


def labor_force_gender_pivot(df: pd.DataFrame, period_sp, concept_sp: str,
                             *, percent: bool = False) -> pd.DataFrame:
    """Men vs Women for one concept, x = years (period_sp filter). Columns Men/Women."""
    cols = {}
    for label, gsp in (("Men", jm.GENDER["Men"]), ("Women", jm.GENDER["Women"])):
        cols[label] = labor_force_pivot(df, gsp, period_sp, [concept_sp], percent=percent).iloc[:, 0]
    return pd.DataFrame(cols)


def labor_force_gender_period_axis(df: pd.DataFrame, year: int, concept_sp: str,
                                   *, percent: bool = False) -> pd.DataFrame:
    """Men vs Women for one concept and one year, x = rolling 3-month windows. Columns Men/Women."""
    cols = {}
    for label, gsp in (("Men", jm.GENDER["Men"]), ("Women", jm.GENDER["Women"])):
        cols[label] = labor_force_period_axis(df, gsp, [year], [concept_sp], percent=percent).iloc[:, 0]
    return pd.DataFrame(cols)


# --- Informality dataset (data/dane/job_market/informalidad/) ---
# df passed to these functions is pre-filtered to Perspectiva=="Total nacional" and the
# correct gender (Total->total.csv, Men/Women->sexo.csv filtered by Sexo). No percent arg.

def _inf_clean(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["Valor"].notna() & (df["Valor"] != 0)]


def informality_pivot(df: pd.DataFrame, period_sp, concepts_sp: list,
                      *, percent: bool = False, denom_sp=None) -> pd.DataFrame:
    """Year x Concepto pivot. percent -> concept / denom_sp * 100 (denom_sp is a Concepto
    row in df); else people x1000. period_sp None -> mean across 12 windows."""
    d = _inf_clean(df)
    if period_sp is not None:
        d = d[d["Periodo"] == period_sp]
    table = d.pivot_table(index="Fecha", columns="Concepto", values="Valor", aggfunc="mean")
    if percent:
        out = {c: table[c] / table[denom_sp] * 100
               for c in concepts_sp if c in table.columns and denom_sp in table.columns}
        pivot = pd.DataFrame(out).reindex(columns=concepts_sp)
    else:
        pivot = table.reindex(columns=concepts_sp) * 1000
    return pivot.dropna(how="all")


def informality_period_axis(df: pd.DataFrame, years: list, concepts_sp: list,
                            *, percent: bool = False, denom_sp=None) -> pd.DataFrame:
    """x = rolling 3-month windows. >=2 concepts -> single year, one col per concept;
    else one col per year for the single concept. percent -> share of denom_sp per window."""
    d = _inf_clean(df)
    cols = {}
    if len(concepts_sp) >= 2:
        dy = d[d["Fecha"] == years[0]]
        den = dy[dy["Concepto"] == denom_sp].set_index("Periodo")["Valor"] if percent else None
        for c in concepts_sp:
            s = dy[dy["Concepto"] == c].set_index("Periodo")["Valor"]
            cols[c] = s / den * 100 if percent else s * 1000
    else:
        d_concept = d[d["Concepto"] == concepts_sp[0]]
        d_den = d[d["Concepto"] == denom_sp] if percent else None
        for y in years:
            s = d_concept[d_concept["Fecha"] == y].set_index("Periodo")["Valor"]
            if percent:
                den = d_den[d_den["Fecha"] == y].set_index("Periodo")["Valor"]
                cols[str(y)] = s / den * 100
            else:
                cols[str(y)] = s * 1000
    table = pd.DataFrame(cols).reindex(list(jm.PERIOD_EN))
    table.index = [jm.PERIOD_EN[p] for p in table.index]
    return table


def informality_gender_pivot(sexo_df: pd.DataFrame, period_sp, concept_sp: str,
                             *, percent: bool = False) -> pd.DataFrame:
    """Men vs Women for one concept, x = years. sexo_df filtered to Total nacional.
    percent -> share of each gender's own Población ocupada."""
    cols = {}
    for label, sexo in (("Men", "Hombres"), ("Women", "Mujeres")):
        gdf = sexo_df[sexo_df["Sexo"] == sexo]
        cols[label] = informality_pivot(
            gdf, period_sp, [concept_sp], percent=percent, denom_sp="Población ocupada").iloc[:, 0]
    return pd.DataFrame(cols)


def informality_gender_period_axis(sexo_df: pd.DataFrame, year: int, concept_sp: str,
                                   *, percent: bool = False) -> pd.DataFrame:
    """Men vs Women for one concept and one year, x = rolling 3-month windows."""
    cols = {}
    for label, sexo in (("Men", "Hombres"), ("Women", "Mujeres")):
        gdf = sexo_df[sexo_df["Sexo"] == sexo]
        cols[label] = informality_period_axis(
            gdf, [year], [concept_sp], percent=percent, denom_sp="Población ocupada").iloc[:, 0]
    return pd.DataFrame(cols)


def informality_group_pivot(df: pd.DataFrame, period_sp, concept_sp: str,
                            *, percent: bool = False) -> pd.DataFrame:
    """Formal vs Informal for one concept, x = years. df has the `Grupo` column.
    percent -> share of each group's own total."""
    cols = {}
    for grupo in ("Formal", "Informal"):
        gdf = df[df["Grupo"] == grupo]
        cols[grupo] = informality_pivot(
            gdf, period_sp, [concept_sp], percent=percent, denom_sp=grupo).iloc[:, 0]
    return pd.DataFrame(cols)


def informality_group_period_axis(df: pd.DataFrame, year: int, concept_sp: str,
                                  *, percent: bool = False) -> pd.DataFrame:
    """Formal vs Informal for one concept and one year, x = rolling 3-month windows."""
    cols = {}
    for grupo in ("Formal", "Informal"):
        gdf = df[df["Grupo"] == grupo]
        cols[grupo] = informality_period_axis(
            gdf, [year], [concept_sp], percent=percent, denom_sp=grupo).iloc[:, 0]
    return pd.DataFrame(cols)


# --- Regions dataset (data/dane/job_market/regiones/): region in `Perspectiva`, semesters I/II ---
def region_norm(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse `Perspectiva` whitespace (merges the double-space Pacífica variant), drop the
    `Total nacional` aggregate (excluded from the Regions UI), and turn the CSV's missing-data
    zeros into NaN (e.g. Orinoquía's pre-2014/2020 years) so charts show gaps, not 0."""
    df = df.copy()
    df["Perspectiva"] = df["Perspectiva"].str.replace(r"\s+", " ", regex=True).str.strip()
    df["Valor"] = df["Valor"].replace(0, float('nan'))
    return df[df["Perspectiva"] != "Total nacional"]


def region_jm_map_data(df: pd.DataFrame, concept_sp: str, *, denom_sp: str) -> pd.DataFrame:
    """Per-region mean share of `concept_sp` (reuse the matching rate row when present, else
    value / denom * 100), keyed on the region label. Returns Code (region label, matches the
    geojson `region` property), Name (display), value. `df` pre-filtered to one year + gender."""
    rate = jm.REGION_RATE_CONCEPTS.get(concept_sp)
    if rate and rate in df["Concepto"].values:
        pct = df[df["Concepto"] == rate].set_index(["Fecha", "Perspectiva"])["Valor"]
    else:
        num = df[df["Concepto"] == concept_sp].set_index(["Fecha", "Perspectiva"])["Valor"]
        den = df[df["Concepto"] == denom_sp].set_index(["Fecha", "Perspectiva"])["Valor"]
        pct = num / den * 100
    out = pct.groupby("Perspectiva").mean().reset_index(name="value").rename(columns={"Perspectiva": "Code"})
    out["Name"] = out["Code"].map(jm.REGION_EN)
    return out[["Code", "Name", "value"]]


def region_jm_pivot(df: pd.DataFrame, concepts_sp: list, period_sp,
                    *, percent: bool = False) -> pd.DataFrame:
    """Year x Concepto pivot for one region (`df` pre-filtered to region + gender). period_sp None
    -> mean across the two semesters. percent -> per-concept shares (no x1000)."""
    d = df if period_sp is None else df[df["Periodo"] == period_sp]
    table = d.pivot_table(index="Fecha", columns="Concepto", values="Valor", aggfunc="mean")
    if percent:
        out = _to_percent(table, jm.REGION_PET_CONCEPT, jm.REGION_RATE_CONCEPTS).reindex(columns=concepts_sp)
    else:
        out = table.reindex(columns=concepts_sp) * 1000
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out.dropna(how="all")


def region_jm_region_pivot(df: pd.DataFrame, concept_sp: str, period_sp,
                           *, percent: bool = False) -> pd.DataFrame:
    """Year x Region pivot of one concept (`df` pre-filtered to the selected regions + gender).
    percent -> per-region share (rate row or value / PET * 100); else people counts x1000."""
    d = df if period_sp is None else df[df["Periodo"] == period_sp]
    rate = jm.REGION_RATE_CONCEPTS.get(concept_sp)
    if percent and rate and rate in d["Concepto"].values:
        pivot = d[d["Concepto"] == rate].pivot_table(
            index="Fecha", columns="Perspectiva", values="Valor", aggfunc="mean")
    else:
        num = d[d["Concepto"] == concept_sp].pivot_table(
            index="Fecha", columns="Perspectiva", values="Valor", aggfunc="mean")
        if percent:
            den = d[d["Concepto"] == jm.REGION_PET_CONCEPT].pivot_table(
                index="Fecha", columns="Perspectiva", values="Valor", aggfunc="mean")
            pivot = num / den * 100
        else:
            pivot = num * 1000
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot.dropna(how="all")


def region_jm_period_axis(df: pd.DataFrame, years: list, concepts_sp: list, regions: list,
                          *, percent: bool = False) -> pd.DataFrame:
    """Semester axis (x = First/Second semester). One column per the dimension that is multi:
    >=2 concepts -> one column per concept (years[0], regions[0]); >=2 regions -> one column per
    region (years[0], one concept); else -> one column per year (one concept + one region).
    `df` pre-filtered to gender. percent -> region rate rows / value-over-PET shares (no x1000)."""
    d = df[df["Fecha"].isin(years)]
    scale = 1000
    if percent:
        wide = d.pivot_table(index=["Fecha", "Perspectiva", "Periodo"], columns="Concepto",
                             values="Valor", aggfunc="mean")
        d = _to_percent(wide, jm.REGION_PET_CONCEPT, jm.REGION_RATE_CONCEPTS).rename_axis(columns="Concepto").stack().rename("Valor").reset_index()
        scale = 1
    cols = {}
    if len(concepts_sp) >= 2:                       # concept priority -> single year + region
        base = d[(d["Fecha"] == years[0]) & (d["Perspectiva"] == regions[0])]
        for c in concepts_sp:
            cols[c] = base[base["Concepto"] == c].set_index("Periodo")["Valor"]
    elif len(regions) >= 2:                         # region priority -> single year + concept
        base = d[(d["Fecha"] == years[0]) & (d["Concepto"] == concepts_sp[0])]
        for r in regions:
            cols[r] = base[base["Perspectiva"] == r].set_index("Periodo")["Valor"]
    else:                                           # year priority -> one concept + region
        base = d[(d["Concepto"] == concepts_sp[0]) & (d["Perspectiva"] == regions[0])]
        for y in years:
            cols[str(y)] = base[base["Fecha"] == y].set_index("Periodo")["Valor"]
    table = pd.DataFrame(cols).reindex(list(jm.REGION_PERIOD_EN)) * scale
    table.index = [jm.REGION_PERIOD_EN[p] for p in table.index]
    return table


def region_jm_gender_pivot(df: pd.DataFrame, period_sp, concept_sp: str,
                           *, percent: bool = False) -> pd.DataFrame:
    """Men vs Women for one concept, x = years. `df` = sexo.csv filtered to one region. Columns Men/Women."""
    cols = {}
    for label, sx in (("Men", jm.REGION_GENDER["Men"]), ("Women", jm.REGION_GENDER["Women"])):
        cols[label] = region_jm_pivot(df[df["Sexo"] == sx], [concept_sp], period_sp, percent=percent).iloc[:, 0]
    return pd.DataFrame(cols)


def region_jm_gender_period_axis(df: pd.DataFrame, year: int, concept_sp: str, region: str,
                                 *, percent: bool = False) -> pd.DataFrame:
    """Men vs Women for one concept and one year, x = semesters. `df` = sexo.csv filtered to one region."""
    cols = {}
    for label, sx in (("Men", jm.REGION_GENDER["Men"]), ("Women", jm.REGION_GENDER["Women"])):
        cols[label] = region_jm_period_axis(
            df[df["Sexo"] == sx], [year], [concept_sp], [region], percent=percent).iloc[:, 0]
    return pd.DataFrame(cols)


# --- Child Labor dataset (data/dane/job_market/infantil/): annual, Total nacional only ---
def child_labor_pivot(df: pd.DataFrame, specs: list, all_minors: pd.Series,
                      *, percent: bool = False) -> pd.DataFrame:
    """Year x concept. specs: list of (label, count_sp, rate_sp). df pre-filtered to
    Perspectiva=='Total nacional' and the chosen gender. percent -> the CSV rate row if present,
    else count / all_minors * 100; otherwise count * 1000 (thousands -> people).
    all_minors: year-indexed Series of the both-sexes minor count (thousands)."""
    table = df.pivot_table(index="Fecha", columns="Concepto", values="Valor", aggfunc="mean")
    cols = {}
    for label, count_sp, rate_sp in specs:
        if percent:
            if rate_sp in table.columns:
                cols[label] = table[rate_sp]
            elif count_sp in table.columns:
                cols[label] = table[count_sp] / all_minors * 100
        elif count_sp in table.columns:
            cols[label] = table[count_sp] * 1000
    out = pd.DataFrame(cols)
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out.dropna(how="all")


def child_labor_gender_pivot(sexo_df: pd.DataFrame, spec: tuple, all_minors: pd.Series,
                             *, percent: bool = False) -> pd.DataFrame:
    """Men vs Women for one concept, x = years. spec: ({"Men": sp, "Women": sp}, rate_sp).
    Columns Men/Women."""
    count_by_gender, rate_sp = spec
    cols = {}
    for label, sexo in (("Men", "Hombres"), ("Women", "Mujeres")):
        gdf = sexo_df[sexo_df["Sexo"] == sexo]
        s = child_labor_pivot(gdf, [(label, count_by_gender[label], rate_sp)], all_minors, percent=percent)
        cols[label] = s.iloc[:, 0] if not s.empty else pd.Series(dtype=float)
    return pd.DataFrame(cols)
