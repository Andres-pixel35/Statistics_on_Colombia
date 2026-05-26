import pandas as pd

input_path = "../data/original/banco_republica/GDP/quarter_growth.xlsx"
output_path = "../data/banco_republica/GDP/quarter_growth.csv"

df = pd.read_excel(input_path, dtype=str)

df = df.drop(index=df.index[0]).reset_index(drop=True)

df = df.rename(columns={df.columns[1]: "Variación Trimestral Anual"})

df[df.columns[1]] = df[df.columns[1]].str.replace(",", ".", regex=False)

df = df.dropna()

df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)

roman_map = {1: "I", 2: "II", 3: "III", 4: "IV"}
df["Fecha"] = [f"{date.year}-{roman_map[date.quarter]}" for date in df["Fecha"]]

df.to_csv(output_path, encoding="utf-8", index=False)
