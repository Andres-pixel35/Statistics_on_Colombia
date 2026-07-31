import streamlit as st
from app_pages.tabs.poverty import indicators, profile, by_sex
from generalities.function import BASE_DIR
from generalities.poverty_generalities.poverty import VIEW
from generalities.i18n import t


st.image(str(BASE_DIR / "logo/logo_text.svg"), width=300)

with st.sidebar:
    view = st.radio(t("View:"), VIEW, format_func=t)

if view == "Indicators":
    indicators.render_indicators()
elif view == "Household Profile":
    profile.render_profile()
else:
    by_sex.render_by_sex()
