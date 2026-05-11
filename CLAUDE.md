# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
streamlit run app.py
```

App must be run from the repo root — all data paths are relative (`./data/...`).

## Architecture

Multi-page Streamlit app displaying Colombian macroeconomic statistics. Entry point is `app.py` (homepage); pages live in `pages/`.

**Data flow:**
1. CSVs in `data/` → read by page files → cleaned by `pages/helpers/macro/macro_functions.py` → charted by `pages/helpers/macro/macro_charts.py`
2. Raw data comes from two sources: **DANE** (National Statistics Dept) and **Banco de la República** (Central Bank)

**Key modules:**
- `pages/Macroeconomics.py` — page entry point, loads data, sidebar radio selects section (GDP/CPI), delegates to renderers
- `pages/tabs/gdp.py` — GDP tab logic: method/perspective/category selectors, sidebar filters, calls macro_functions + macro_charts
- `pages/tabs/cpi.py` — CPI tab logic: method/perspective/category selectors, sidebar filters, calls macro_functions + macro_charts
- `pages/helpers/macro/macro_functions.py` — data cleaning (`clean_gdp`, `clean_annual_growth`) and Streamlit sidebar/filter logic (`generalities_spend_product`)
- `pages/helpers/macro/macro_charts.py` — Plotly chart builders (`line_chart`, `bar_chart` — generic, take `info` list for titles/axis labels; `gdp_growth` — single-year selection renders gauge indicator instead of line chart)
- `generalities/` — dicts mapping Spanish column names (from source CSVs) to English display labels; `dictionaries.py` has filter UI dicts (presidents, months); `inflation.py` has CPI perspective name mappings (Spanish CSV column → English label); `function.py` has shared helpers (`get_valid_presidents`, `find_key_by_value`)
- `clean_data/` — one-off scripts for transforming raw Excel/CSV source files into the cleaned CSVs in `data/`

**Data directory layout:**
```
data/
  dane/GDP/{spend,production,income}/   ← DANE quarterly GDP tables (columns = year-quarter, rows = concepts)
  banco_republica/GDP/                  ← annual_growth.csv, quarter_growth.csv
  banco_republica/CPI/                  ← inflacion_15.csv + spend_category/ by city
  banco_republica/population/
  banco_republica/unemployment/
```

**Translation pattern:** Each GDP perspective has a matching dict in `generalities/gdp_spend.py` (or `gdp_production.py`, `gdp_income.py`). The dict key is the Spanish `Concepto` value in the CSV; the value is the English label shown in the UI. `gdp.py` dynamically resolves which dict to use via `getattr(t, f"spend_{file}_terms", None)`.

**President filter:** `presidents` dict maps name → list of years (integers). Both `macro_functions.py` and `gdp.py` filter valid presidents by intersecting the data's year range with `presidents[name]`.
