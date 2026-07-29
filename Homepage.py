import pandas as pd
import streamlit as st
from generalities.dictionaries import months
from generalities.function import BASE_DIR, load_csv, to_datatime
from pages.helpers.macro.gdp_functions import load_banco_annual, variable_growth, gdp_per_capita_growth
from pages.helpers.macro.job_market_functions import load_desestacionalizado_unemployment
from pages.helpers.macro.ise_functions import ise_long
from pages.helpers.macro import debt_functions as dbf
from pages.helpers.macro import productivity_functions as pf
from pages.helpers.demography import population_functions as pop
from pages.helpers.demography import births_functions as bir
from pages.helpers.demography import deaths_functions as dth
from generalities.macro_generalities import debt as dg
from generalities.demography_generalities.population import POP_PATHS, PREV_YEAR
from generalities.demography_generalities.births import BIRTHS_PATHS
from generalities.demography_generalities.deaths import DEATHS_PATHS
from generalities.poverty_generalities import poverty as pv
from pages.helpers import kpi_cards as kc
from pages.helpers.miscellaneous import rates_functions as rf

st.set_page_config(layout="wide", page_title="Homepage", initial_sidebar_state="collapsed")
st.logo(str(BASE_DIR / "logo/logo.svg"), size="medium")

st.markdown(
    """<style>
    .block-container {max-width: 1300px; margin: auto;}
    [data-testid="stVerticalBlockBorderWrapper"] {background-color: rgba(128,128,128,0.05);}
    </style>""",
    unsafe_allow_html=True,
)

header_left, header_right = st.columns([3, 1])
with header_left:
    st.image(str(BASE_DIR / "logo/logo_text.svg"), width=300)

last_updated_dates = []

# --- GDP ---
real_annual = load_banco_annual(BASE_DIR / "data/banco_republica/GDP/real_annual.csv").set_index("Fecha")
latest_year = real_annual.index[-1]
annual_growth = float(real_annual.loc[latest_year, "Crecimiento"])

quarter_growth_series = variable_growth(
    load_csv(BASE_DIR / "data/dane/GDP/spend/summarize.csv", dtype=str),
    "Producto Interno Bruto",
    "quarter",
)
quarter_growth = quarter_growth_series.iloc[-1]
gdp_year, roman_quarter = quarter_growth["Fecha"].split("-")
gdp_quarter = {"I": 1, "II": 2, "III": 3, "IV": 4}[roman_quarter]

gdp_cfg = {
    "title": "Real GDP Annual Growth",
    "value": f"{annual_growth:.2f}%",
    "delta_text": f"Q{gdp_quarter} {gdp_year}: {quarter_growth['Growth']:.2f}%",
    "delta_good": quarter_growth["Growth"] >= 0,
    "metadata": f"{latest_year} · Annual, vs prior quarter",
    "accent": "#4B7EC0",
    "spark": quarter_growth_series["Growth"].tail(12),
}

# --- CPI ---
cpi = to_datatime(load_csv(BASE_DIR / "data/banco_republica/CPI/city/Total_Nacional.csv"), dayfirst=False)
cpi_date = cpi.index[-1]
cpi_value = cpi.loc[cpi_date, "Variación anual (%)"]
year_ago_date = cpi_date - pd.DateOffset(years=1)
cpi_delta, cpi_delta_good = None, None
if year_ago_date in cpi.index:
    delta_pp = cpi_value - cpi.loc[year_ago_date, "Variación anual (%)"]
    cpi_delta = f"{delta_pp:+.2f} pp vs {year_ago_date:%b %Y}"
    cpi_delta_good = delta_pp < 0
last_updated_dates.append(cpi_date)

cpi_cfg = {
    "title": "Annual Inflation",
    "value": f"{cpi_value:.2f}%",
    "delta_text": cpi_delta,
    "delta_good": cpi_delta_good,
    "metadata": f"{cpi_date:%B %Y} · Monthly, YoY",
    "accent": "#f97316",
    "spark": cpi["Variación anual (%)"].tail(12),
}

