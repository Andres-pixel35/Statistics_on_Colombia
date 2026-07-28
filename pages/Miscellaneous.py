import streamlit as st
from pages.tabs.miscellaneous import exchange_rate, monetary_policy_rate, minimum_wage, lending_rate
from generalities.function import load_csv, BASE_DIR
from generalities.miscellaneous_generalities.rates import VIEW

st.set_page_config(layout="wide", page_title="Miscellaneous")
st.logo(str(BASE_DIR / "logo/logo.svg"), size="medium")

path_exchange_rate = BASE_DIR / "data/banco_republica/miscellaneous/trm.csv"
path_policy_rate = BASE_DIR / "data/banco_republica/miscellaneous/tasa_monetaria.csv"
path_minimum_wage = BASE_DIR / "data/banco_republica/miscellaneous/salario_minimo.csv"
path_lending_rate = BASE_DIR / "data/banco_republica/miscellaneous/tasa_colocacion.csv"

exchange_rate_df = load_csv(path_exchange_rate).rename(columns={"﻿Fecha": "Fecha"})
policy_rate_df = load_csv(path_policy_rate)
minimum_wage_df = load_csv(path_minimum_wage)
lending_rate_df = load_csv(path_lending_rate)

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
