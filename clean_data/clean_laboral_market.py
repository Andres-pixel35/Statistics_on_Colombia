import os
import re
import pandas as pd
from generalities.function import norm

src_dir = "./data/original/dane/laboral_market"
out_dir = "./data/dane/laboral_market"

# file -> dimension column name, output sub-folder, {sheet_index: csv_name}
FILES = [
    {"file": "mercado_laboral.xlsx", "dim": "Perspectiva", "folder": "Mercado Laboral",
     "sheets": {3: "total", 6: "posicion_ocupacional", 7: "ramas_actividad",
                8: "fuera_fuerza_trabajo"}},
    {"file": "departamentos.xls", "dim": "Departamentos", "folder": "Departamentos",
     "sheets": {2: "total", 3: "hombres", 4: "mujeres", 7: "ramas_actividad"}},
    {"file": "informalidad.xlsx", "dim": "Perspectiva", "folder": "informalidad",
     "sheets": {6: "total", 8: "sexo", 9: "educacion", 10: "ramas_actividad",
                11: "posicion_ocupacional", 12: "lugar_trabajo", 13: "tamano_empresa",
                14: "seguridad_social", 15: "seguridad_social_sexo"}},
    {"file": "regiones.xls", "dim": "Perspectiva", "folder": "regiones",
     "sheets": {3: "total", 4: "sexo"}},
    {"file": "infantil.xlsx", "dim": "Perspectiva", "folder": "infantil",
     "sheets": {2: "total", 3: "sexo", 4: "edad", 6: "asistencia_escolar",
                7: "razon", 8: "horas", 9: "rama_actividad", 10: "posicion",
                11: "ingreso", 13: "actividades_sexo"}},
]

GENDER = {"hombres": "Hombres", "mujeres": "Mujeres",
          "hombre": "Hombres", "mujer": "Mujeres"}
YEAR_RE = re.compile(r"(19|20)\d{2}")
MONTHS = {"ene", "feb", "mar", "abr", "may", "jun",
          "jul", "ago", "sep", "oct", "nov", "dic"}
GENDER_SUFFIX = re.compile(r"^(.*\S)\s*-\s*(hombres|mujeres)\s*$", re.I)

# Sheets where the whole sheet is one gender (block titles are departments).
FILE_SEXO = {("departamentos.xls", 3): "Hombres",
             ("departamentos.xls", 4): "Mujeres"}


def read_sheet(path, sheet_idx):
    engine = "openpyxl" if path.lower().endswith(".xlsx") else "xlrd"
    return pd.read_excel(path, sheet_name=sheet_idx, header=None, engine=engine)


