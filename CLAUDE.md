# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
streamlit run app.py
```

The app can be run from anywhere — data paths are absolute, anchored on `BASE_DIR` (`generalities/function.py`, resolves to the repo root). Exception: the `clean_data/*` scripts use relative `../data` paths and must be run from inside `clean_data/`.

## Architecture

Multi-page Streamlit app displaying Colombian macroeconomic statistics. Entry point is `app.py` (homepage); pages live in `pages/`.

**Data flow:**
1. CSVs in `data/` → read by page files → cleaned by `pages/helpers/macro/macro_functions.py` → charted by `pages/helpers/macro/macro_charts.py`
2. Raw data comes from four sources: **DANE** (National Statistics Dept), **Banco de la República** (Central Bank), **World Bank** (net migration), and **Migración Colombia** (inbound/outbound travelers, stored under `datos_abiertos/`)

**Key modules:**
- `pages/Macroeconomics.py` — page entry point, loads data, sidebar radio selects section (GDP/CPI/Population), delegates to renderers
- `pages/tabs/gdp.py` — GDP tab logic: method/perspective/category selectors, sidebar filters, calls macro_functions + macro_charts
- `pages/tabs/cpi.py` — CPI tab logic: method/perspective/category selectors, sidebar filters, calls macro_functions + macro_charts
- `pages/tabs/population.py` — entry `render_population` opens with a **View** radio (`generalities/migration.VIEW = ["National", "Migration", "Births", "Deaths"]`) routing to four renderers:
  - *National* (`_render_population_tab`): Total vs Growth selector. Total perspectives are National / Net Migration / Births / Deaths; Growth is year-over-year `diff`/`pct_change` (Absolute/Percentage). Optional "Compare with Births / Net Migration / Deaths" overlays (Growth+Absolute); in Total mode the Births and Deaths perspectives expose a one-way "Compare with Deaths"/"Compare with Births" overlay for natural-increase views; single-year selection renders a gauge `indicator` instead of a chart
  - *Migration* (`_render_migration_tab`): chart types Map / Line / Bar; "Compare by" Countries / Direction / Gender / Year; Map is a choropleth by country
  - *Births* (`_render_births_tab`): "Compare by" Gender / Mother Age / Education / Department / Municipality. Department supports a Colombia choropleth (geojson); Municipality drills down within a department; totals use a ranked horizontal bar
  - *Deaths* (`_render_deaths_tab`): "Compare by" Gender / Age Group / Area / Department / Cause (Top 10) / Cause (Compare). Gender comes from `total.csv`; Age Group and Area come from `area_grupo_edad.csv` (2008+) — Age Group adds Gender (Total/Men/Women) and Area sub-filters, Area adds an Age-group filter; Department, both Cause modes, and the choropleth come from the dept×cause CSVs (2019+) behind an **Occurrence/Residence** "Place" selector. Department reuses `births_department_data`/`births_geo_trend` (dept frame is `TOTAL NACIONAL`-filtered and `Fecha`→`year`-renamed); Cause (Top 10) is a ranked bar of the top 10 causes for the active filters; Cause (Compare) charts ≤5 user-picked causes
- `pages/helpers/macro/macro_functions.py` — data cleaning (`clean_gdp`, `clean_annual_growth`) and Streamlit sidebar/filter logic (`generalities_spend_product`); CPI builders (`build_yearly_table`, `cpi_sidebar_filters`, `build_cpi_series`, `build_comparison_series`); migration pivots (`build_migration_map_data`, `migration_countries_pivot`, `migration_single_pivot`, `migration_year_pivot`); births pivots (`births_national_series`, `births_gender_pivot`, `births_age_pivot`, `births_education_pivot`, `births_department_data`, `births_geo_trend`); deaths pivots (`deaths_national_series`, `deaths_gender_pivot`, `deaths_area_pivot`, `deaths_age_pivot`, `deaths_top_causes`, `deaths_cause_pivot`, `deaths_cause_names` — dept-based ones reuse the births geo helpers)
- `pages/helpers/macro/macro_charts.py` — Plotly chart builders (`line_chart`, `bar_chart` — generic, take `info` list for titles/axis labels and an optional `highlight` arg that greys non-selected series; both cap at the **first 6 series** (with a warning) when given a wider DataFrame; `gdp_growth` — single-year selection renders gauge indicator instead of line chart; `indicator` — gauge; `choropleth_map` — country-name choropleth; `colombia_choropleth` — geojson choropleth keyed on DANE dept code; `ranked_bar_chart` — horizontal)
- `generalities/` — dicts mapping Spanish column names (from source CSVs) to English display labels; `dictionaries.py` has filter UI dicts (presidents, months); `inflation.py` has CPI perspective name mappings (Spanish CSV column → English label); `migration.py` has `COUNTRY_EN` (Spanish→English country names), `COL_MAP` ((direction, metric)→CSV column), `METRIC_LABEL`, `VIEW`; `births.py` has `BIRTHS_PATHS`, `BIRTHS_COMPARE`, `GENDER_EN`, `AGE_EN`, `EDU_EN`, plus `DEPT_GEOJSON_PATH`/`DEPT_FEATURE_KEY`; `deaths.py` has `DEATHS_PATHS`, `DEATHS_COMPARE`, `GENDER_EN`, `AREA_EN`, `AGE_EN` (both Spanish typo spellings map to one label), `CAUSE_EN` (keyed on `_norm`'d accent-stripped Spanish cause → English; collapses accent-variant duplicate causes), reusing births' `DEPT_GEOJSON_PATH`/`DEPT_FEATURE_KEY`; `function.py` has shared helpers — path/loading (`BASE_DIR`, `load_csv`/`load_geojson` both `@st.cache_data`, `to_datatime`), lookups (`get_valid_presidents`, `find_key_by_value`), president filtering (`president_multiselect`, `reshape_by_presidents`, `show_all_years`)
- `clean_data/` — one-off scripts for transforming raw Excel/CSV source files into the cleaned CSVs in `data/`; `clean_borns.py` decrypts password-protected `.xls` workbooks via LibreOffice (`soffice --headless --convert-to xlsx`); `clean_deaths.py` parses DANE death workbooks positionally (with a header guard `check_groups`) into the four `data/dane/deaths/` CSVs

**Data directory layout:**
```
data/
  dane/GDP/{spend,production,income}/   ← DANE quarterly GDP tables (columns = year-quarter, rows = concepts)
  dane/borns/                           ← births_total.csv + births_by_{department,municipality,mother_age,education}.csv (DANE)
  dane/deaths/                          ← total.csv + area_grupo_edad.csv (2008+) + departamento_{muerte,residencia}.csv (dept×cause, 2019+) (DANE)
  dane/geo/                             ← colombia_departments.geojson (dept choropleth)
  banco_republica/GDP/                  ← annual_growth.csv, quarter_growth.csv
  banco_republica/CPI/                  ← inflacion_15.csv + spend_category/ by city
  banco_republica/population/           ← population.csv (annual, Fecha = 31/12, Población)
  banco_republica/unemployment/
  world_bank/net_migration.csv          ← annual net migration
  datos_abiertos/migration.csv          ← Migración Colombia inbound/outbound by country
  original/dane/borns/*.xls(x)          ← raw DANE births workbooks (cleaned by clean_data/clean_borns.py)
  original/dane/deaths/*.xls(x)         ← raw DANE deaths workbooks by year (cleaned by clean_data/clean_deaths.py)
```

**Translation pattern:** Each GDP perspective has a matching dict in `generalities/gdp_spend.py` (or `gdp_production.py`, `gdp_income.py`). The dict key is the Spanish `Concepto` value in the CSV; the value is the English label shown in the UI. `gdp.py` dynamically resolves which dict to use via `getattr(t, f"spend_{file}_terms", None)`.

**President filter:** `presidents` dict maps name → list of years (integers); `get_valid_presidents` intersects the data's year range with these. The UI is now a multiselect (`president_multiselect`): selecting one president filters years to `presidents[name]`; selecting two or more enters **comparison mode**, where `reshape_by_presidents` (`generalities/function.py`) re-indexes data to a relative "Term Year" axis and emits one column per variable×president. Used across GDP, CPI, and Population (National/Migration/Births/Deaths).
