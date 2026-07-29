import streamlit as st
from pages.tabs.miscellaneous import exchange_rate, monetary_policy_rate, minimum_wage, lending_rate, misery_rate
from pages.helpers.macro.gdp_functions import gdp_per_capita_growth
from generalities.function import load_csv, BASE_DIR
from generalities.miscellaneous_generalities.rates import VIEW

st.set_page_config(layout="wide", page_title="Miscellaneous")
st.logo(str(BASE_DIR / "logo/logo.svg"), size="medium")

path_exchange_rate = BASE_DIR / "data/banco_republica/miscellaneous/trm.csv"
path_policy_rate = BASE_DIR / "data/banco_republica/miscellaneous/tasa_monetaria.csv"
path_minimum_wage = BASE_DIR / "data/banco_republica/miscellaneous/salario_minimo.csv"
path_lending_rate = BASE_DIR / "data/banco_republica/miscellaneous/tasa_colocacion.csv"
path_cpi = BASE_DIR / "data/banco_republica/CPI/city/Total_Nacional.csv"
path_real_annual = BASE_DIR / "data/banco_republica/GDP/real_annual.csv"

exchange_rate_df = load_csv(path_exchange_rate).rename(columns={"﻿Fecha": "Fecha"})
policy_rate_df = load_csv(path_policy_rate)
minimum_wage_df = load_csv(path_minimum_wage)
lending_rate_df = load_csv(path_lending_rate)
cpi_df = load_csv(path_cpi)
gdp_growth_by_year = gdp_per_capita_growth(path_real_annual)

st.image(str(BASE_DIR / "logo/logo_text.svg"), width=300)

with st.sidebar:
    view = st.radio("View:", VIEW)

if view == "Exchange Rate":
    exchange_rate.render_exchange_rate(exchange_rate_df)
elif view == "Monetary Policy Rate":
    monetary_policy_rate.render_monetary_policy_rate(policy_rate_df)
elif view == "Minimum Wage":
    minimum_wage.render_minimum_wage(minimum_wage_df, exchange_rate_df)
elif view == "Lending Rate":
    lending_rate.render_lending_rate(lending_rate_df)
elif view == "Misery Rate":
    misery_rate.render_misery_rate(cpi_df, lending_rate_df, gdp_growth_by_year)
