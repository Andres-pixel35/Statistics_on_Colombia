DEFAULT_STEM = "por_persona_empleada"
ACTIVITY_STEM = "actividad_economica"
ACTIVITY_COL = "Actividad Económica"

PRODUCTIVITY_FILES = {
    "By Employed Person": "por_persona_empleada",
    "By Hour Worked": "por_hora_trabajada",
    "Value Added Approach": "productividad_total_factores",
    "Production Approach": "nacional",
    "Economic Activity Approach": "actividad_economica",
}

# Stem -> subdir under data/dane/productivity/
PRODUCTIVITY_BASE = {
    "por_persona_empleada": "laboral",
    "por_hora_trabajada": "laboral",
    "productividad_total_factores": "valor_agregado",
    "nacional": "produccion/nacional",
    "actividad_economica": "produccion/actividad_economica",
}

# Spanish "Actividad Económica" value -> English label (Economic Activity Approach only)
ACTIVITY_EN = {
    "Agricultura, ganadería, caza, silvicultura y pesca":
        "Agriculture, Livestock, Hunting, Forestry and Fishing",
    "Minería y extracción": "Mining and Quarrying",
    "Industrias manufactureras": "Manufacturing",
    "Electricidad, gas y agua": "Electricity, Gas and Water",
    "Construcción": "Construction",
    "Comercio, hoteles y restaurantes": "Trade, Hotels and Restaurants",
    "Transporte, almacenamiento y comunicaciones": "Transport, Storage and Communications",
    "Intermediación financiera, actividades inmobiliarias, empresariales y de alquiler":
        "Financial Intermediation, Real Estate, Business and Rental Activities",
    "Actividades de servicios sociales, comunales y personales":
        "Social, Community and Personal Services",
    "Total de la economía": "Total Economy",
}

# Key order matters: the first key is the headline measure, used as the default concept.
PRODUCTIVITY_TERMS = {
    "por_persona_empleada": {
        "Labor productivity per employed person": "productividad laboral por persona empleada (%)",
        "Total factor productivity": "productividad total de los factores (pp)",
        "Contribution of hours worked per employee": "contribución de las horas trabajadas por empleado (pp)",
        "Labor composition": "composición laboral (pp)",
        "Contribution of capital per employed person": "contribución del capital por persona empleada (pp)",
    },
    "por_hora_trabajada": {
        "Labor productivity per hour worked": "productividad laboral por hora trabajada (%)",
        "Total factor productivity": "productividad total de los factores (pp)",
        "Labor composition": "composición laboral (pp)",
        "Contribution of capital per hour worked": "contribución del capital por hora trabajada (pp)",
    },
    "productividad_total_factores": {
        "Gross Value Added Growth": "valor agregado bruto (%)",
        "Labor Services": "servicios laborales (pp)",
        "Capital Services": "servicios de capital (pp)",
        "Contribution of Factors": "contribución de los factores (pp)",
        "Total Factor Productivity": "productividad total de los factores (pp)",
    },
    "nacional": {
        "Gross Production Growth": "producción (%)",
        "Labor Services (Total)": "servicios laborales total (pp)",
        "Labor Services (Women)": "servicios laborales mujeres (pp)",
        "Labor Services (Men)": "servicios laborales hombres (pp)",
        "Capital Services": "servicios de capital (pp)",
        "Intermediate Consumption": "consumos intermedios (pp)",
        "Contribution of Factors": "contribución de los factores (pp)",
        "Total Factor Productivity": "productividad total de los factores (pp)",
    },
    "actividad_economica": {
        "Production Growth Rate": "Tasas de crecimiento (%)",
        "Labor Composition": "Composición del trabajo (pp)",
        "Hours Worked": "Horas trabajadas (pp)",
        "Labor Total": "Laboral Total (pp)",
        "ICT Capital": "Capital TIC (pp)",
        "Non-ICT Capital": "Capital No TIC (pp)",
        "Capital Total": "Capital Total (pp)",
        "Energy": "Energía (pp)",
        "Materials": "Materiales (pp)",
        "Services": "Servicios (pp)",
        "Intermediate Consumption Total": "Consumo intermedio Total (pp)",
        "Contribution of Factors": "Contribución de los factores (pp)",
        "Total Factor Productivity": "Productividad Total de los Factores (pp)",
    },
}
