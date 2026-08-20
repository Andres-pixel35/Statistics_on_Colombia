import pandas as pd

from generalities.function import BASE_DIR

DEFICIT_BASE = BASE_DIR / "data/hacienda/deficit"

# Years the source marks as not-yet-final (Annual view's "preliminary" caption).
PRELIMINARY_YEARS = pd.read_csv(DEFICIT_BASE / "anual" / "preliminary_years.csv")["year"].tolist()

# Frequency -> subfolder; also the Frequency selectbox's options, in display order.
FREQUENCIES = {"Annual": "anual", "Quarterly": "trimestral", "Monthly": "mensual"}

# Unit -> filename. "% of GDP" is precomputed by the source against DANE nominal GDP.
UNITS = {"COP": "balance_cop.csv", "% of GDP": "balance_pib.csv"}
UNIT_AXIS = {"COP": "Trillion (COP)", "% of GDP": "% of GDP"}
COP_SCALE = 1_000  # miles de millones -> Trillion (COP); see CLAUDE.md deficit.py section

# One genuinely reworded label between balance_cop and balance_pib (annual row 41).
CONCEPT_ALIASES = {"recuperacion de cartera diferente spnf":
                   "recuperacion de cartera spnf (intereses)"}

# Keys are norm()-ed Spanish Concepto values (lowercase, accent-stripped, whitespace-collapsed).
# Duplicated names (the three "Resto" rows) are parent-qualified as "<norm parent> > <norm concepto>",
# where parent is the last " > " segment of Grupo.
ANNUAL_TERMS = {
    "1. ingresos totales (sin causados)": "Total Revenue (excl. accrued)",
    "ingresos corrientes de la nacion": "Current Revenue",
    "ingresos tributarios": "Tax Revenue",
    "dian": "DIAN (Tax & Customs)",
    "renta": "Income Tax",
    "cuotas": "Income Tax — Instalments",
    "retencion": "Income Tax — Withholding",
    "iva interno": "Domestic VAT",
    "iva externo": "Import VAT",
    "gravamen arancelario": "Customs Duties",
    "sobretasa a la importaciones cif": "CIF Import Surcharge",
    "imp. nacional a la gasolina y acpm": "National Fuel Tax (Gasoline & Diesel)",
    "impuesto al carbono": "Carbon Tax",
    "consumo": "Consumption Tax",
    "cree": "CREE (Equity Income Tax)",
    "sobretasa a la gasolina y acpm": "Fuel Surcharge (Gasoline & Diesel)",
    "gravamen movimientos financieros": "Financial Transactions Tax",
    "impuestos saludables y de plastico": "Healthy & Plastic Taxes",
    "dian > resto": "Other DIAN Taxes",
    "timbre": "Stamp Tax",
    "impuesto simple": "SIMPLE Tax Regime",
    "normalizacion": "Normalization Tax",
    "retencion en la fuente inmuebles": "Withholding on Real Estate",
    "contribucion para la democracia (patrimonio) / impuesto a la riqueza": "Democracy Contribution / Wealth Tax",
    "ingresos no tributarios": "Non-Tax Revenue",
    "contribucion de hidrocarburos": "Hydrocarbon Contribution",
    "concesiones": "Concessions",
    "telefonia celular": "Mobile Telephony",
    "concesiones portuarias y otros": "Port and Other Concessions",
    "ingresos no tributarios > resto": "Other Non-Tax Revenue",
    "fondos especiales": "Special Funds",
    "otros recursos de capital": "Other Capital Resources",
    "rendimientos financieros totales": "Total Financial Yields",
    "excedentes financieros": "Financial Surpluses",
    "ecopetrol": "Ecopetrol",
    "banco de la republica": "Banco de la República",
    "telecom": "Telecom",
    "isa e isagen": "ISA and ISAGEN",
    "bancoldex": "Bancóldex",
    "estapublicos": "Public Establishments",
    "resto de empresas": "Other Companies",
    "recuperacion de cartera spnf (intereses)": "Loan Portfolio Recovery (NFPS)",
    "otros recursos": "Other Resources",
    "reintegros y recursos no apropiados": "Refunds and Unappropriated Resources",
    "otros recursos > resto": "Other Capital Resources — Rest",
    "2. pagos totales": "Total Payments",
    "pagos totales sin intereses": "Total Payments excl. Interest",
    "pagos corrientes de la nacion": "Current Payments",
    "intereses": "Interest",
    "intereses deuda externa": "External Debt Interest",
    "intereses deuda interna": "Internal Debt Interest",
    "costo impuesto endeudamiento externo": "External Borrowing Tax Cost",
    "funcionamiento": "Operating Expenses",
    "servicios personales": "Personnel Services",
    "transferencias": "Transfers",
    "transferencias regionales (sgp desde 2002)": "Regional Transfers (SGP since 2002)",
    "situado fiscal": "Situado Fiscal",
    "participaciones municipales": "Municipal Shares",
    "fondo de compensacion educativa deuda ley 60/93 (2002)": "Education Compensation Fund / Law 60/93 Debt (2002)",
    "pensiones": "Pensions",
    "otras": "Other Transfers",
    "gastos generales y otros": "General and Other Expenses",
    "inversion": "Investment",
    "3. deficit o superavit efectivo": "Cash Deficit / Surplus",
    "prestamo neto": "Net Lending",
    "ingresos causados": "Accrued Revenue",
    "gastos causados": "Accrued Expenses",
    "deuda flotante": "Floating Debt",
    "4. deficit o superavit total": "Total Deficit / Surplus",
    "5. costos de la reest. financiera": "Financial Restructuring Costs",
    "capitaliz. intereses fogafin": "Fogafín Interest Capitalization",
    "indexacion tes ley 546": "Law 546 TES Indexation",
    "indexacion trd": "TRD Indexation",
    "intereses ley 546": "Law 546 Interest",
    "intereses fogafin": "Fogafín Interest",
    "amortizacion trd": "TRD Amortization",
    "amortizacion ley 546": "Law 546 Amortization",
    "liquidacion caja agraria": "Caja Agraria Liquidation",
    "6. deficit a financiar": "Deficit to Finance",
    "balance primario": "Primary Balance",
}

