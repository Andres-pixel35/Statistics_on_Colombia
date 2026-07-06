PRODUCTIVITY_FILES = {
    "By Employed Person": "por_persona_empleada",
    "By Hour Worked": "por_hora_trabajada",
    "Value Added Approach": "productividad_total_factores",
}

# Stem -> subdir under data/dane/productivity/
PRODUCTIVITY_BASE = {
    "por_persona_empleada": "laboral",
    "por_hora_trabajada": "laboral",
    "productividad_total_factores": "valor_agregado",
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
}
