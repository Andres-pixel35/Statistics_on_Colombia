import pandas as pd

path_in = "../data/original/datos_abiertos/Entradas_de_extranjeros_a_Colombia_20260520.csv"
path_out = "../data/original/datos_abiertos/Salidas_de_colombianos_desde_el_territorio_nacional_20260520.csv"
path_save = "../data/datos_abiertos/migration.csv"

MONTH_MAP = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
    "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
    "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12,
}

use_columns = [0, 1, 2, 4, 5, 7]  # Año, Mes, País, Femenino, Masculino, Total


def load_and_clean(path):
    df = pd.read_csv(path, encoding="utf-8", usecols=use_columns, decimal=",")
    col = df.columns[2]
    df[col] = df[col].astype(str).str.strip().str.title()
    df["Fecha"] = pd.to_datetime(
        df["Año"].astype(str) + "-" + df["Mes"].map(MONTH_MAP).astype(str)
    ).dt.to_period("M")
    df[["Femenino", "Masculino", "Total"]] = df[["Femenino", "Masculino", "Total"]].astype(int)
    return df, col


df_in, col_in = load_and_clean(path_in)
df_out, col_out = load_and_clean(path_out)

grp_in = (
    df_in.groupby(["Fecha", col_in], sort=False)[["Femenino", "Masculino", "Total"]]
    .sum()
    .reset_index()
    .rename(columns={col_in: "País", "Femenino": "Femenino_in", "Masculino": "Masculino_in", "Total": "Total_in"})
)

grp_out = (
    df_out.groupby(["Fecha", col_out], sort=False)[["Femenino", "Masculino", "Total"]]
    .sum()
    .reset_index()
    .rename(columns={col_out: "País", "Femenino": "Femenino_out", "Masculino": "Masculino_out", "Total": "Total_out"})
)

merged = grp_in.merge(grp_out, on=["Fecha", "País"], how="outer")

int_cols = ["Femenino_in", "Masculino_in", "Total_in", "Femenino_out", "Masculino_out", "Total_out"]
merged[int_cols] = merged[int_cols].fillna(0).astype(int)

merged = merged.sort_values(["Fecha", "País"]).reset_index(drop=True)

merged.to_csv(path_save, index=False)
print(f"Saved {len(merged)} rows → {path_save}")
