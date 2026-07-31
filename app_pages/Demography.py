import streamlit as st
from app_pages.tabs.demography import national, department, municipality, migration, births, deaths
from generalities.function import load_csv, BASE_DIR
from generalities.demography_generalities.migration import VIEW
from generalities.i18n import t


path_population = BASE_DIR / "data/dane/population/nacional.csv"

population_df = load_csv(path_population)

st.image(str(BASE_DIR / "logo/logo_text.svg"), width=300)

with st.sidebar:
    view = st.radio(t("View:"), VIEW, format_func=t)

if view == "National":
    national.render_national(population_df)
elif view == "Department":
    department.render_department()
elif view == "Municipality":
    municipality.render_municipality()
elif view == "Migration":
    migration.render_migration()
elif view == "Births":
    births.render_births()
else:
    deaths.render_deaths()
