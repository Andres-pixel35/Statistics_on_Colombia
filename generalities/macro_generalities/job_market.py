GENDER = {
    "Total": "TOTAL NACIONAL",
    "Men": "HOMBRES",
    "Women": "MUJERES",
}

# Spanish rolling 3-month window -> English label (UI adds "Annual average" as default)
PERIOD_EN = {
    "Ene - Mar": "Jan - Mar",
    "Feb - Abr": "Feb - Apr",
    "Mar - May": "Mar - May",
    "Abr - Jun": "Apr - Jun",
    "May - Jul": "May - Jul",
    "Jun - Ago": "Jun - Aug",
    "Jul - Sep": "Jul - Sep",
    "Ago - Oct": "Aug - Oct",
    "Sep - Nov": "Sep - Nov",
    "Oct - Dic": "Oct - Dec",
    "Nov - Ene": "Nov - Jan",
    "Dic - Feb": "Dec - Feb",
}

# UI label -> filename stem ("Total" is the default)
LABOR_FORCE_FILES = {
    "Total": "total",
    "By Activity Branch": "ramas_actividad",
    "By Occupational Position": "posicion_ocupacional",
    "Out of Labor Force": "fuera_fuerza_trabajo",
}

# Departments dataset (data/dane/job_market/Departamentos/): gender = separate file
DEPT_GENDER_FILES = {"Total": "total", "Men": "hombres", "Women": "mujeres"}
DEPT_DEFAULT_CONCEPT = "Población desocupada"  # default concept for the Total table

# Activity-branch concepts (ramas_actividad.csv); strings must match the CSV verbatim
dept_ramas_terms = {
    "Total ocupados": "Total employed",
    "Agricultura, ganadería, caza, silvicultura y pesca": "Agriculture, livestock, hunting, forestry & fishing",
    "Explotación de minas y canteras": "Mining & quarrying",
    "Industrias manufactureras": "Manufacturing",
    "Suministro de electricidad, gas, agua y gestión de desechos": "Utilities (electricity, gas, water, waste)",
    "Construcción": "Construction",
    "Comercio y reparación de vehículos": "Commerce & vehicle repair",
    "Alojamiento y servicios de comida": "Accommodation & food services",
    "Transporte y almacenamiento": "Transport & storage",
    "Información y comunicaciones": "Information & communications",
    "Actividades financieras y de seguros": "Finance & insurance",
    "Actividades inmobiliarias": "Real estate",
    "Actividades profesionales, científicas, técnicas y de servicios administrativos": "Professional, scientific, technical & admin services",
    "Administración pública y defensa, educación y atención de la salud humana": "Public administration, education & health",
    "Actividades artísticas, entretenimiento, recreación y otras actividades de servicios": "Arts, entertainment & other services",
    "No informa": "Not reported",
}

PET_CONCEPT = "Población en edad de trabajar (PET)"

# total concept -> existing CSV rate concept; None means compute (value / PET * 100)
RATE_CONCEPTS = {
    "Población en edad de trabajar (PET)": "% población en edad de trabajar",
    "Fuerza de trabajo": "Tasa Global de Participación (TGP)",
    "Población ocupada": "Tasa de Ocupación (TO)",
    "Población desocupada": "Tasa de Desocupación (TD)",
    "Población subocupada": "Tasa de Subocupación (TS)",
    "Población fuera de la fuerza de trabajo": None,
    "Fuerza de trabajo potencial": None,
}

# Total-gender-only concepts that mirror a Men/Women concept; collapsed to the plain name
CONCEPT_ALIASES = {
    "Población ocupada Total Nacional": "Población ocupada",
    "Fuera de la fuerza de trabajo - Total Nacional": "Fuera de la fuerza de trabajo",
}

# Spanish Concepto -> English label. Rate concepts (%/Tasa) excluded from total_terms.
total_terms = {
    "Población en edad de trabajar (PET)": "Working-age population (WAP)",
    "Fuerza de trabajo": "Labor force",
    "Población ocupada": "Employed",
    "Población desocupada": "Unemployed",
    "Población subocupada": "Underemployed",
    "Población fuera de la fuerza de trabajo": "Outside the labor force",
    "Fuerza de trabajo potencial": "Potential labor force",
}

ramas_terms = {
    "Población ocupada": "Employed",
    "Agricultura, ganadería, caza, silvicultura y pesca": "Agriculture, livestock, hunting, forestry & fishing",
    "Explotación de minas y canteras": "Mining & quarrying",
    "Industrias manufactureras": "Manufacturing",
    "Suministro de electricidad gas, agua y gestión de desechos": "Utilities (electricity, gas, water, waste)",
    "Construcción": "Construction",
    "Comercio y reparación de vehículos": "Commerce & vehicle repair",
    "Alojamiento y servicios de comida": "Accommodation & food services",
    "Transporte y almacenamiento": "Transport & storage",
    "Información y comunicaciones": "Information & communications",
    "Actividades financieras y de seguros": "Finance & insurance",
    "Actividades inmobiliarias": "Real estate",
    "Actividades profesionales, científicas, técnicas y servicios administrativos": "Professional, scientific, technical & admin services",
    "Administración pública y defensa, educación y atención de la salud humana": "Public administration, education & health",
    "Actividades artísticas, entretenimiento, recreación y otras actividades de servicios": "Arts, entertainment & other services",
    "No informa": "Not reported",
}

