import pandas as pd

path_in = "../data/original/world_bank/net_migration.xls"
path_out = "../data/world_bank/net_migration.csv"

df = pd.read_excel(path_in, skiprows=3)

df = df[df.iloc[:, 0] == "Colombia"]

df = df.drop(df.columns[[0, 1, 2, 3]], axis=1)

a = df.T
a.reset_index(inplace=True)
a = a.rename(columns={a.columns[0]: "Fecha", a.columns[1]: "Migration"})

a.to_csv(path_out, index=False)
print(f"Saved {len(a)} row(s) → {path_out}")
