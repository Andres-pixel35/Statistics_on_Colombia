import streamlit as st
import pandas as pd

def render_cpi(cpi_df: pd.DataFrame) -> None:
    cpi_local = cpi_df.copy()

    st.title("CPI")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.selectbox("Method:", ["Headline Inflation", "Core Inflation (excluding 15 items)"])

    if method == "Headline Inflation":
        with col2:
            perspective = st.selectbox("Perspective:", ["Annual", "Monthly", "Year-to-date"])

        #if perspective == "Annual":
            #with col3:
                #month = st.selectbox("Month:", )
            