# --- Unemployment ---
unemployment = to_datatime(load_csv(BASE_DIR / "data/banco_republica/unemployment/unemployment.csv"), dayfirst=True)
unemp_date = unemployment.index[-1]
unemp_value = unemployment.loc[unemp_date, "Tasa de desempleo"]
year_ago_date = unemp_date - pd.DateOffset(years=1)
unemp_delta, unemp_delta_good = None, None
if year_ago_date in unemployment.index:
    delta_pp = unemp_value - unemployment.loc[year_ago_date, "Tasa de desempleo"]
    unemp_delta = f"{delta_pp:+.2f} pp vs {year_ago_date:%b %Y}"
    unemp_delta_good = delta_pp < 0
last_updated_dates.append(unemp_date)

unemployment_cfg = {
    "title": "Unemployment Rate",
    "value": f"{unemp_value:.2f}%",
    "delta_text": unemp_delta,
    "delta_good": unemp_delta_good,
    "metadata": f"{unemp_date:%B %Y} · Monthly, YoY",
    "accent": "#16a34a",
    "spark": unemployment["Tasa de desempleo"].tail(12),
}

# --- ISE ---
ise_total = ise_long(load_csv(BASE_DIR / "data/dane/ISE/original/tasas_anuales.csv"))
ise_total = ise_total[ise_total["Concepto"] == "Indicador de Seguimiento a la Economía"].sort_values(["Fecha", "Mes"])
ise_latest = ise_total.iloc[-1]
ise_prev_year_row = ise_total[(ise_total["Fecha"] == ise_latest["Fecha"] - 1) & (ise_total["Mes"] == ise_latest["Mes"])]
ise_delta, ise_delta_good = None, None
if not ise_prev_year_row.empty:
    delta_pp = ise_latest["Valor"] - ise_prev_year_row.iloc[0]["Valor"]
    ise_delta = f"{delta_pp:+.2f} pp vs {months[ise_latest['Mes']]} {ise_latest['Fecha'] - 1}"
    ise_delta_good = delta_pp >= 0

ise_cfg = {
    "title": "ISE Annual Growth",
    "value": f"{ise_latest['Valor']:.2f}%",
    "delta_text": ise_delta,
    "delta_good": ise_delta_good,
    "metadata": f"{months[ise_latest['Mes']]} {ise_latest['Fecha']} · Annual, YoY",
    "accent": "#4f46e5",
    "spark": ise_total["Valor"].tail(12),
}

# --- Exchange Rate ---
trm = to_datatime(load_csv(BASE_DIR / "data/banco_republica/miscellaneous/trm.csv"), dayfirst=False)
trm_date = trm.index[-1]
trm_value = trm.loc[trm_date, "trm"]
month_ago_value = trm["trm"].asof(trm_date - pd.DateOffset(months=1))
trm_delta = None
if pd.notna(month_ago_value):
    trm_delta = f"{trm_value - month_ago_value:+.2f} COP vs 1 month ago"
last_updated_dates.append(trm_date)

exchange_rate_cfg = {
    "title": "Exchange Rate",
    "value": f"{trm_value:,.2f} COP",
    "delta_text": trm_delta,
    "delta_good": None,
    "metadata": f"{trm_date:%d %b %Y} · Daily",
    "accent": "#06b6d4",
    "spark": trm["trm"].tail(12),
}

# --- Monetary Policy Rate ---
policy_rate = to_datatime(load_csv(BASE_DIR / "data/banco_republica/miscellaneous/tasa_monetaria.csv"), dayfirst=True)
rate = policy_rate["Tasa (%)"]
changes = rate[rate != rate.shift()]
policy_date, policy_value = changes.index[-1], changes.iloc[-1]
prev_date, prev_value = changes.index[-2], changes.iloc[-2]
last_updated_dates.append(policy_date)

policy_rate_cfg = {
    "title": "Monetary Policy Rate",
    "value": f"{policy_value:.2f}%",
    "delta_text": f"{policy_value - prev_value:+.2f} pts vs {prev_date:%d %b %Y}",
    "delta_good": None,
    "metadata": f"{policy_date:%d %b %Y} · Rate changes",
    "accent": "#9333ea",
    "spark": changes.tail(12),
}

