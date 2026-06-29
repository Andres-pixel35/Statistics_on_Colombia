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
# "Total" table: Gender = Total -> total.csv (no Sexo col); Men/Women -> sexo.csv by `Sexo`.
# The other two tables have a `Grupo` column (Población ocupada/Formal/Informal) and no
# gender; their breakdown is in `Concepto`. INFORMALITY_FILES keys are the UI Table options.
INFORMALITY_FILES = {
    "Total": "total",
    "Social Security": "seguridad_social",
    "By Occupational Position": "posicion_ocupacional",
    "By Activity Branch": "ramas_actividad",
    "By Workplace": "lugar_trabajo",
    "By Company Size": "tamano_empresa",
    "By Education": "educacion",
}

informality_total_terms = {
    "Población ocupada": "Occupied Population",
    "Formal": "Formal",
    "Informal": "Informal",
}

seguridad_social_terms = {
    "Población ocupada": "Occupied Population",
    "Afiliada a salud": "Affiliated to health",
    "Régimen contributivo": "Contributory regime",
    "Régimen especial": "Special regime",
    "Régimen subsidiado": "Subsidized regime",
    "Aportantes": "Contributors",
    "Beneficiarios": "Beneficiaries",
    "Cotiza a pensión": "Contributing to pension",
    "Otro": "Other",
    "No sabe": "Unknown",
}

# Grouped tables reuse existing concept dicts (keys match the informality CSV spelling);
# the render filters out rollups + concepts absent from the selected Grupo. ramas reuses the
# Departments dict (dept_ramas_terms) — the Labor Force ramas_terms has divergent DANE spelling.
lugar_trabajo_terms = {
    "En esta vivienda": "In this dwelling",
    "En otras viviendas": "In other dwellings",
    "En kiosco - caseta": "In a kiosk / stall",
    "En un vehículo": "In a vehicle",
    "De puerta en puerta": "Door to door",
    "Sitio al descubierto en la calle": "Open-air spot on the street",
    "Local fijo, oficina, fábrica, etc": "Fixed premises (office, factory, etc.)",
    "En el campo o área rural": "In the field or rural area",
    "En una obra en construcción": "At a construction site",
    "En una mina o cantera": "In a mine or quarry",
    "Otro": "Other",
}

tamano_empresa_terms = {
    "Microempresa": "Microenterprise",
    "Empresa pequeña": "Small business",
    "Empresa mediana": "Medium business",
    "Empresa grande": "Large business",
}

educacion_terms = {
    "Ninguno": "None",
    "Básica primaria": "Primary",
    "Básica secundaria": "Lower secondary",
    "Educación media": "Upper secondary",
    "Técnica profesional y Tecnológica": "Technical & technological",
    "Universitaria": "University",
    "Posgrado": "Postgraduate",
}

INFORMALITY_TERMS = {
    "total": informality_total_terms,
    "seguridad_social": seguridad_social_terms,
    "posicion_ocupacional": posicion_terms,
    "ramas_actividad": dept_ramas_terms,
    "lugar_trabajo": lugar_trabajo_terms,
    "tamano_empresa": tamano_empresa_terms,
    "educacion": educacion_terms,
}

# Total-like tables: Gender split (own file + a *_sexo file), denom Población ocupada.
# `sexo` = gender filename stem; `default` = default concept (Spanish key); `miles` = filter
# to the absolute "(en miles)" Grupo (seguridad_social has a 2nd Distribución porcentual Grupo).
INFORMALITY_TOTAL_LIKE = {
    "total":            {"sexo": "sexo",                  "default": "Informal",         "miles": False},
    "seguridad_social": {"sexo": "seguridad_social_sexo", "default": "Afiliada a salud", "miles": True},
}

# UI label -> `Grupo` value (also the percentage denominator concept for that group)
INFORMALITY_GROUP = {"Total": "Población ocupada", "Formal": "Formal", "Informal": "Informal"}

# DANE relabels seen across year ranges; collapse to one Concepto so series stay whole
INFORMALITY_CONCEPT_FIXES = {"Empleado del gobierno": "Obrero, empleado del gobierno"}