def is_year(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return 1990 <= f <= 2100 and f == int(f)


def is_num(v):
    return pd.notna(pd.to_numeric(v, errors="coerce"))


def normalize_period(label):
    """Collapse DANE period variants to one label.

    Strips embedded years and footnote marks, standardizes hyphen spacing, and
    capitalizes month tokens so 'Nov 07 - ene 08' -> 'Nov - Ene', 'IV - 2022' ->
    'IV', 'Ene - mar'/'Ago- Oct'/'Feb-Abr'/'Ene - Mar*' all fold onto one label.
    Roman numerals ('IV', 'I', 'II') and 'Anual' are left untouched.
    """
    s = re.sub(r"\d+", "", str(label)).replace("*", "").replace("^", "")
    s = re.sub(r"\s*-\s*", " - ", s)
    s = re.sub(r"\s+", " ", s).strip().strip(" -").strip()
    return " ".join(t.capitalize() if t.lower() in MONTHS else t for t in s.split(" "))


def title_above(df, anchor):
    """Nearest non-null col0 text above the anchor row = the block title."""
    for r in range(anchor - 1, -1, -1):
        cell = df.iloc[r, 0]
        if pd.notna(cell) and str(cell).strip():
            return str(cell).strip()
    return ""


def split_gender(title):
    """'Total Nacional - Hombres' -> ('Total Nacional', 'Hombres').

    Standalone 'HOMBRES' (no dash) returns (title, None) so it stays a block title.
    """
    m = GENDER_SUFFIX.match(title)
    if m:
        return m.group(1).strip(), GENDER[m.group(2).lower()]
    return title, None


def classify(df, H):
    """Return (data_start, {col: (year, periodo)}) for the block at anchor row H.

    Four families: C embedded 'IV - YYYY' headers; A year row + period row;
    annual with years on the Concepto row; annual with years on the next row.
    """
    ncols = df.shape[1]
    row_h = df.iloc[H]
    row_h1 = df.iloc[H + 1] if H + 1 < len(df) else None
    cols = range(1, ncols)

    # Family C: header strings embed a period token AND a year ('IV - 2022').
    # A bare text-typed year like '2008' (normalize_period -> '') is NOT family C —
    # it is a family-A year cell that happens to be stored as text.
    cc = [c for c in cols if isinstance(row_h[c], str)
          and YEAR_RE.search(row_h[c]) and normalize_period(row_h[c])]
    if cc:
        return H + 1, {c: (int(YEAR_RE.search(row_h[c]).group(0)),
                           normalize_period(row_h[c])) for c in cc}

    years_h = [c for c in cols if is_year(row_h[c])]
    if years_h:
        text_h1 = (row_h1 is not None and
                   any(isinstance(row_h1[c], str) and row_h1[c].strip()
                       and not is_year(row_h1[c]) for c in cols))
        if text_h1:  # Family A: years (ffill) on H, period labels on H+1
            year_by_col, last = {}, None
            for c in cols:
                if is_year(row_h[c]):
                    last = int(row_h[c])
                year_by_col[c] = last
            colmap = {c: (year_by_col[c], normalize_period(row_h1[c]))
                      for c in cols
                      if isinstance(row_h1[c], str) and row_h1[c].strip()
                      and year_by_col[c] is not None}
            return H + 2, colmap
        # Annual: years on the Concepto row, no period row
        return H + 1, {c: (int(row_h[c]), "Anual") for c in years_h}

    # Annual: years on the row below the Concepto row
    if row_h1 is not None:
        years_h1 = [c for c in cols if is_year(row_h1[c])]
        if years_h1:
            return H + 2, {c: (int(row_h1[c]), "Anual") for c in years_h1}
    return H + 1, {}


def parse_sheet(df, dim, default_sexo="Total"):
    anchors = [r for r in range(len(df)) if norm(df.iloc[r, 0]) == "concepto"]
    titles = {a: title_above(df, a) for a in anchors}
    records = []

    for i, H in enumerate(anchors):
        # Gender may live in the title ('Total Nacional - Hombres'); split it out.
        perspectiva, title_sexo = split_gender(titles[H])
        data_start, colmap = classify(df, H)
        if not colmap:
            continue
        end = titles_index(anchors, titles, i, df)

        def emit(row, concept, sexo):
            for c, (year, periodo) in colmap.items():
                num = pd.to_numeric(df.iloc[row, c], errors="coerce")
                if pd.notna(num):
                    records.append({"Fecha": year, dim: perspectiva, "Sexo": sexo,
                                    "Concepto": concept, "Periodo": periodo,
                                    "Valor": float(num)})

        sexo = title_sexo or default_sexo
        headline = None  # first normal concept of the block (e.g. 'Población ocupada')
        for r in range(data_start, end):
            c0 = df.iloc[r, 0]
            if pd.isna(c0) or not str(c0).strip():
                continue
            label = str(c0).strip()
            if norm(label) == "concepto":
                continue
            if norm(label) in GENDER:  # nested gender sub-header (valued or not)
                sexo = GENDER[norm(label)]
                if headline is not None and any(is_num(df.iloc[r, c]) for c in colmap):
                    emit(r, headline, sexo)  # valued header = that gender's headline total
                continue
            if not any(is_num(df.iloc[r, c]) for c in colmap):
                continue
            if headline is None:
                headline = label
            emit(r, label, sexo)

    return pd.DataFrame(records, columns=["Fecha", dim, "Sexo", "Concepto",
                                          "Periodo", "Valor"])


def titles_index(anchors, titles, i, df):
    """Block data ends at the title row of the next block (or end of sheet)."""
    if i + 1 < len(anchors):
        next_anchor = anchors[i + 1]
        for r in range(next_anchor - 1, -1, -1):
            cell = df.iloc[r, 0]
            if pd.notna(cell) and str(cell).strip():
                return r
        return next_anchor
    return len(df)


def main():
    total_csv = 0
    for cfg in FILES:
        path = os.path.join(src_dir, cfg["file"])
        folder = os.path.join(out_dir, cfg["folder"])
        os.makedirs(folder, exist_ok=True)
        for idx, name in cfg["sheets"].items():
            df = read_sheet(path, idx)
            default_sexo = FILE_SEXO.get((cfg["file"], idx), "Total")
            out = parse_sheet(df, cfg["dim"], default_sexo)
            out.to_csv(os.path.join(folder, name + ".csv"), index=False)
            total_csv += 1
            print(f"{cfg['folder']}/{name}.csv: {len(out)} rows")
    print(f"\nSaved {total_csv} CSVs to {out_dir}")


if __name__ == "__main__":
    main()