# --- Misery Index ---
lending_df = to_datatime(load_csv(BASE_DIR / "data/banco_republica/miscellaneous/tasa_colocacion.csv"), dayfirst=True)
misery_gdp_growth_by_year = gdp_per_capita_growth(BASE_DIR / "data/banco_republica/GDP/real_annual.csv")
misery_unemployment = load_desestacionalizado_unemployment(
    str(BASE_DIR / "data/dane/job_market/desestacionalizado/total.csv")
)["Tasa de desempleo"]
misery_series = rf.misery_index_annual(
    misery_unemployment, cpi["Variación anual (%)"], lending_df["Tasa (%)"], misery_gdp_growth_by_year,
)["Misery Index"]
misery_year = misery_series.index[-1]
misery_value = misery_series.iloc[-1]
misery_delta, misery_delta_good = None, None
if len(misery_series) > 1:
    delta = misery_value - misery_series.iloc[-2]
    misery_delta = f"{delta:+.2f} pts vs {misery_series.index[-2]}"
    misery_delta_good = delta < 0

misery_cfg = {
    "title": "Misery Index",
    "value": f"{misery_value:.2f}",
    "delta_text": misery_delta,
    "delta_good": misery_delta_good,
    "metadata": f"{misery_year} · Annual, 2× Seasonally Adj. Unemployment + Inflation + Lending Rate − GDP per-capita growth",
    "accent": "#ea580c",
    "spark": misery_series.tail(12),
}

# --- Public Debt (% of GDP) ---
gdp_nominal = dbf.gdp_millions(dg.NOMINAL_ANNUAL_PATH)
saldos = to_datatime(load_csv(BASE_DIR / "data/hacienda/debt/saldos/saldos.csv"), dayfirst=False)
latest_gdp_year = max(y for y in gdp_nominal.index.astype(int) if y in saldos.index.year)
debt_latest_row = saldos[saldos.index.year == latest_gdp_year].iloc[-1]
debt_pct = dbf.to_gdp_pct(debt_latest_row["Deuda total"], gdp_nominal, year=latest_gdp_year)

debt_delta, debt_delta_good = None, None
prev_year = latest_gdp_year - 1
if str(prev_year) in gdp_nominal.index:
    prev_rows = saldos[(saldos.index.year == prev_year) & (saldos.index.month == debt_latest_row.name.month)]
    if not prev_rows.empty:
        prev_pct = dbf.to_gdp_pct(prev_rows.iloc[-1]["Deuda total"], gdp_nominal, year=prev_year)
        debt_delta = f"{debt_pct - prev_pct:+.2f} pp vs {debt_latest_row.name:%b} {prev_year}"
        debt_delta_good = debt_pct < prev_pct
last_updated_dates.append(debt_latest_row.name)

debt_years = saldos.index.year.astype(str)
debt_pct_trend = (saldos["Deuda total"] / debt_years.map(gdp_nominal).astype(float) * 100).dropna()

debt_gdp_cfg = {
    "title": "Public Debt (% of GDP)",
    "value": f"{debt_pct:.2f}%",
    "delta_text": debt_delta,
    "delta_good": debt_delta_good,
    "metadata": f"{debt_latest_row.name:%b %Y} · Monthly, YoY",
    "accent": "#dc2626",
    "spark": debt_pct_trend.tail(12),
}

# --- Productivity ---
productivity_df = load_csv(BASE_DIR / "data/dane/productivity/laboral/por_persona_empleada.csv")
productivity_series = pf.productivity_pivot(
    productivity_df, {"Labor productivity per employed person": "productividad laboral por persona empleada (%)"},
)["Labor productivity per employed person"]
prod_year = productivity_series.index[-1]
prod_value = productivity_series.iloc[-1]
prod_delta, prod_delta_good = None, None
if len(productivity_series) > 1:
    delta_pp = prod_value - productivity_series.iloc[-2]
    prod_delta = f"{delta_pp:+.2f} pp vs {productivity_series.index[-2]}"
    prod_delta_good = delta_pp >= 0

productivity_cfg = {
    "title": "Labor Productivity Growth",
    "value": f"{prod_value:.2f}%",
    "delta_text": prod_delta,
    "delta_good": prod_delta_good,
    "metadata": f"{prod_year} · Annual, per employed person",
    "accent": "#0d9488",
    "spark": productivity_series.tail(12),
}

