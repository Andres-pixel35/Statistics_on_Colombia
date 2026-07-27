import streamlit as st
from pages.tabs.poverty import indicators, profile, by_sex
from generalities.function import BASE_DIR
from generalities.poverty_generalities.poverty import VIEW

st.set_page_config(layout="wide", page_title="Poverty")
st.logo(str(BASE_DIR / "logo/logo.svg"), size="medium")

st.image(str(BASE_DIR / "logo/logo_text.svg"), width=300)

with st.sidebar:
    view = st.radio("View:", VIEW)

if view == "Indicators":
    indicators.render_indicators()
elif view == "Household Profile":
    profile.render_profile()
else:
    by_sex.render_by_sex()
