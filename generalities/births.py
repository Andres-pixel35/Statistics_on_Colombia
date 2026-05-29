from generalities.function import BASE_DIR

BIRTHS_PATHS = {
    "total":      BASE_DIR / "data/dane/borns/births_total.csv",
    "age":        BASE_DIR / "data/dane/borns/births_by_mother_age.csv",
    "education":  BASE_DIR / "data/dane/borns/births_by_education.csv",
    "department": BASE_DIR / "data/dane/borns/births_by_department.csv",
    "municipality": BASE_DIR / "data/dane/borns/births_by_municipality.csv",
}

DEPT_GEOJSON_PATH = BASE_DIR / "data/dane/geo/colombia_departments.geojson"
DEPT_FEATURE_KEY = "properties.DPTO"  # geojson property holding the 2-digit DANE code

BIRTHS_COMPARE = ["Gender", "Mother Age", "Education", "Department", "Municipality"]

GENDER_EN = {"hombres": "Boys", "mujeres": "Girls"}

AGE_EN = {
    "De 10-14 Años": "10–14",
    "De 15-19 Años": "15–19",
    "De 20-24 Años": "20–24",
    "De 25-29 Años": "25–29",
    "De 30-34 Años": "30–34",
    "De 35-39 Años": "35–39",
    "De 40-44 Años": "40–44",
    "De 45-49 Años": "45–49",
    "De 50-54 Años": "50–54",
    "Sin información": "Unknown",
}

EDU_EN = {
    "preescolar":                "Preschool",
    "basica_primaria":           "Primary",
    "basica_secundaria":         "Lower secondary",
    "media_academica_o_clasica": "Academic upper secondary",
    "media_tecnica":             "Technical upper secondary",
    "normalista":                "Teacher training",
    "tecnica_profesional":       "Technical",
    "tecnologica":               "Technological",
    "profesional":               "University",
    "especializacion":           "Specialization",
    "maestria":                  "Master's",
    "doctorado":                 "Doctorate",
    "ninguno":                   "None",
    "sin_informacion":           "Unknown",
}
