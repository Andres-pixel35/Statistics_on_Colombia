import os
import re
import glob
import tempfile
import unicodedata
import subprocess
import pandas as pd
from xlrd.biffh import XLRDError

src_dir = "../data/original/dane/borns"
out_dir = "../data/dane/borns"

AGE_RE = re.compile(r"^(De \d+-\d+ Años|Sin información)$")
MUNI_RE = re.compile(r"^\d+\s+\S")  # "05001 Medellín"


def read_book(path):
    """Return a pandas ExcelFile, decrypting protected .xls via LibreOffice."""
    if path.lower().endswith(".xlsx"):
        return pd.ExcelFile(path, engine="openpyxl")
    try:
        return pd.ExcelFile(path, engine="xlrd")
    except XLRDError:
        tmp = tempfile.mkdtemp(prefix="borns_")
        profile = os.path.join(tmp, "profile")
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "xlsx", "--outdir", tmp,
             f"-env:UserInstallation=file://{profile}", path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        stem = os.path.splitext(os.path.basename(path))[0]
        return pd.ExcelFile(os.path.join(tmp, stem + ".xlsx"), engine="openpyxl")


def slug(label):
    """Spanish header -> snake_case ascii column name."""
    text = unicodedata.normalize("NFKD", str(label)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


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


def cuadro1(year, path):
    """Return (national_row dict, age_df). Works for old single-sheet and new files."""
    book = read_book(path)
    if year <= 2018:
        df = book.parse(book.sheet_names[0], header=None, skiprows=10)
        has_indet = False
    else:
        df = book.parse("Cuadro1", header=None, skiprows=7)
        has_indet = True

    df = df.dropna(how="all")
    label = df.iloc[:, 0].astype(str).str.strip()

    nat = df[is_national(df.iloc[:, 0])].iloc[0]
    national = {
        "year": year,
        "total_nacional": int(nat.iloc[1]),
        "hombres": int(nat.iloc[2]),
        "mujeres": int(nat.iloc[3]),
        "indeterminado": int(nat.iloc[4]) if has_indet else 0,
    }

    ages = df[label.str.match(AGE_RE)].copy()
    age_df = pd.DataFrame({
        "year": year,
        "grupo_edad": ages.iloc[:, 0].astype(str).str.strip().values,
        "total": to_int(ages.iloc[:, 1]).values,
        "hombres": to_int(ages.iloc[:, 2]).values,
        "mujeres": to_int(ages.iloc[:, 3]).values,
        "indeterminado": to_int(ages.iloc[:, 4]).values if has_indet else 0,
    })
    return national, age_df


def cuadro3(year, path):
    """Return (department_df, municipality_df) from Cuadro3 (2019-2025)."""
    df = read_book(path).parse("Cuadro3", header=None, skiprows=7).dropna(how="all")
    dept = df.iloc[:, 2].astype(str).str.strip()
    muni = df.iloc[:, 3].astype(str).str.strip()
    # Department name ("05 Antioquia") only appears on its total row; carry it down to munis.
    dept_name = df.iloc[:, 2].astype("object").ffill().astype(str).str.strip()

    is_dept_total = dept.str.match(MUNI_RE)  # "<code> <name>" only on dept-total rows
    is_muni = muni.str.match(MUNI_RE)

    depts = df[is_dept_total].copy()
    dept_df = pd.DataFrame({
        "year": year,
        "departamento": depts.iloc[:, 2].astype(str).str.strip().values,
        "total": to_int(depts.iloc[:, 4]).values,
        "hombres": to_int(depts.iloc[:, 5]).values,
        "mujeres": to_int(depts.iloc[:, 6]).values,
        "indeterminado": to_int(depts.iloc[:, 7]).values,
    })

    munis = df[is_muni].copy()
    muni_df = pd.DataFrame({
        "year": year,
        "departamento": dept_name[is_muni].values,
        "municipio": munis.iloc[:, 3].astype(str).str.strip().values,
        "total": to_int(munis.iloc[:, 4]).values,
        "hombres": to_int(munis.iloc[:, 5]).values,
        "mujeres": to_int(munis.iloc[:, 6]).values,
        "indeterminado": to_int(munis.iloc[:, 7]).values,
    })
    return dept_df, muni_df


def cuadro13(year, path):
    """Return national-block age x education breakdown from Cuadro13 (2019-2025)."""
    book = read_book(path)
    head = book.parse("Cuadro13", header=None, skiprows=7, nrows=2)
    edu_cols = [slug(x) for x in head.iloc[1, 6:].tolist()]

    df = book.parse("Cuadro13", header=None, skiprows=7).dropna(how="all")
    # National block: from "Total Nacional" until the next department (col2 filled again).
    dept = df.iloc[:, 2]
    start = df.index[is_national(dept)][0]
    after = dept.loc[start + 1:]
    end = after[after.notna()].index.min()
    block = df.loc[start:(end - 1)] if pd.notna(end) else df.loc[start:]

    age_label = block.iloc[:, 4].astype(str).str.strip()
    rows = block[age_label.str.match(AGE_RE)].copy()

    out = pd.DataFrame({
        "year": year,
        "grupo_edad": rows.iloc[:, 4].astype(str).str.strip().values,
        "total": to_int(rows.iloc[:, 5]).values,
    })
    for i, name in enumerate(edu_cols):
        out[name] = to_int(rows.iloc[:, 6 + i]).values
    return out


def main():
    os.makedirs(out_dir, exist_ok=True)
    years = files_by_year()

    totals, ages, depts, munis, edus = [], [], [], [], []
    for year, path in years.items():
        national, age_df = cuadro1(year, path)
        totals.append(national)
        ages.append(age_df)
        if year >= 2019:
            dept_df, muni_df = cuadro3(year, path)
            depts.append(dept_df)
            munis.append(muni_df)
            edus.append(cuadro13(year, path))
        print(f"{year}: total_nacional={national['total_nacional']}, age_rows={len(age_df)}")

    total_df = pd.DataFrame(totals).set_index("year")
    total_df.to_csv(os.path.join(out_dir, "births_total.csv"))
    pd.concat(ages, ignore_index=True).to_csv(
        os.path.join(out_dir, "births_by_mother_age.csv"), index=False)
    pd.concat(depts, ignore_index=True).to_csv(
        os.path.join(out_dir, "births_by_department.csv"), index=False)
    pd.concat(munis, ignore_index=True).to_csv(
        os.path.join(out_dir, "births_by_municipality.csv"), index=False)
    pd.concat(edus, ignore_index=True).to_csv(
        os.path.join(out_dir, "births_by_education.csv"), index=False)

    print(f"Saved 5 CSVs to {out_dir} ({len(years)} years; 4/5/6 cover 2019-2025)")


if __name__ == "__main__":
    main()
