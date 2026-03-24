import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option("display.max_rows", None)

path = "./data/banco_republica/GDP/annual_growth.csv"

df = pd.read_csv(path, encoding="utf-8", dtype=str)

df = df.set_index("Fecha")
df = df.apply(lambda col: col.str.replace(",", ".", regex=False))

df.index = pd.to_datetime(df.index, dayfirst=True)

df.index = [f"{date.year}" for date in df.index]

df.to_csv(path, encoding="utf-8", index=True)

