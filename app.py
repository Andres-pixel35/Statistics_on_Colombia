import streamlit as st
from generalities.function import BASE_DIR

st.set_page_config(layout="wide", page_title="Homepage", initial_sidebar_state="expanded")
st.logo(str(BASE_DIR / "logo/logo.png"), size="large")

st.image(str(BASE_DIR / "logo/logo_text.png"), width=300)

st.info("This web is thought to be displayed in a computer.")
st.info("Go to the sidebar.")
st.write("SOON")


