from generalities.function import BASE_DIR, SeriesSpec

CONCEPTS = {"Total Debt": "Deuda total", "Internal Debt": "Deuda interna", "External Debt": "Deuda externa"}
TOTAL_SPEC = SeriesSpec(CONCEPTS["Total Debt"], "Total Debt")
NOMINAL_ANNUAL_PATH = BASE_DIR / "data/banco_republica/GDP/nominal_annual.csv"
PERFIL_PATH = BASE_DIR / "data/hacienda/debt/perfil/perfil_total.csv"
PERIODO_EN = {"Amortizaciones": "Amortization", "Intereses": "Interest", "Total": "Total"}

FUENTE_PATHS = {
    "Internal": BASE_DIR / "data/hacienda/debt/fuente/fuente_interna.csv",
    "External": BASE_DIR / "data/hacienda/debt/fuente/fuente_externa.csv",
    "Total": BASE_DIR / "data/hacienda/debt/fuente/fuente_total.csv",
}

FUENTE_TERMS = {
    "Internal": {
        "TES": "TES", "Bonos Fogafin": "Fogafin Bonds", "Bonos Ley 546/99": "Law 546/99 Bonds",
        "Títulos de reducción de deuda": "Debt Reduction Securities", "Bonos agrarios": "Agrarian Bonds",
        "Bonos de paz": "Peace Bonds", "Bono de seguridad": "Security Bond",
        "Depositós pásivos del Tesoro": "Treasury Passive Deposits", "Otros": "Other",
    },
    "External": {
        "Bonos": "Bonds", "BID": "IDB", "BIRF": "IBRD", "CAF": "CAF", "Otros": "Other",
    },
    "Total": {
        "TES": "TES", "Bonos externos": "External Bonds", "BID": "IDB", "BIRF": "IBRD", "CAF": "CAF",
        "Créditos comerciales": "Commercial Credits", "Bonos Ley 546": "Law 546 Bonds",
        "Bonos Fogafin": "Fogafin Bonds", "Bonos Agrarios": "Agrarian Bonds",
        "Títulos de reducción de deuda": "Debt Reduction Securities", "Bonos de Paz": "Peace Bonds",
        "Titulos de Tesorería": "Treasury Securities", "Otros - deuda interna": "Other - Internal",
        "Otros - deuda externa": "Other - External",
    },
}

TASA_PATHS = {
    "Internal": BASE_DIR / "data/hacienda/debt/tasa/tasa_interna.csv",
    "External": BASE_DIR / "data/hacienda/debt/tasa/tasa_externa.csv",
    "Total": BASE_DIR / "data/hacienda/debt/tasa/tasa_total.csv",
}

TASA_TERMS = {
    "Internal": {
        "COP fija": "COP Fixed", "UVR fija": "UVR Fixed", "COP IPC": "COP CPI-Indexed",
        "USD fija": "USD Fixed", "DTF": "DTF", "Otros": "Other",
        "%tasa fija": "% Fixed Rate", "% tasa variable": "% Variable Rate",
    },
    "External": {"Tasa fija": "Fixed Rate", "Tasa variable": "Variable Rate"},
    "Total": {"Tasa fija": "Fixed Rate", "Tasa variable": "Variable Rate"},
}

MONEDA_PATHS = {
    "Internal": BASE_DIR / "data/hacienda/debt/moneda/moneda_interna.csv",
    "External": BASE_DIR / "data/hacienda/debt/moneda/moneda_externa.csv",
    "Total": BASE_DIR / "data/hacienda/debt/moneda/moneda_total.csv",
}

MONEDA_TERMS = {
    "Internal": {
        "COP": "COP", "UVR indexado (COP)": "UVR-Indexed (COP)", "USD": "USD",
        "% Moneda local": "% Local Currency", "% Moneda extranjera": "% Foreign Currency",
    },
    "External": {
        "USD": "USD", "EUR": "EUR", "JPY": "JPY", "GBP": "GBP", "CHF": "CHF", "COP": "COP",
        "% Moneda extranjera": "% Foreign Currency",
    },
    "Total": {
        "USD": "USD", "EUR": "EUR", "JPY": "JPY", "CHF": "CHF", "UVR (COP)": "UVR (COP)", "COP": "COP",
        "% Moneda local": "% Local Currency", "% Moneda extranjera": "% Foreign Currency",
    },
}

INDICADORES_PATH = BASE_DIR / "data/hacienda/debt/indicadores/indicadores.csv"

INDICADORES_TERMS = {
    "Duration": {
        "Internal": "Duración - Deuda interna",
        "External": "Duración - Deuda externa",
        "Total": "Duración - Deuda total",
    },
    "Average Life": {
        "Internal": "Vida media - Deuda interna",
        "External": "Vida media - Deuda externa",
        "Total": "Vida media - Deuda total",
    },
    "Average Coupon": {
        "Internal": "Cupón promedio (%) - Deuda interna (COP)",
        "External": "Cupón promedio (%) - Deuda externa (USD)",
        "Total": "Cupón promedio (%) - Deuda Total",
    },
}

INDICADORES_UNITS = {"Duration": "Years", "Average Life": "Years", "Average Coupon": "%"}
