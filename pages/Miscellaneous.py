import streamlit as st
from pages.tabs.miscellaneous import trm
from generalities.function import load_csv, BASE_DIR
from generalities.miscellaneous_generalities.trm import VIEW

st.set_page_config(layout="wide", page_title="Miscellaneous")

path_trm = BASE_DIR / "data/banco_republica/miscellaneous/trm.csv"

trm_df = load_csv(path_trm).rename(columns={"﻿Fecha": "Fecha"})

st.title("Statistics on Colombia")

with st.sidebar:
    view = st.radio("View:", VIEW)

if view == "TRM":
    trm.render_trm(trm_df)
