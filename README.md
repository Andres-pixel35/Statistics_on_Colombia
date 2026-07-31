<p align="center">
  <img src="logo/logo_text.svg" alt="Statistics on Colombia" width="400">
</p>

<p align="center">
  🇬🇧 English | <a href="README.es.md">🇪🇸 Español</a>
</p>

<a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue" alt="License: GPL-3.0"></a>

# Statistics on Colombia

**Statistics on Colombia** is an open-source project that presents Colombian
statistics in a simple, interactive way — GDP, inflation (CPI), the job
market, productivity, public debt and deficit, poverty, and demographics
(population, births, deaths, and migration), among others.

## Table of contents

- [Live demo](#live-demo)
- [Status](#status)
- [Features](#features)
  - [Homepage](#homepage)
  - [Macroeconomics](#macroeconomics)
  - [Demography](#demography)
  - [Miscellaneous](#miscellaneous)
  - [Poverty](#poverty)
  - [Across the whole app](#across-the-whole-app)
- [Tech stack](#tech-stack)
- [Data sources](#data-sources)
- [Project structure](#project-structure)
- [Data pipeline](#data-pipeline)
- [Download & installation](#download--installation)
- [License](#license)
- [Contact](#contact)

## Live demo

- **Web app:** https://statisticsoncolombia.streamlit.app/
- **Instagram:** https://www.instagram.com/statisticscolombia/

## Status

Feature development is **complete** as of July 2026. The data is kept up to
date with the latest releases from each source, and occasional fixes, new
datasets, or new features may still be added over time.

The app's interface is fully available in **Spanish**.

## Features

### Homepage

A KPI-card dashboard with the latest value, change versus the previous
period, and a sparkline trend for every headline series — grouped into
Headline Indicators, Economic Indicators, Public Finance, Poverty &
Inequality, and Demographics — with quick links to each full page.

### Macroeconomics

- **GDP** — levels and growth by spending, production, and income
  perspectives; annual, annual-per-quarter, and quarter-over-quarter growth;
  per-capita view; in-year (quarterly) view.
- **CPI (inflation)** — national, per-city, and per-spend-category series
  from the 15- and 20-core-item baskets.
- **Job Market** — unemployment (original and seasonally adjusted), labor
  force, departments and regions (with choropleth maps), employment
  formality, and child labor.
- **Productivity** — DANE total-factor-productivity tables: by employed
  person, by hour worked, value added, production, and by economic activity.
- **Debt** — central government gross debt: balances (also as % of GDP or of
  total debt), sources, rates, currency, maturity profile, and indicators.
- **Deficit** — fiscal balance at annual, quarterly, and monthly frequency,
  in COP or as % of GDP, with a revenue-vs-spending comparison.
- **ISE** — the monthly economic activity indicator (original and seasonally
  adjusted), by category and activity branch.

### Demography

- **Population** — national, by department, and by municipality; population
  pyramids; official projections shown as dashed lines; birth and death
  rates.
- **Migration** — net migration and inbound/outbound travelers by country,
  direction, and gender, including a world map.
- **Births** — by gender, mother's age (with a births pyramid), education,
  department, and municipality.
- **Deaths** — by gender, age group (with a deaths pyramid), area, cause of
  death, department, and municipality, with optional rates per 1,000
  population.

### Miscellaneous

- **Exchange rate** (COP/USD), **monetary policy rate**, **minimum wage**
  (nominal, real, or in USD), **lending rate**, and the **misery index**
  (Hanke formula).

### Poverty

- **Indicators** — monetary and extreme poverty, poverty gap, severity,
  poverty lines, Gini, and per-capita income, by national aggregates and
  capital cities, including a choropleth map.
- **Household profile** — poverty by household and household-head
  characteristics.
- **By sex** — poverty indicators for men and women across domains.

### Across the whole app

- Compare any series across **presidential terms** with a relative
  "term year" axis.
- **Light/dark theme** and **mobile-friendly** charts.
- Department and region **choropleth maps** of Colombia.

## Tech stack

- **Streamlit** — hosts the app and renders the interactive interface
- **Python** + **pandas** — data cleaning and manipulation
- **Plotly** — charting

## Data sources

- **DANE** — Colombia's National Administrative Department of Statistics
- **Banco de la República** — Colombia's central bank
- **Ministerio de Hacienda** — public debt and fiscal balance
- **World Bank** — net migration
- **Migración Colombia / Datos Abiertos** — inbound/outbound travelers, via
  Colombia's open-data platform

## Project structure

```
streamlit_app.py      ← entry point
app_pages/            ← one script per page + homepage
  tabs/               ← per-page view logic (macroeconomics, demography, …)
  helpers/            ← data cleaning/pivoting + Plotly chart builders
generalities/         ← config dicts (Spanish→English labels, filters, paths)
clean_data/           ← scripts that turn the raw workbooks into clean CSVs
data/                 ← cleaned CSVs the app reads, grouped by source
  original/           ← raw workbooks as downloaded from each source
info_data/            ← notes on where each dataset comes from and how it's updated
logo/                 ← app logo (SVG)
```

## Data pipeline

Raw workbooks downloaded from each source live in `data/original/`. The
scripts in `clean_data/` transform them into the clean CSVs under `data/`
that the app reads:

- Most scripts are run from inside `clean_data/`
  (e.g. `cd clean_data && python clean_borns.py`).
- `clean_deaths.py` and `clean_job_market.py` are run as modules from the
  repo root (e.g. `python -m clean_data.clean_job_market`).

A few Banco de la República CSVs (exchange rate, policy rate, minimum wage,
annual GDP) are maintained by hand — the steps are documented in
`info_data/`.

## Download & installation

To download the project and run it locally:

```bash
# 1. Clone the repository (or use "Code → Download ZIP" on GitHub)
git clone https://github.com/Andres-pixel35/Statistics_on_Colombia.git
cd Statistics_on_Colombia

# 2. Install the dependencies
pip install -r requirements.txt
#    …or with conda:
# conda env create -f environment.yml

# 3. Run the app
streamlit run streamlit_app.py
```

The app opens in your browser at `http://localhost:8501`.

## License

This project is licensed under the **GNU General Public License v3.0
(GPL-3.0)** — see the [LICENSE](LICENSE) file for details.

## Contact

Questions, suggestions, or anything related to this project? Reach me at
**statistics-colombia@proton.me**.
