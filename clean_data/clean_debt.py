import os
import pandas as pd

src_path = "../data/original/hacienda/debt/Histórico Total Mayo2026.xls"
out_dir = "../data/hacienda/debt"

HEADER_LABELS = {"Corte a", "Fecha corte", "Fecha"}


def read_flat(xl, sheet, ncols=None, pct=False):
    """One-row-per-date sheets: Saldos, Fuente/Tasa/Moneda × interna/externa/total."""
    df = pd.read_excel(xl, sheet_name=sheet, header=None)
    hdr = df.index[df[0].isin(HEADER_LABELS)][0]
    if ncols:
        df = df.iloc[:, :ncols]
    df.columns = df.iloc[hdr]
    df = df.iloc[hdr + 1:].reset_index(drop=True)
    df = df.loc[:, df.columns.notna()]  # drop unlabeled stray columns (source artifacts)
    df = df.dropna(axis=1, how="all")  # drop labeled-but-empty stray columns
    df = df[df[df.columns[0]].notna()].reset_index(drop=True)  # drop stray embedded header rows
    df = df.rename(columns={df.columns[0]: "Fecha"})
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%Y-%m-%d")
    value_cols = df.columns[1:]
    df[value_cols] = df[value_cols].replace("-", pd.NA).apply(pd.to_numeric)
    if pct:
        df[value_cols] = df[value_cols] * 100
    return df


def read_indicadores(xl, sheet):
    """Duración/Vida media (años) + Cupón promedio (%), each × interna/externa/total."""
    df = pd.read_excel(xl, sheet_name=sheet, header=None)
    hdr = df.index[df[0].isin(HEADER_LABELS)][0]
    groups = df.iloc[hdr - 2].ffill()
    subs = df.iloc[hdr]
    cols = ["Fecha"] + [
        f"{groups[c]} - {' '.join(str(subs[c]).split())}" for c in df.columns[1:]
    ]
    df.columns = cols
    df = df.iloc[hdr + 1:].reset_index(drop=True)
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%Y-%m-%d")
    value_cols = df.columns[1:]
    df[value_cols] = df[value_cols].replace("-", pd.NA).apply(pd.to_numeric)
    cupon_cols = [c for c in value_cols if "Cupón" in c]
    df[cupon_cols] = df[cupon_cols] * 100
    return df


def read_perfil(xl, sheet):
    """Maturity/amortization schedule: 3 rows per Fecha corte (Amortizaciones/Intereses/Total),
    one column per maturity year."""
    df = pd.read_excel(xl, sheet_name=sheet, header=None)
    hdr = df.index[df[0].isin(HEADER_LABELS)][0]
    df.columns = df.iloc[hdr]
    df = df.iloc[hdr + 1:].reset_index(drop=True)
    date_col, period_col = df.columns[0], df.columns[1]
    group = (df[period_col] == "Amortizaciones").cumsum()
    df[date_col] = df.groupby(group)[date_col].transform(lambda s: s.ffill().bfill())
    df = df.rename(columns={date_col: "Fecha"})
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%Y-%m-%d")
    df = df.rename(columns={c: int(c) for c in df.columns if isinstance(c, float)})
    value_cols = [c for c in df.columns if c not in ("Fecha", "Período de servicio")]
    df[value_cols] = df[value_cols].replace("-", pd.NA).apply(pd.to_numeric)
    return df


README = {
    "saldos": """# Saldos

`saldos.csv` — monthly debt balance, **COP millones** (Colombian pesos, millions). Columns:
`Deuda interna`, `Deuda externa`, `Deuda total`. Not a percentage.
""",
    "fuente": """# Fuente

All values are **percentages (0-100)**, breakdown by debt instrument (e.g. TES, Bonos Fogafin).

- `fuente_interna.csv` — % of **internal** debt.
- `fuente_externa.csv` — % of **external** debt.
- `fuente_total.csv` — % of **total** debt.
""",
    "tasa": """# Tasa

All values are **percentages (0-100)**, breakdown by interest rate type (fixed vs. variable, and rate index for interna).

- `tasa_interna.csv` — % of **internal** debt.
- `tasa_externa.csv` — % of **external** debt.
- `tasa_total.csv` — % of **total** debt.
""",
    "moneda": """# Moneda

All values are **percentages (0-100)**, breakdown by currency.

- `moneda_interna.csv` — % of **internal** debt.
- `moneda_externa.csv` — % of **external** debt.
- `moneda_total.csv` — % of **total** debt.
""",
    "perfil": """# Perfil

`perfil_total.csv` — projected debt service schedule (maturity profile), **COP millones**.
Each `Fecha corte` (report date) has 3 rows (`Período de servicio`: Amortizaciones/Intereses/Total)
and one column per maturity year (2001-2062) showing the amount due that year. Not a percentage.
""",
    "indicadores": """# Indicadores

`indicadores.csv` — debt portfolio indicators, mixed units, each split by
**Deuda interna / Deuda externa / Deuda total**:

- `Duración - *`, `Vida media - *` — **years**. Not a percentage, not COP millones.
- `Cupón promedio - *` — **annual interest rate, percentage (0-100)**. `Deuda interna` is
  quoted in COP terms, `Deuda externa` in USD terms (per source). Not a share of total debt.
""",
}


def main():
    xl = pd.ExcelFile(src_path)

    outputs = {
        ("saldos", "saldos.csv"): read_flat(xl, "Saldos", ncols=4),
        ("fuente", "fuente_interna.csv"): read_flat(xl, "Fuente - interna", pct=True),
        ("fuente", "fuente_externa.csv"): read_flat(xl, "Fuente - externa", pct=True),
        ("fuente", "fuente_total.csv"): read_flat(xl, "Fuente - total", pct=True),
        ("tasa", "tasa_interna.csv"): read_flat(xl, "Tasa - interna", pct=True),
        ("tasa", "tasa_externa.csv"): read_flat(xl, "Tasa - externa", pct=True),
        ("tasa", "tasa_total.csv"): read_flat(xl, "Tasa - total", pct=True),
        ("moneda", "moneda_interna.csv"): read_flat(xl, "Moneda - interna", pct=True),
        ("moneda", "moneda_externa.csv"): read_flat(xl, "Moneda - externa", pct=True),
        ("moneda", "moneda_total.csv"): read_flat(xl, "Moneda - total", pct=True),
        ("perfil", "perfil_total.csv"): read_perfil(xl, "Perfil - total"),
        ("indicadores", "indicadores.csv"): read_indicadores(xl, "Indicadores"),
    }

    for folder in {folder for folder, _ in outputs}:
        os.makedirs(os.path.join(out_dir, folder), exist_ok=True)
        with open(os.path.join(out_dir, folder, "README.md"), "w") as f:
            f.write(README[folder])

    for (folder, name), df in outputs.items():
        path = os.path.join(out_dir, folder, name)
        df.to_csv(path, index=False)
        print(f"{os.path.join(folder, name)}: {len(df)} rows")

    print(f"\nSaved {len(outputs)} CSVs to {out_dir}")


if __name__ == "__main__":
    main()