# --- Child Labor dataset (data/dane/job_market/infantil/) — Total nacional only ---
CHILD_LABOR_FILES = {"Total": "total", "By Age Group": "edad", "By Hours Worked": "horas"}
CHILD_LABOR_ALL_MINORS = "Población de 5 a 17 años"   # gender-share denom (both sexes, from total.csv)
CHILD_TOTAL_POP = "Población total"   # whole-population denom for the edad age-group totals (total.csv)

# edad.csv: child-labor concepts by age band (`Grupo`). count concept = f"Población de {band} {suffix}",
# paired with the band-wide official rate row (% mode); band-pop denom = f"Población de {band}" (fallback).
CHILD_AGE_GROUPS = {"5–14": "5 a 14 años", "15–17": "15 a 17 años"}
CHILD_AGE_CONCEPTS = {
    "Working minors": {
        "suffix": "que trabaja",
        "rate": "Tasa de Trabajo Infantil (TTI)"},
    "Unpaid domestic work (15h+)": {
        "suffix": "que no trabaja y realiza trabajo doméstico no remunerado en su hogar por 15 horas o más",
        "rate": "Tasa de Trabajo Infantil Ampliada por Trabajo Doméstico no remunerado (TTIAD)"},
    "Unpaid domestic & care work (15h+)": {
        "suffix": "que no trabaja y realiza trabajo doméstico y de cuidado no remunerado en su hogar por 15 horas o más",
        "rate": "Tasa de Trabajo Infantil Ampliada por Trabajo Doméstico y de Cuidado no remunerado (TTIADC)"},
    # Age-group total: count = the band's own population row; % = band / CHILD_TOTAL_POP (whole pop).
    "Population in age group": {
        "suffix": "",
        "rate": None},
}

# horas.csv: working children (5–17) by weekly hours; % = bucket / CHILD_HOURS_DENOM (working pop, in horas.csv).
CHILD_HOURS_DENOM = "Población de 5 a 17 años que trabaja"
CHILD_HOURS_CONCEPTS = {
    "Less than 15h": "Menos de 15 horas",
    "15 to 29h":     "De 15 a 29 horas",
    "30h or more":   "30 horas y más",
    "Not reported":  "No informa",
}

# English label -> per-gender count Concepto + the CSV rate Concepto (already a %).
# In Men/Women views the headcount's rate string is absent from sexo.csv, so percent falls back
# to count / CHILD_LABOR_ALL_MINORS * 100 (the requested gender share). "Población total" omitted.
CHILD_LABOR_CONCEPTS = {
    "Population aged 5–17": {
        "Total": "Población de 5 a 17 años",
        "Men":   "Hombres de 5 a 17 años",
        "Women": "Mujeres de 5 a 17 años",
        "rate":  "% población de 5 a 17 años",
    },
    "Working minors": {
        "Total": "Población de 5 a 17 años que trabaja",
        "Men":   "Hombres de 5 a 17 años que trabajan",
        "Women": "Mujeres de 5 a 17 años que trabajan",
        "rate":  "Tasa de Trabajo Infantil (TTI)",
    },
    "Unpaid domestic work (15h+)": {
        "Total": "Población de 5 a 17 años que no trabaja y realiza trabajo doméstico no remunerado en su hogar por 15 horas o más",
        "Men":   "Hombres de 5 a 17 años que no trabajan y realizan trabajo doméstico no remunerado en su hogar por 15 horas o más",
        "Women": "Mujeres de 5 a 17 años que no trabajan y realizan trabajo doméstico no remunerado en su hogar por 15 horas o más",
        "rate":  "Tasa de Trabajo Infantil Ampliada por Trabajo Doméstico no remunerado (TTIAD)",
    },
    "Unpaid domestic & care work (15h+)": {
        "Total": "Población de 5 a 17 años que no trabaja y realiza trabajo doméstico y de cuidado no remunerado en su hogar por 15 horas o más",
        "Men":   "Hombres de 5 a 17 años que no trabajan y realizan trabajo doméstico y de cuidado no remunerado en su hogar por 15 horas o más",
        "Women": "Mujeres de 5 a 17 años que no trabajan y realizan trabajo doméstico y de cuidado no remunerado en su hogar por 15 horas o más",
        "rate":  "Tasa de Trabajo Infantil Ampliada por Trabajo Doméstico y de Cuidado no remunerado (TTIADC)",
    },
}
