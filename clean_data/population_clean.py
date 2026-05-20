import pandas as pd

path_in = "../data/original/datos_abiertos/Entradas_de_extranjeros_a_Colombia_20260520.csv"
safe_path_in = "../data/datos_abiertos/inbound_co/"
path_out = "../data/original/datos_abiertos/Salidas_de_colombianos_desde_el_territorio_nacional_20260520.csv"
safe_path_out = "../data/datos_abiertos/outbound_co/"

MONTH_MAP = {
     "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
     "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
     "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12,
 }

use_columns = [0, 1, 2, 4, 5, 7]
df = pd.read_csv(path_in, encoding="utf-8", usecols=use_columns, decimal=",")

column = df.columns[2]
df[column] = df[column].astype(str).str.strip().str.title()

df["Fecha"] = pd.to_datetime(
     df["Año"].astype(str) + "-" + df["Mes"].map(MONTH_MAP).astype(str)
 ).dt.to_period("M")

df[["Femenino", "Masculino", "Total"]]= df[["Femenino", "Masculino", "Total"]].astype(int)

grouped = (
     df.groupby(["Fecha", column], sort=False)[["Femenino", "Masculino", "Total"]]
     .sum()
     .reset_index()
 )

for country, sub in grouped.groupby(column):
    safe = country.replace("/", "-").replace(" ", "_")
    sub.to_csv(f"{safe_path_in}{safe}.csv", index=False)
    print(f"Saved: {safe}")

