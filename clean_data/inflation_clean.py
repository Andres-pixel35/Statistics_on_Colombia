import pandas as pd

def xlsx_to_csv_by_city(filepath):
    raw = pd.read_excel(filepath, header=None)

    city_row = raw[raw.iloc[:, 1:].notna().any(axis=1)].index[0]
    metric_row = raw[raw.iloc[:, 1:].notna().any(axis=1)].index[1]
    data_start = raw[raw.iloc[:, 0].notna()].index[0]

    cities = raw.iloc[city_row].ffill()
    metrics = raw.iloc[metric_row]

    df = raw.iloc[data_start:].reset_index(drop=True)
    df.columns = pd.MultiIndex.from_arrays([cities, metrics])

    date_col = df.iloc[:, 0]
    city_names = cities.iloc[1:].unique()

    for city in city_names:
        city_df = df[city].copy()
    
        city_df.insert(0, "Fecha", date_col.values)
        filename = f"{str(city).strip().replace(' ', '_')}.csv"
        
        city_df = city_df.iloc[1:]
        city_df.to_csv(f"../data/banco_republica/CPI/spend_category/{filename}", index=False)
        print(f"Saved: {filename}")

xlsx_to_csv_by_city("../data/original/banco_republica/CPI/2_IPC_2018_por_division_de_gasto_iqy.xlsx")