# --- Minimum Wage ---
wage_df = load_csv(BASE_DIR / "data/banco_republica/miscellaneous/salario_minimo.csv")
wage_series = wage_df.set_index("Fecha")["Salario"]
wage_year = wage_series.index[-1]
wage_value = wage_series.iloc[-1]
wage_delta, wage_delta_good = None, None
if len(wage_series) > 1:
    growth_pct = (wage_value / wage_series.iloc[-2] - 1) * 100
    wage_delta = f"{growth_pct:+.2f}% vs {wage_series.index[-2]}"
    wage_delta_good = growth_pct >= 0

minimum_wage_cfg = {
    "title": "Minimum Wage",
    "value": f"{wage_value:,.0f} COP",
    "delta_text": wage_delta,
    "delta_good": wage_delta_good,
    "metadata": f"{wage_year} · Annual",
    "accent": "#d97706",
    "spark": wage_series.tail(12),
}

# --- Debt Indicators (Duration / Average Life / Average Coupon) ---
indicadores = to_datatime(load_csv(dg.INDICADORES_PATH), dayfirst=False)


def _indicator_cfg(title, column, accent, value_fmt):
    series = indicadores[column].dropna()
    date = series.index[-1]
    value = series.iloc[-1]
    delta_text, delta_good = None, None
    year_ago = date - pd.DateOffset(years=1)
    if year_ago in series.index:
        delta = value - series.loc[year_ago]
        delta_text = f"{delta:+.2f} vs {year_ago:%b %Y}"
        delta_good = None
    return {
        "title": title,
        "value": value_fmt.format(value),
        "delta_text": delta_text,
        "delta_good": delta_good,
        "metadata": f"{date:%b %Y} · Monthly, YoY",
        "accent": accent,
        "spark": series.tail(12),
    }


debt_duration_cfg = _indicator_cfg("Debt Duration", "Duración - Deuda total", "#dc2626", "{:.2f} yrs")
debt_avg_life_cfg = _indicator_cfg("Debt Average Life", "Vida media - Deuda total", "#dc2626", "{:.2f} yrs")
debt_avg_coupon_cfg = _indicator_cfg("Debt Average Coupon", "Cupón promedio (%) - Deuda Total", "#dc2626", "{:.2f}%")

# --- Poverty & Inequality ---
def _poverty_cfg(cfg):
    """cfg: title, relpath, accent, value_fmt, delta_fmt. All three poverty/inequality
    measures are rates where lower is better, reported as an absolute delta."""
    series = load_csv(pv.POVERTY_BASE / cfg["relpath"]).set_index("Fecha")["Nacional"].sort_index()
    value = series.iloc[-1]
    delta_text, delta_good = None, None
    if len(series) > 1:
        delta = value - series.iloc[-2]
        delta_text = cfg["delta_fmt"].format(delta) + f" vs {series.index[-2]}"
        delta_good = delta <= 0
    return {
        "title": cfg["title"],
        "value": cfg["value_fmt"].format(value),
        "delta_text": delta_text,
        "delta_good": delta_good,
        "metadata": f"{series.index[-1]} · Annual",
        "accent": cfg["accent"],
        "spark": series.tail(12),
    }


poverty_cfg = _poverty_cfg({"title": "Monetary Poverty", "accent": "#7c3aed",
                            "relpath": "pobreza_monetaria/incidencia.csv",
                            "value_fmt": "{:.1f}%", "delta_fmt": "{:+.1f}pp"})
extreme_poverty_cfg = _poverty_cfg({"title": "Extreme Poverty", "accent": "#7c3aed",
                                    "relpath": "pobreza_extrema/incidencia.csv",
                                    "value_fmt": "{:.1f}%", "delta_fmt": "{:+.1f}pp"})
gini_cfg = _poverty_cfg({"title": "Gini Coefficient", "accent": "#7c3aed",
                         "relpath": "gini/gini.csv",
                         "value_fmt": "{:.3f}", "delta_fmt": "{:+.3f}"})

# --- Population ---
national_pop_df = load_csv(POP_PATHS["national"])
population_series = pop.national_total_series(national_pop_df, gender="Total", age="All ages", cap=PREV_YEAR)
pop_year = population_series.index[-1]
pop_value = population_series.iloc[-1]
pop_delta, pop_delta_good = None, None
if len(population_series) > 1:
    growth_pct = (pop_value / population_series.iloc[-2] - 1) * 100
    pop_delta = f"{growth_pct:+.2f}% vs {population_series.index[-2]}"
    pop_delta_good = None

