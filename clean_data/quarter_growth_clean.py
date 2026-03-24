import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option("display.max_rows", None)

path = "./data/banco_republica/GDP/quarter_growth.csv"

df = pd.read_csv(path, encoding="utf-8", dtype=str, na_values="-")

df = df.apply(lambda col: col.str.replace(".", "", regex=False))
df = df.apply(lambda col: col.str.replace(",", ".", regex=False))

df = df.drop(columns=[df.columns[1]])
df = df.set_index("Fecha")
df = df.dropna()

df.index = pd.to_datetime(df.index, dayfirst=True)

roman_map = {1: "I", 2: "II", 3: "III", 4: "IV"}

df.index = [f"{date.year}-{roman_map[date.quarter]}" for date in df.index]

df.columns = ["Variación Trimestral Anual", "Variación Año Corrido"]

df.to_csv(path, encoding="utf-8", index=True)

