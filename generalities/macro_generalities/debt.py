from generalities.function import BASE_DIR, SeriesSpec

CONCEPTS = {"Total Debt": "Deuda total", "Internal Debt": "Deuda interna", "External Debt": "Deuda externa"}
TOTAL_SPEC = SeriesSpec(CONCEPTS["Total Debt"], "Total Debt")
NOMINAL_ANNUAL_PATH = BASE_DIR / "data/banco_republica/GDP/nominal_annual.csv"
