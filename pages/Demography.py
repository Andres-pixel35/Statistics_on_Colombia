import streamlit as st
from pages.tabs.demography import national, department, municipality, migration, births, deaths
from generalities.function import load_csv, BASE_DIR
from generalities.demography_generalities.migration import VIEW

st.set_page_config(layout="wide", page_title="Demography")

path_population = BASE_DIR / "data/dane/population/nacional.csv"

population_df = load_csv(path_population)

st.title("Statistics on Colombia")

with st.sidebar:
    view = st.radio("View:", VIEW)

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
