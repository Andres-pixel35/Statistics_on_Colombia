from generalities.function import BASE_DIR
from generalities.demography_generalities.births import DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY  # noqa: F401

POVERTY_BASE = BASE_DIR / "data/dane/poverty"
VIEW = ["Indicators", "Household Profile", "By Sex"]

# paths keys ARE the "Type" selectbox options -> Gini/Income collapse to one option
METRICS = {
    "Poverty Incidence": {"paths": {"Monetary": "pobreza_monetaria/incidencia.csv",
                                    "Extreme":  "pobreza_extrema/incidencia.csv"},
                          "unit": "% of population", "fmt": ",.1f"},
    "People in Poverty": {"paths": {"Monetary": "pobreza_monetaria/personas.csv",
                                    "Extreme":  "pobreza_extrema/personas.csv"},
                          "unit": "Millions of people", "fmt": ",.2f", "scale": 1000},
    "Poverty Gap":       {"paths": {"Monetary": "brecha/brecha_monetaria.csv",
                                    "Extreme":  "brecha/brecha_extrema.csv"},
                          "unit": "%", "fmt": ",.1f"},
    "Poverty Severity":  {"paths": {"Monetary": "severidad/severidad_monetaria.csv",
                                    "Extreme":  "severidad/severidad_extrema.csv"},
                          "unit": "%", "fmt": ",.1f"},
    "Poverty Line":      {"paths": {"Monetary": "lineas_pobreza/linea_pobreza.csv",
                                    "Extreme":  "lineas_pobreza/linea_pobreza_extrema.csv"},
                          "unit": "COP per person per month", "fmt": ",.0f"},
    "Gini Coefficient":  {"paths": {"Monetary": "gini/gini.csv"},
                          "unit": "Gini (0–1)", "fmt": ",.3f"},
    "Per-capita Income": {"paths": {"Monetary": "ingreso_percapita/ingreso_percapita.csv"},
                          "unit": "COP per month", "fmt": ",.0f"},
}

DEFAULT_DOMAIN = "Nacional"
AGGREGATE_DOMAINS = ["Nacional", "Cabeceras", "Centros poblados y rural disperso",
                     "13 ciudades y A.M.", "Otras cabeceras"]
SEXO_EN = {"Hombre": "Men", "Mujer": "Women"}

# Only the 5 aggregates need translating; the other domains are city names, whose
# "… A.M." (área metropolitana) suffix becomes "… M.A." via domain_label().
DOMAIN_EN = {
    "Nacional": "National",
    "Cabeceras": "Urban areas",
    "Centros poblados y rural disperso": "Towns and dispersed rural areas",
    "13 ciudades y A.M.": "13 cities and M.A.",
    "Otras cabeceras": "Other urban areas",
}


def domain_label(domain: str) -> str:
    return DOMAIN_EN.get(domain, domain.replace(" A.M.", " M.A."))

# Capital city (as spelled in the CSV headers) -> DANE department code. "… A.M." columns
# are excluded: only plain city names key the map.
CITY_DPTO = {
    "Armenia": "63", "Barranquilla": "08", "Bogotá": "11", "Bucaramanga": "68",
    "Cali": "76", "Cartagena": "13", "Cúcuta": "54", "Florencia": "18",
    "Ibagué": "73", "Manizales": "17", "Medellín": "05", "Montería": "23",
    "Neiva": "41", "Pasto": "52", "Pereira": "66", "Popayán": "19",
    "Quibdó": "27", "Riohacha": "44", "Santa Marta": "47", "Sincelejo": "70",
    "Tunja": "15", "Valledupar": "20", "Villavicencio": "50",
}

PROFILE_FILES = {"Household Head": "perfil_jefe", "Household": "perfil_hogar"}
PROFILE_TYPES = {"Monetary": "incidencia_pobreza.csv",
                 "Extreme": "incidencia_pobreza_extrema.csv"}

GRUPO_EN = {
    "Total": "Total",
    "Sexo": "Sex",
    "Edad": "Age",
    "Nivel Educativo": "Education Level",
    "Situación laboral": "Employment Status",
    "Posición Ocupacional": "Occupational Position",
    "Cotización a pensión": "Pension Contribution",
    "Número de niños menores de 12 años": "Children under 12",
    "Número de ocupados en el hogar": "Employed Members",
    "Tamaño del hogar": "Household Size",
}

CATEGORIA_EN = {
    "Hombre": "Men",
    "Mujer": "Women",
    "Hasta 25 años": "Up to 25",
    "Entre 26 y 35 años": "26 to 35",
    "Entre 36 y 45 años": "36 to 45",
    "Entre 46 y 55 años": "46 to 55",
    "Entre 56 y 65 años": "56 to 65",
    "Mayor a 65 años": "Over 65",
    "Ninguno o primaria": "None or primary",
    "Secundaria": "Secondary",
    "Técnica o Tecnológica": "Technical",
    "Universidad o posgrado": "University or postgraduate",
    "Ocupados": "Employed",
    "Desocupados": "Unemployed",
    "Población fuera de la fuerza de trabajo": "Outside the labor force",
    "Asalariados": "Wage earners",
    "Patronos y Cuenta Propia": "Employers and self-employed",
    "Afiliado": "Contributing",
    "No Afiliado": "Not contributing",
    "No tiene niños": "No children",
    "Un niño": "One child",
    "Dos niños": "Two children",
    "Tres o más niños": "Three or more children",
    "Ningún ocupado": "No employed member",
    "Un ocupado": "One employed member",
    "Dos o más ocupados": "Two or more employed members",
    "Una persona": "One person",
    "Dos personas": "Two people",
    "Tres personas": "Three people",
    "Cuatro personas o más": "Four or more people",
}
