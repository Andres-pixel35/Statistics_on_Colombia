import streamlit as st
from generalities.function import BASE_DIR
from generalities.i18n import t, language_selector

st.set_page_config(layout="wide")
st.logo(str(BASE_DIR / "logo/logo.svg"), size="medium")
language_selector()

pg = st.navigation([
    st.Page("app_pages/homepage.py", title=t("Homepage"), icon=":material/home:", default=True),
    st.Page("app_pages/Macroeconomics.py", title=t("Macroeconomics"), icon=":material/monitoring:"),
    st.Page("app_pages/Demography.py", title=t("Demography"), icon=":material/groups:"),
    st.Page("app_pages/Miscellaneous.py", title=t("Miscellaneous"), icon=":material/tune:"),
    st.Page("app_pages/Poverty.py", title=t("Poverty"), icon=":material/volunteer_activism:"),
])
pg.run()