# Shared by mensual and trimestral (identical labels, no duplicated names).
PERIOD_TERMS = {
    "ingresos totales": "Total Revenue",
    "ingresos corrientes de la nacion": "Current Revenue",
    "tributarios": "Tax Revenue",
    "no tributarios": "Non-Tax Revenue",
    "fondos especiales": "Special Funds",
    "ingresos de capital": "Capital Revenue",
    "ingresos causados": "Accrued Revenue",
    "gastos totales": "Total Spending",
    "intereses": "Interest",
    "intereses deuda externa": "External Debt Interest",
    "intereses deuda interna": "Internal Debt Interest",
    "indexacion tes b denominados en uvr": "UVR-Denominated TES B Indexation",
    "funcionamiento": "Operating Expenses",
    "servicios personales": "Personnel Services",
    "transferencias": "Transfers",
    "gastos generales": "General Expenses",
    "inversion": "Investment",
    "prestamo neto": "Net Lending",
    "deficit total": "Total Deficit",
    "costos de la reestructuracion financiera": "Financial Restructuring Costs",
    "deficit a financiar": "Deficit to Finance",
}

TERMS = {"anual": ANNUAL_TERMS, "mensual": PERIOD_TERMS, "trimestral": PERIOD_TERMS}

# Annual-only root key for the Total Deficit/Surplus group (its Concepts cascade needs a
# caption clarifying it isn't self-contained — see deficit.py tab).
TOTAL_DEFICIT_ROOT = "4. deficit o superavit total"

# frequency folder -> (revenue root key, spending root key) for "Compare revenue vs. spending"
COMPARE_ROOTS = {
    "anual":      ("1. ingresos totales (sin causados)", "2. pagos totales"),
    "mensual":    ("ingresos totales", "gastos totales"),
    "trimestral": ("ingresos totales", "gastos totales"),
}
