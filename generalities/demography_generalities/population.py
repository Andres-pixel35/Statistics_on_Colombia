from generalities.function import BASE_DIR, PREV_YEAR  # PREV_YEAR re-exported for demography consumers

POP_PATHS = {
    "national":     BASE_DIR / "data/dane/population/nacional.csv",
    "departmental": BASE_DIR / "data/dane/population/departamental.csv",
    "municipal":    BASE_DIR / "data/dane/population/municipal.csv",
}

# gender → aggregate (whole-population) column
GENDER_AGG = {"Total": "Total", "Men": "Total Hombres", "Women": "Total Mujeres"}
# gender → per-age column prefix ("Hombres_0", "Mujeres_0", "Total_0", ...)
GENDER_PREFIX = {"Total": "Total", "Men": "Hombres", "Women": "Mujeres"}

# single-year age filter (0..100)
AGE_SINGLE = ["All ages"] + [str(n) for n in range(101)]

# 5-year buckets for the population pyramid: (label, low, high) inclusive
PYRAMID_GROUPS = [(f"{lo}–{lo + 4}", lo, lo + 4) for lo in range(0, 100, 5)] + [("100+", 100, 100)]

# pyramid / share-metric gender colors
MEN_COLOR = "#1f77b4"
WOMEN_COLOR = "#e377c2"

PROJECTED_NOTE = ("Projected data is based on the 2018 National Population and Housing Census (CNPV), "
                  "updated with information following the COVID-19 pandemic.")

PYRAMID_MODES = ["Numbers", "% within age group", "% of total population"]
