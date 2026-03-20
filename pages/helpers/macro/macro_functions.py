import pandas as pd

def clean_gdp(df: pd.DataFrame) -> pd.Series:
    gdp_local = df.copy()

    gdp_local = gdp_local.set_index("Concepto")
    gdp_local = gdp_local.apply(lambda col: col.str.replace(".", "", regex=False))

    gdp_series = gdp_local.iloc[-1,:]

    if len(gdp_series) > 5:
        gdp_series.index = gdp_series.index.str.split("-").str[0]
        gdp_series = gdp_series.astype(int)

        gdp_series = gdp_series.groupby(gdp_series.index).sum()

    return gdp_series
