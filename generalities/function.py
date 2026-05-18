import pandas as pd
import streamlit as st
from generalities.dictionaries import presidents

def get_valid_presidents(tmp_years: dict) -> list:
    return [
        name for name, pres_years in presidents.items()
        if not set(pres_years).isdisjoint(tmp_years)
    ]

def find_key_by_value(d: dict, value: str):
    return next((k for k, v in d.items() if v == value), None)

def show_all_years(df: pd.DataFrame|pd.Series, president) -> pd.DataFrame | pd.Series:
    with st.sidebar:
        show_all = st.checkbox("Show all years", value=False)

    if not show_all and not president:
        df = df[df.index >= 2000]

    return df

def to_datatime(df: pd.DataFrame, dayfirst: bool) -> pd.DataFrame | pd.Series:
    df_local = df.copy()
    df_local["Fecha"] = pd.to_datetime(df_local["Fecha"], dayfirst=dayfirst)
    df_local = df_local.set_index("Fecha").sort_index(ascending=True)

    return df_local
