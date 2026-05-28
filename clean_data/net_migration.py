import pandas as pd

path_in = "../data/original/world_bank/net_migration.xls"
path_out = "../data/world_bank/net_migration.csv"

df = pd.read_excel(path_in, skiprows=3)

df = df[df.iloc[:, 0] == "Colombia"]

df = df.drop(df.columns[[1, 2, 3]], axis=1)

df = df.rename(columns={df.columns[0]: "Country"})

df.to_csv(path_out, index=False)
print(f"Saved {len(df)} row(s) → {path_out}")
