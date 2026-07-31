import pandas as pd
import streamlit as st
from generalities.dictionaries import months
from generalities.function import find_key_by_value
from generalities.demography_generalities.migration import COUNTRY_EN, COL_MAP
from generalities.i18n import t


def build_migration_map_data(df: pd.DataFrame, year: int | None, month_name: str, data_col: str, meta: list) -> tuple:
    direction, _, _ = meta

    if year is None:
        if month_name == "All":
            filtered = df
            title = t("{direction} travelers — All years").format(direction=t(direction))
        else:
            month_num = find_key_by_value(months, month_name)
            filtered = df[df["Fecha"].dt.month == month_num]
            title = t("{direction} travelers — {when}").format(direction=t(direction), when=f"{t(month_name)} ({t('All')})")
    elif month_name == "All":
        filtered = df[df["Fecha"].dt.year == year]
        title = t("{direction} travelers — {when}").format(direction=t(direction), when=year)
    else:
        month_num = find_key_by_value(months, month_name)
        filtered = df[(df["Fecha"].dt.year == year) & (df["Fecha"].dt.month == month_num)]
        title = t("{direction} travelers — {when}").format(direction=t(direction), when=f"{t(month_name)} {year}")

    grouped = filtered.groupby("País")[data_col].sum().reset_index()
    grouped["Location"] = grouped["País"].map(COUNTRY_EN)
    grouped = grouped.dropna(subset=["Location"])

    return grouped, title

def migration_countries_pivot(df_f: pd.DataFrame, all_countries_en: list, data_col: str, period_label: str, meta: list) -> tuple:
    direction, metric, label = meta

    with st.sidebar:
        selected_en = st.multiselect(t("Countries:"), all_countries_en, key="mig_countries", format_func=t)

    if not selected_en:
        st.info(t("Select one or more countries from the sidebar."))
        return None, None

    selected_es = [find_key_by_value(COUNTRY_EN, n) for n in selected_en]
    df_c = df_f[df_f["País"].isin(selected_es)].copy()
    df_c["País_en"] = df_c["País"].map(COUNTRY_EN)

    pivot = (
        df_c.pivot_table(index="Period", columns="País_en", values=data_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index.name = period_label
    info = [t("{direction} — {metric} travelers by country").format(direction=t(direction), metric=t(metric)), period_label, label]

    return pivot, info

def migration_single_pivot(df_f: pd.DataFrame, all_countries_en: list, compare_by: str, meta: list, period_label: str) -> tuple:
    direction, metric, _ = meta

    key = "mig_country_dir" if compare_by == "Direction" else "mig_country_gender"

    with st.sidebar:
        selected_en = st.selectbox(t("Country:"), ["All"] + all_countries_en, key=key, format_func=t)

    if selected_en != "All":
        country_es = find_key_by_value(COUNTRY_EN, selected_en)
        df_f = df_f[df_f["País"] == country_es]

    country_label = "All countries" if selected_en == "All" else selected_en

    if compare_by == "Direction":
        col_a = COL_MAP[("Inbound", metric)]
        col_b = COL_MAP[("Outbound", metric)]
        col_names = ["Inbound", "Outbound"]
        title = t("{country} — {metric} travelers").format(country=t(country_label), metric=t(metric))
    else:
        col_a = COL_MAP[(direction, "Female")]
        col_b = COL_MAP[(direction, "Male")]
        col_names = ["Female", "Male"]
        title = t("{country} — {direction} by gender").format(country=t(country_label), direction=t(direction))

    pivot = df_f.groupby("Period")[[col_a, col_b]].sum()
    pivot.columns = col_names
    pivot.index.name = period_label
    info = [title, period_label, "People"]

    return pivot, info

def migration_year_pivot(df_f: pd.DataFrame, data_col: str, meta: list) -> tuple:
    direction, metric, label, *country = meta

    month_order = [months[i] for i in sorted(months.keys())]

    df_f = df_f.copy()
    df_f["Month_num"] = df_f["Fecha"].dt.month
    df_f["Year"] = df_f["Fecha"].dt.year.astype(str)

    pivot = (
        df_f.pivot_table(index="Month_num", columns="Year", values=data_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index = pivot.index.map(months)
    pivot = pivot.reindex([m for m in month_order if m in pivot.index])
    pivot.index.name = "Month"

    if country:
        info = [t("{direction} — {subject} year comparison").format(direction=t(direction), subject=t(country[0])), "Month", label]
    else:
        info = [t("{direction} — {subject} year comparison").format(direction=t(direction), subject=t(metric)), "Month", label]

    return pivot, info