population_cfg = {
    "title": "National Population",
    "value": f"{pop_value:,.0f}",
    "delta_text": pop_delta,
    "delta_good": pop_delta_good,
    "metadata": f"{pop_year} · Annual",
    "accent": "#475569",
    "spark": population_series.tail(12),
}

# --- Births ---
births_series = bir.births_national_series(load_csv(BIRTHS_PATHS["total"]))
births_year = births_series.index[-1]
births_value = births_series.iloc[-1]
births_delta, births_delta_good = None, None
if len(births_series) > 1:
    growth_pct = (births_value / births_series.iloc[-2] - 1) * 100
    births_delta = f"{growth_pct:+.2f}% vs {births_series.index[-2]}"
    births_delta_good = growth_pct >= 0

births_cfg = {
    "title": "Births (National)",
    "value": f"{births_value:,.0f}",
    "delta_text": births_delta,
    "delta_good": births_delta_good,
    "metadata": f"{births_year} · Annual",
    "accent": "#db2777",
    "spark": births_series.tail(12),
}

# --- Deaths ---
deaths_series = dth.deaths_national_series(load_csv(DEATHS_PATHS["total"]))
deaths_year = deaths_series.index[-1]
deaths_value = deaths_series.iloc[-1]
deaths_delta, deaths_delta_good = None, None
if len(deaths_series) > 1:
    growth_pct = (deaths_value / deaths_series.iloc[-2] - 1) * 100
    deaths_delta = f"{growth_pct:+.2f}% vs {deaths_series.index[-2]}"
    deaths_delta_good = growth_pct <= 0

deaths_cfg = {
    "title": "Deaths (National)",
    "value": f"{deaths_value:,.0f}",
    "delta_text": deaths_delta,
    "delta_good": deaths_delta_good,
    "metadata": f"{deaths_year} · Annual",
    "accent": "#57534e",
    "spark": deaths_series.tail(12),
}

# --- Net Migration ---
migration_series = load_csv(BASE_DIR / "data/world_bank/net_migration.csv").set_index("Fecha")["Migration"].astype(int)
migration_year = migration_series.index[-1]
migration_value = migration_series.iloc[-1]
migration_delta, migration_delta_good = None, None
if len(migration_series) > 1:
    delta = migration_value - migration_series.iloc[-2]
    migration_delta = f"{delta:+,.0f} vs {migration_series.index[-2]}"
    migration_delta_good = None

net_migration_cfg = {
    "title": "Net Migration",
    "value": f"{migration_value:,.0f}",
    "delta_text": migration_delta,
    "delta_good": migration_delta_good,
    "metadata": f"{migration_year} · Annual",
    "accent": "#0284c7",
    "spark": migration_series.tail(12),
}

with header_right:
    st.markdown(
        f'<div style="text-align:right;color:#6b7280;font-size:13px;padding-top:20px;">'
        f'Last updated<br><strong>{max(last_updated_dates):%d %b %Y}</strong></div>',
        unsafe_allow_html=True,
    )

kc.render_section({
    "title": "Headline Indicators",
    "description": "The country's most important national indicators.",
    "cfgs": [gdp_cfg, cpi_cfg, unemployment_cfg, exchange_rate_cfg, poverty_cfg, misery_cfg],
    "expanded": True,
})

kc.render_section({
    "title": "Economic Indicators",
    "description": "Core measures of national economic performance.",
    "cfgs": [gdp_cfg, cpi_cfg, ise_cfg, policy_rate_cfg, productivity_cfg, minimum_wage_cfg],
    "page": "pages/Macroeconomics.py",
})

kc.render_section({
    "title": "Public Finance",
    "description": "Government debt levels and profile.",
    "cfgs": [debt_gdp_cfg, debt_duration_cfg, debt_avg_life_cfg, debt_avg_coupon_cfg],
    "page": "pages/Macroeconomics.py",
})

kc.render_section({
    "title": "Poverty & Inequality",
    "description": "Monetary poverty, extreme poverty and income distribution.",
    "cfgs": [poverty_cfg, extreme_poverty_cfg, gini_cfg],
    "page": "pages/Poverty.py",
})

kc.render_section({
    "title": "Demographics",
    "description": "Population size and its main drivers.",
    "cfgs": [population_cfg, births_cfg, deaths_cfg, net_migration_cfg],
    "page": "pages/Demography.py",
})
