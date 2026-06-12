import sys
import os
import re
import pandas as pd

SRC = "../data/original/dane/population"
OUT = "../data/dane/population"

# per-category: list of (filename, sheet, format)  format in {"old", "new"}
FILES = {
    "nacional": [
        ("1950-2017.xlsx", "Nacional_1950_2017", "old"),
        ("2018-2070.xlsx", "PobNacionalxÁreaSexoEdad", "new"),
    ],
    "departamental": [
        ("1985-1992.xlsx", "Departamental_1985_1992", "old"),
        ("1993-2004.xlsx", "Departamental_1993_2004", "old"),
        ("2005-2017.xlsx", "Departamental_2005-2017", "old"),
        ("2018-2050.xlsx", "PobDepartamentalxÁreaSexoEdad", "new"),
    ],
    "municipal": [
        ("1985-1994.xlsx", "Municipal", "old"),
        ("1995-2004.xlsx", "Municipal", "old"),
        ("2005-2017.xlsx", "NuevaMpal", "old"),
        ("2018-2042.xlsx", "PobMunicipalxÁreaSexoEdad", "new"),
    ],
}

# id columns to KEEP per category (canonical names)
ID_KEEP = {
    "nacional": ["AÑO"],
    "departamental": ["DP", "DPNOM", "AÑO"],
    "municipal": ["DP", "DPNOM", "Municipio", "AÑO"],
}

# NEW per-age label, e.g. "Hombres 0 años" / "Mujeres 1 año" / "Total 100 años y más"
AGE_RE = re.compile(r"^(Hombres|Mujeres|Total)\s+(\d+)\s+a[ñn]o", re.IGNORECASE)


def normalize_old(col):
    """Canonicalize an OLD-style column name."""
    col = str(col).strip()
    # drop the " y más" suffix on top-age columns: "Total_100 y más" -> "Total_100"
    col = re.sub(r"\s*y m[áa]s$", "", col)
    if col.lower() in ("total general", "total general"):
        return "Total"
    return col


def normalize_new(top_row, sub_row):
    """Build canonical column names from the NEW two-row header."""
    cols = []
    for top, sub in zip(top_row, sub_row):
        top = "" if pd.isna(top) else str(top).strip()
        sub = "" if pd.isna(sub) else str(sub).strip()
        label = sub or top
        m = AGE_RE.match(label)
        if m:
            cols.append(f"{m.group(1).title()}_{m.group(2)}")
        elif label == "Hombres":
            cols.append("Total Hombres")
        elif label == "Mujeres":
            cols.append("Total Mujeres")
        else:
            cols.append(label)
    return cols


def finalize(df):
    """Filter to Total-area rows and coerce AÑO to int."""
    df = df[df["ÁREA GEOGRÁFICA"] == "Total"].copy()
    df = df.drop(columns="ÁREA GEOGRÁFICA")
    df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce")
    df = df.dropna(subset=["AÑO"])
    df["AÑO"] = df["AÑO"].astype(int)
    return df


def read_old(path, sheet):
    probe = pd.read_excel(path, sheet_name=sheet, header=None, nrows=25)
    header_row = None
    for i, row in probe.iterrows():
        cells = {str(x).strip() for x in row.tolist()}
        if {"DP", "AÑO", "ÁREA GEOGRÁFICA"} <= cells:
            header_row = i
            break
    if header_row is None:
        raise ValueError(f"No OLD header row found in {path} :: {sheet}")
    df = pd.read_excel(path, sheet_name=sheet, header=header_row)
    df.columns = [normalize_old(c) for c in df.columns]
    return finalize(df)


def read_new(path, sheet):
    head = pd.read_excel(path, sheet_name=sheet, header=None, skiprows=7, nrows=2)
    cols = normalize_new(head.iloc[0].tolist(), head.iloc[1].tolist())
    df = pd.read_excel(path, sheet_name=sheet, header=None, skiprows=9, names=cols)
    return finalize(df)


def resolve_municipio(df):
    """Municipal files swap DPMP/MPIO between code and name across year-spans.
    Keep the all-non-numeric column (the name) as `Municipio`; drop the code."""
    name_col = next(
        c for c in ("DPMP", "MPIO")
        if c in df.columns and pd.to_numeric(df[c], errors="coerce").isna().all()
    )
    df = df.rename(columns={name_col: "Municipio"})
    return df.drop(columns=[c for c in ("DPMP", "MPIO") if c in df.columns])


def value_order(columns):
    """Ordered value columns present in the frame: sex×age, per-age total, aggregates."""
    order = []
    for prefix in ("Hombres", "Mujeres", "Total"):
        for age in range(101):
            order.append(f"{prefix}_{age}")
    order += ["Total Hombres", "Total Mujeres", "Total"]
    present = set(columns)
    return [c for c in order if c in present]


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in FILES:
        print("usage: python population_clean.py {nacional|departamental|municipal}")
        sys.exit(1)

    category = sys.argv[1]
    frames = []
    for filename, sheet, fmt in FILES[category]:
        path = os.path.join(SRC, category, filename)
        reader = read_old if fmt == "old" else read_new
        frame = reader(path, sheet)
        if category == "municipal":
            frame = resolve_municipio(frame)
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    cols = ID_KEEP[category] + value_order(df.columns)
    df = df[cols]

    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, f"{category}.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows → {out_path}")


if __name__ == "__main__":
    main()
