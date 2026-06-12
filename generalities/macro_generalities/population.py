from datetime import datetime
from generalities.function import BASE_DIR

PREV_YEAR = datetime.now().year - 1

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
