# Trimestral

- `balance_cop.csv` — quarterly fiscal balance (Gobierno Nacional Central), **miles de millones
  (COP)** — same unit as `data/banco_republica/GDP/nominal_annual.csv`'s `PIB`.
- `balance_pib.csv` — same rows, **% of GDP**, already in percentage-point units
  (not a 0-1 fraction).

`Grupo` — the row's ancestor `Concepto` chain, taken from the source workbook's own
outline indent levels. Empty for top-level rows.
