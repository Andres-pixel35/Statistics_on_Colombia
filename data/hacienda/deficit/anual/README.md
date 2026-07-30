# Anual

- `balance_cop.csv` — annual fiscal balance (Gobierno Nacional Central), **miles de millones
  (COP)** — same unit as `data/banco_republica/GDP/nominal_annual.csv`'s `PIB`.
- `balance_pib.csv` — same rows, **% of GDP** (DANE GDP denominator), already in
  percentage-point units (not a 0-1 fraction).

`Grupo` — the row's ancestor `Concepto` chain (e.g. `Renta`'s Grupo is
`1. INGRESOS TOTALES ... > INGRESOS CORRIENTES DE LA NACION > DIAN`), taken from the
source workbook's own outline indent levels. Empty for top-level rows
(`1. INGRESOS TOTALES`, `2. PAGOS TOTALES`, ...).

Both cover 1994-2025; **2025 figures are preliminary** per the source's `*Cifras
preliminares` footnote (the `*` marker was stripped from the column name).