posicion_terms = {
    "Población ocupada": "Employed",
    "Obrero, empleado particular": "Private employee",
    "Obrero, empleado del gobierno": "Government employee",
    "Empleado doméstico": "Domestic worker",
    "Trabajador por cuenta propia": "Self-employed",
    "Patrón o empleador": "Employer",
    "Trabajador familiar sin remuneración": "Unpaid family worker",
    "Jornalero o peón": "Day laborer",
    "Otro": "Other",
}

fuera_terms = {
    "Fuera de la fuerza de trabajo": "Outside labor force",
    "Estudiando": "Studying",
    "Oficios del Hogar": "Household chores",
    "Otros": "Other",
}

LABOR_FORCE_TERMS = {
    "total": total_terms,
    "ramas_actividad": ramas_terms,
    "posicion_ocupacional": posicion_terms,
    "fuera_fuerza_trabajo": fuera_terms,
}

# Regions dataset (data/dane/job_market/regiones/): region in `Perspectiva`, gender in `Sexo`
# (sexo.csv), `Periodo` = semesters I/II. "Total nacional" is excluded from the UI.
# Region label (Perspectiva) -> departments that compose it (DANE methodology), matched to the
# departments geojson via norm() to dissolve a regions geojson.
REGION_DEPTS = {
    "Total región Caribe": ["Atlántico", "Bolívar", "Cesar", "Córdoba", "Sucre",
                            "Magdalena", "La Guajira"],
    "Total región Oriental": ["Norte de Santander", "Santander", "Boyacá",
                              "Cundinamarca", "Meta"],
    "Total región Central": ["Caldas", "Risaralda", "Quindío", "Tolima", "Huila",
                             "Caquetá", "Antioquia"],
    "Total región Pacífica": ["Chocó", "Cauca", "Nariño", "Valle del Cauca"],
    "Total regiones Orinoquía, Amazonía e Insular*": [
        "Arauca", "Casanare", "Putumayo", "Amazonas", "Guainía", "Guaviare",
        "Vaupés", "Vichada", "Archipiélago de San Andrés Providencia y Santa Catalina"],
    "Bogotá D. C.": ["Santafé de Bogotá D.C"],
}

REGION_PET_CONCEPT = "Población en edad de trabajar"
REGION_DEFAULT_CONCEPT = "Población desocupada"

# Region label (Perspectiva, internal value) -> English display (filter, map hover, legend)
REGION_EN = {
    "Total región Caribe": "Caribbean",
    "Total región Central": "Central",
    "Total región Oriental": "Eastern",
    "Total región Pacífica": "Pacific",
    "Total regiones Orinoquía, Amazonía e Insular*": "Orinoquia, Amazonia & Insular",
    "Bogotá D. C.": "Bogotá D.C.",
}

# Total -> total.csv (no gender column); Men/Women -> sexo.csv filtered by `Sexo`
REGION_GENDER = {"Total": None, "Men": "Hombres", "Women": "Mujeres"}

# Spanish semester -> English label (UI adds "Annual average" as default)
REGION_PERIOD_EN = {"I": "First semester", "II": "Second semester"}

# Spanish Concepto -> English label (people concepts only; rate rows excluded)
region_terms = {
    "Población en edad de trabajar": "Working-age population (WAP)",
    "Fuerza de trabajo": "Labor force",
    "Población ocupada": "Employed",
    "Población desocupada": "Unemployed",
    "Población subocupada": "Underemployed",
    "Población fuera de la fuerza de trabajo": "Outside the labor force",
    "Fuerza de trabajo potencial": "Potential labor force",
}

# concept -> existing CSV rate concept; None means compute (value / PET * 100)
REGION_RATE_CONCEPTS = {
    "Población en edad de trabajar": "% población en edad de trabajar",
    "Fuerza de trabajo": "Tasa Global de Participación (TGP)",
    "Población ocupada": "Tasa de Ocupación (TO)",
    "Población desocupada": "Tasa de Desocupación (TD)",
    "Población subocupada": "Tasa de Subocupación (TS)",
    "Población fuera de la fuerza de trabajo": None,
    "Fuerza de trabajo potencial": None,
}

# --- Informality dataset (data/dane/job_market/informalidad/) ---
# Gender = Total -> total.csv (no Sexo col); Men/Women -> sexo.csv filtered by `Sexo`.
# Only "Total" table for now; INFORMALITY_FILES keys serve as UI Table selector options.
INFORMALITY_FILES = {
    "Total": "total",
}

informality_total_terms = {
    "Población ocupada": "Occupied Population",
    "Formal": "Formal",
    "Informal": "Informal",
}

INFORMALITY_TERMS = {
    "total": informality_total_terms,
}

INFORMALITY_DEFAULT_CONCEPT = "Informal"
