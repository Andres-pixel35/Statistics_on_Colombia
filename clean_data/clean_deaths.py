import os
import re
import glob
import tempfile
import subprocess
import pandas as pd
from xlrd.biffh import XLRDError
from generalities.function import norm

src_dir = "./data/original/dane/deaths"
out_dir = "./data/dane/deaths"

CAUSE_RE = re.compile(r"^\d+\s")  # "001 Enfermedades..."

# Canonical labels assigned positionally so columns align across all years
# (e.g. 2025 spells "De 7 a 27 días" while 2019-2024 use the typo "...dias").
AREA_GROUPS = ["Total", "Cabecera municipal", "Centro poblado",
               "Rural disperso", "Sin información"]
AGE_GROUPS = [
    "Total", "Menor 1 hora", "De 1 a 23 horas", "De 1 a 6 días",
    "De 7 a 27 días", "De 28 a 29 días", "De 1 a 5 meses", "De 6 a 11 meses",
    "De 1 año", "De 2 a 4 años", "De 5 a 9 años", "De 10 a 14 años",
    "De 15 a 19 años", "De 20 a 24 años", "De 25 a 29 años", "De 30 a 34 años",
    "De 35 a 39 años", "De 40 a 44 años", "De 45 a 49 años", "De 50 a 54 años",
    "De 55 a 59 años", "De 60 a 64 años", "De 65 a 69 años", "De 70 a 74 años",
    "De 75 a 79 años", "De 80 a 84 años", "De 85 a 89 años", "De 90 a 94 años",
    "De 95 a 99 años", "De 100 años y más", "Edad desconocida",
]
AGE_GROUPS_MUN = [
    "Total", "Menor 1 año", "De 1-4 años", "De 5-14 años", "De 15-44 años",
    "De 45-64 años", "De 65-84 años", "De 85-99 años", "De 100 y más",
    "Edad desconocida",
]
SUB = ["Hombres", "Mujeres", "Indeterminado"]


def read_book(path):
    """Return a pandas ExcelFile, decrypting protected .xls via LibreOffice."""
    if path.lower().endswith(".xlsx"):
        return pd.ExcelFile(path, engine="openpyxl")
    try:
        return pd.ExcelFile(path, engine="xlrd")
    except XLRDError:
        tmp = tempfile.mkdtemp(prefix="deaths_")
        profile = os.path.join(tmp, "profile")
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "xlsx", "--outdir", tmp,
             f"-env:UserInstallation=file://{profile}", path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        stem = os.path.splitext(os.path.basename(path))[0]
        return pd.ExcelFile(os.path.join(tmp, stem + ".xlsx"), engine="openpyxl")


def to_int(series):
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def is_national(series):
    return series.astype(str).str.strip().str.lower() == "total nacional"


def files_by_year():
    out = {}
    for path in glob.glob(os.path.join(src_dir, "*")):
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem.isdigit():
            out[int(stem)] = path
    return dict(sorted(out.items()))


def gender_columns(labels):
    """["Total_Hombres", "Total_Mujeres", ...] for each group label."""
    return [f"{label}_{sub}" for label in labels for sub in SUB]

def check_groups(df, nat_index, start, expected, year, sheet):
    """Guard: positional group mapping breaks silently if a file reorders columns.

    The level-1 header sits 2 rows above the national row; ffill it and verify each
    canonical group label lands where we read it (cols start, start+3, ...).
    """
    header = df.loc[nat_index - 2].ffill()
    for gi, label in enumerate(expected):
        got = header.iloc[start + gi * 3]
        if norm(got) != norm(label):
            raise ValueError(
                f"{year} {sheet}: header col {start + gi * 3} is {got!r}, "
                f"expected {label!r} — column layout changed, fix the positional mapping."
            )


def cuadro1(year, path):
    """Return (national_dict, area_df) from Cuadro1 (all years).

    17 cols: col0 age group, col1 grand total, then 5 area groups x 3 genders.
    """
    book = read_book(path)
    sheet = "Cuadro1" if "Cuadro1" in book.sheet_names else book.sheet_names[0]
    df = book.parse(sheet, header=None).dropna(how="all")

    cols = gender_columns(AREA_GROUPS)  # 15 names, map to df cols 2..16

    nat = df[is_national(df.iloc[:, 0])].iloc[0]
    check_groups(df, nat.name, 2, AREA_GROUPS, year, sheet)
    national = {"Fecha": year, "total": int(nat.iloc[1])}
    for i, name in enumerate(cols):
        national[name] = int(pd.to_numeric(nat.iloc[2 + i], errors="coerce") or 0)

    # Age rows: numeric total (col1), excluding the national aggregate.
    is_age = pd.to_numeric(df.iloc[:, 1], errors="coerce").notna() & ~is_national(df.iloc[:, 0])
    ages = df[is_age].copy()
    area_df = pd.DataFrame({
        "Fecha": year,
        "grupo_edad": ages.iloc[:, 0].astype(str).str.strip().values,
        "total": to_int(ages.iloc[:, 1]).values,
    })
    for i, name in enumerate(cols):
        area_df[name] = to_int(ages.iloc[:, 2 + i]).values
    return national, area_df


