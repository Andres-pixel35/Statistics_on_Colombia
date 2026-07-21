from generalities.function import BASE_DIR

DATASETS = {
    "Original": {
        "base": "data/dane/ISE/original",
        "growth_label": "Annual Growth",
        "growth_file": "tasas_anuales.csv",
    },
    "Seasonally Adjusted": {
        "base": "data/dane/ISE/ajustado_estacional",
        "growth_label": "Monthly Growth",
        "growth_file": "tasas_mensuales.csv",
    },
}


def ise_paths(dataset: str) -> dict:
    cfg = DATASETS[dataset]
    base = BASE_DIR / cfg["base"]
    return {
        cfg["growth_label"]: base / cfg["growth_file"],
        "Year to Date Growth": base / "tasas_ano_corrido.csv",
        "Index": base / "indice.csv",
    }


def ise_units(dataset: str) -> dict:
    return {
        DATASETS[dataset]["growth_label"]: "%",
        "Year to Date Growth": "%",
        "Index": "Index (2015=100)",
    }

CATEGORY_EN = {
    "Indicador de Seguimiento a la Economía": "Total ISE",
    "Actividades primarias": "Primary Activities",
    "Actividades secundarias": "Secondary Activities",
    "Actividades terciarias": "Tertiary Activities",
}

ACTIVITY_EN = {
    "Indicador de Seguimiento a la Economía": {
        "Indicador de Seguimiento a la Economía": "Total ISE",
    },
    "Actividades primarias": {
        "Agricultura, ganadería, caza, silvicultura y pesca; Explotación de minas y canteras":
            "Agriculture, Livestock, Hunting, Forestry, Fishing and Mining",
    },
    "Actividades secundarias": {
        "Industrias manufactureras; Construcción": "Manufacturing and Construction",
    },
    "Actividades terciarias": {
        "Actividades terciarias": "Tertiary Activities (Total)",
        "Suministro de electricidad, gas, vapor y aire acondicionado; Distribución de agua; "
        "evacuación y tratamiento de aguas residuales, gestión de desechos y actividades de "
        "saneamiento ambiental":
            "Electricity, Gas, Water Supply and Waste Management",
        "Comercio al por mayor y al por menor; Reparación de vehículos automotores y "
        "motocicletas; Transporte y almacenamiento; Alojamiento y servicios de comida":
            "Trade, Vehicle Repair, Transportation and Accommodation & Food Services",
        "Información y comunicaciones": "Information and Communications",
        "Actividades financieras y de seguros": "Financial and Insurance Activities",
        "Actividades inmobiliarias": "Real Estate Activities",
        "Actividades profesionales, científicas y técnicas; Actividades de servicios "
        "administrativos y de apoyo":
            "Professional, Scientific, Technical and Administrative Support Activities",
        "Administración pública y defensa; planes de seguridad social de afiliación "
        "obligatoria; Educación; Actividades de atención de la salud humana y de servicios "
        "sociales; Actividades artísticas, de entretenimiento y recreación y otras actividades "
        "de servicios; Actividades de los hogares individuales en calidad de empleadores; "
        "actividades no diferenciadas de los hogares individuales como productores de bienes y "
        "servicios para uso propio":
            "Public Administration, Education, Health, Arts & Entertainment and Household "
            "Activities",
    },
}