def cuadro_dept(year, path, sheet):
    """Return department x cause df from Cuadro11 (occurrence) / Cuadro12 (residence).

    97 cols: col0 index, col1 department, col2 cause, col3 grand total,
    then 31 age groups x 3 genders.
    """
    df = read_book(path).parse(sheet, header=None).dropna(how="all")

    nat_index = df[is_national(df.iloc[:, 1])].index[0]
    check_groups(df, nat_index, 4, AGE_GROUPS, year, sheet)

    departamento = df.iloc[:, 1].astype("object").ffill().astype(str).str.strip()
    causa = df.iloc[:, 2].astype(str).str.strip()
    is_cause = causa.str.match(CAUSE_RE)  # drops "TOTAL" rows and footnotes
    rows = df[is_cause]

    cols = gender_columns(AGE_GROUPS)  # 93 names, map to df cols 4..96
    out = pd.DataFrame({
        "Fecha": year,
        "departamento": departamento[is_cause].values,
        "causa": rows.iloc[:, 2].astype(str).str.strip().values,
        "total": to_int(rows.iloc[:, 3]).values,
    })
    for i, name in enumerate(cols):
        out[name] = to_int(rows.iloc[:, 4 + i]).values
    return out


def cuadro5_dept_mun(year, path):
    """Return department x municipio x cause df from Cuadro5 (residence, 67-cause list).

    36 cols: col0 dept code, col1 extended DIVIPOLA, col2 departamento (ffill),
    col3 municipio (ffill, "Total Dpto" for the dept-aggregate block), col4 cause,
    col5 grand total, then 10 age groups x 3 genders.

    Cuadro5 uses a different, coarser cause classification (67-list) than Cuadro11/12's
    105-list — the codes are not comparable, so this is a separate output, not a
    replacement. The dept-aggregate block ("Total Dpto") is dropped since it's
    redundant with grouping the municipio rows by departamento.
    """
    df = read_book(path).parse("Cuadro5", header=None).dropna(how="all")

    nat_index = df[is_national(df.iloc[:, 2])].index[0]
    check_groups(df, nat_index, 6, AGE_GROUPS_MUN, year, "Cuadro5")

    departamento = df.iloc[:, 2].astype("object").ffill().astype(str).str.strip()
    municipio = df.iloc[:, 3].astype("object").ffill().astype(str).str.strip()
    causa = df.iloc[:, 4].astype(str).str.strip()
    is_cause = causa.str.match(CAUSE_RE) & (municipio != "Total Dpto")
    rows = df[is_cause]

    cols = gender_columns(AGE_GROUPS_MUN)  # 30 names, map to df cols 6..35
    out = pd.DataFrame({
        "Fecha": year,
        "departamento": departamento[is_cause].values,
        "municipio": municipio[is_cause].values,
        "causa": rows.iloc[:, 4].astype(str).str.strip().values,
        "total": to_int(rows.iloc[:, 5]).values,
    })
    for i, name in enumerate(cols):
        out[name] = to_int(rows.iloc[:, 6 + i]).values
    return out


def main():
    os.makedirs(out_dir, exist_ok=True)
    years = files_by_year()

    totals, areas, occ, res, mun = [], [], [], [], []
    for year, path in years.items():
        national, area_df = cuadro1(year, path)
        totals.append(national)
        areas.append(area_df)
        line = f"{year}: total={national['total']}, age_rows={len(area_df)}"
        if year >= 2019:
            o = cuadro_dept(year, path, "Cuadro11")
            r = cuadro_dept(year, path, "Cuadro12")
            m = cuadro5_dept_mun(year, path)
            occ.append(o)
            res.append(r)
            mun.append(m)
            line += f", occ_rows={len(o)}, res_rows={len(r)}, mun_rows={len(m)}"
        print(line)

    pd.DataFrame(totals).set_index("Fecha").to_csv(os.path.join(out_dir, "total.csv"))
    pd.concat(areas, ignore_index=True).to_csv(
        os.path.join(out_dir, "area_grupo_edad.csv"), index=False)
    pd.concat(mun, ignore_index=True).to_csv(
        os.path.join(out_dir, "departamento_municipio_residencia.csv"), index=False)
    pd.concat(occ, ignore_index=True).to_csv(
        os.path.join(out_dir, "departamento_muerte.csv"), index=False)
    pd.concat(res, ignore_index=True).to_csv(
        os.path.join(out_dir, "departamento_residencia.csv"), index=False)

    print(f"Saved 5 CSVs to {out_dir} ({len(years)} years; dept CSVs cover 2019+)")


if __name__ == "__main__":
    main()
