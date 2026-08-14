import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import streamlit as st
from app_pages.helpers.macro import gdp_functions as mf
from generalities.function import cap_series
from generalities.i18n import t, get_lang
from generalities.demography_generalities.population import MEN_COLOR, WOMEN_COLOR
from app_pages.helpers.mobile import (
    _title, _top_margin, _gauge_title, _map_layout,
    _legend, _bottom_margin, _chart_height, _category_ticks,
)

# Mainland Colombia's lon/lat extent. The San Andrés y Providencia archipelago
# sits ~700km off in the Caribbean; fitbounds("locations") stretches the view to
# include it, shrinking the mainland shape everyone actually looks at.
MAINLAND_LON_RANGE = [-79.5, -66.5]
MAINLAND_LAT_RANGE = [-4.6, 12.8]

def line_chart(data: pd.DataFrame, labels: dict, info: list, highlight: str = None):
    info = [t(info[0]), t(info[1]), t(info[2]), *info[3:]]
    highlight = t(highlight)
    data = cap_series(data)
    data = data.rename(index=lambda i: t(i) if isinstance(i, str) else i)
    fig = px.line(data, labels={data.index.name or "index": info[1], "value": info[2]})
    fig.update_layout(

        height=600,

        title=_title(info[0]),

        margin=dict(l=50, r=20, t=_top_margin(), b=0),
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=0.5,
        gridcolor="rgba(255, 255, 255, 0.1)",
        tickfont=dict(size=15),
        tickformat=",.0f"
    )

    fig.update_xaxes(
        type="category",
        showgrid=False,
        **_category_ticks(len(data)),
    )

    fig.update_layout(
        xaxis_title_font=dict(size=15),
        yaxis_title_font=dict(size=15),
    )

    fig.for_each_trace(lambda t_: t_.update(name = t(labels.get(t_.name, t_.name)),
                                          hovertemplate = f"<b>%{{fullData.name}}</b><br>{info[1]}: %{{x}}<br>{info[2]}: %{{y:,.2f}}<extra></extra>"))

    if highlight:
        for trace in fig.data:
            if trace.name != highlight:
                trace.update(line=dict(color="rgba(180,180,180,0.3)"))

    fig.update_layout(legend_title_text="")

    fig.update_layout(
        height=_chart_height(len(fig.data)),
        legend=_legend(len(fig.data)),
        margin=dict(t=_top_margin(), b=_bottom_margin(len(fig.data)))
    )
    return fig

def bar_chart(data: pd.DataFrame, labels: dict, info: list, highlight: str = None, barmode: str = "group"):
    info = [t(info[0]), t(info[1]), t(info[2]), *info[3:]]
    highlight = t(highlight)
    data = cap_series(data)
    data = data.rename(index=lambda i: t(i) if isinstance(i, str) else i)
    # "relative" stacks positives above zero and negatives below it independently; plain "stack"
    # piles traces in order regardless of sign, which can visually bury a bar under a bigger one
    # of the opposite sign. Same rendering as "stack" when every value shares a sign.
    px_barmode = "relative" if barmode == "stack" else barmode
    fig = px.bar(data, barmode=px_barmode, labels={data.index.name or "index": info[1], "value": info[2]})
    fig.update_layout(
        height=600,
        title=_title(info[0]),
        margin=dict(l=50, r=20, t=_top_margin(), b=0),
    )

    fig.update_yaxes(
        showgrid=False,
        gridwidth=0.5,
        gridcolor="rgba(255, 255, 255, 0.1)",
        tickfont=dict(size=15),
        tickformat=",.0f"
    )

    fig.update_xaxes(
        type="category",
        showgrid=False,
        **_category_ticks(len(data)),
    )

    fig.update_layout(
        xaxis_title_font=dict(size=15),
        yaxis_title_font=dict(size=15),
    )

    fig.for_each_trace(lambda t_: t_.update(name=t(labels.get(t_.name, t_.name)),
                                          hovertemplate=f"<b>%{{fullData.name}}</b><br>{info[1]}: %{{x}}<br>{info[2]}: %{{y:,.2f}}<extra></extra>"))

    if highlight:
        for trace in fig.data:
            if trace.name != highlight:
                trace.update(marker=dict(color="rgba(180,180,180,0.3)"))

    fig.update_layout(legend_title_text="")

    fig.update_layout(
        height=_chart_height(len(fig.data)),
        legend=_legend(len(fig.data)),
        margin=dict(t=_top_margin(), b=_bottom_margin(len(fig.data)))
    )
    return fig


def _format_number(col: pd.Series) -> pd.Series:
    if not pd.api.types.is_numeric_dtype(col):
        return col
    decimals = 0 if (col.dropna() == col.dropna().round()).all() else 2
    es = get_lang() == "es"
    return col.map(lambda x: x if pd.isna(x) else
                    (f"{x:,.{decimals}f}".translate(str.maketrans(",.", ".,"))
                     if es else f"{x:,.{decimals}f}"))


def translate_table(data, info=None, labels=None):
    labels = labels or {}
    data = data.rename(index=lambda i: t(i) if isinstance(i, str) else i)
    if info:
        data.index.name = t(info[1])
    elif data.index.name:
        data.index.name = t(data.index.name)
    if isinstance(data, pd.DataFrame):
        data = data.rename(columns=lambda c: t(labels.get(c, c)) if isinstance(c, str) else c)
    elif data.name:
        data = data.rename(t(labels.get(data.name, data.name)))
    data = data.apply(_format_number) if isinstance(data, pd.DataFrame) else _format_number(data)
    return data


def line_or_bar(chart_type, data, info, labels=None, highlight=None,
                force_bar=False, bar_if_single=True, barmode="group"):

    if chart_type == "Table":
        return translate_table(data, info, labels)

    single_row = isinstance(data, pd.DataFrame) and len(data) == 1

    if chart_type == "Bar" or force_bar or (bar_if_single and single_row):
        if single_row:
            series = data.iloc[0]
            series.index = [t((labels or {}).get(c, c)) for c in series.index]
            return ranked_bar_chart(series, [info[0], info[2], ""])
        return bar_chart(data, labels or {}, info, highlight=highlight, barmode=barmode)

    return line_chart(data, labels or {}, info, highlight=highlight)


def ranked_bar_chart(series: pd.Series, info: list):
    info = [t(info[0]), t(info[1]), t(info[2]), *info[3:]]
    data = series.sort_values(ascending=True)
    fmt = ",.0f" if (data == data.round()).all() else ",.2f"
    fig = px.bar(
        x=data.values,
        y=[t(i) for i in data.index.astype(str)],
        orientation="h",
        labels={"x": info[1], "y": info[2]},
    )
    fig.update_layout(
        height=max(450, 42 * len(data)),
        title=_title(info[0]),
        margin=dict(l=50, r=20, t=_top_margin(), b=0),
        showlegend=False,
        xaxis_title_font=dict(size=15),
        yaxis_title_font=dict(size=15),
    )
    fig.update_xaxes(
        showgrid=False, gridwidth=0.5, gridcolor="rgba(255, 255, 255, 0.1)",
        tickfont=dict(size=15), tickformat=fmt,
    )
    fig.update_yaxes(showgrid=False, tickfont=dict(size=13), automargin=True)
    fig.update_traces(
        marker_color="darkblue",
        hovertemplate=f"<b>%{{y}}</b><br>{info[1]}: %{{x:{fmt}}}<extra></extra>",
    )
    return fig

def gdp_growth(df: pd.DataFrame, year: list, president: str, index: int, quarter: str|None, title: str = "Real Annual GDP Growth", chart_type: str = "Line"):
    title = t(title)
    df, df_local = mf.clean_annual_growth(df, year, president, index, quarter)
    if chart_type == "Table":
        return translate_table(df_local, [title, "Year", "Growth (%)"])
    if len(df_local) > 1:
        plot = px.bar if chart_type == "Bar" else px.line
        fig = plot(df_local, labels={"value": t("Growth (%)"), "Fecha": t("Year")})

        fig.update_layout(

            height=600,

            title=_title(title),

            showlegend=False,
            margin=dict(l=50, r=20, t=_top_margin(), b=0),
        )

        fig.update_yaxes(
            showgrid=True,
            gridwidth=0.5,
            gridcolor="rgba(255, 255, 255, 0.1)",
            tickfont=dict(size=15),
            tickformat=",.0f"
        )

        fig.update_xaxes(
            type="category",
            showgrid=False,
            **_category_ticks(len(df_local)),
        )

        fig.update_layout(
            xaxis_title_font=dict(size=15),
            yaxis_title_font=dict(size=15),
        )

        fig.for_each_trace(lambda t_: t_.update(
            hovertemplate=f"<br>{t('Year')}: %{{x}}<br>{t('Growth (%)')}: %{{y:.2f}}<extra></extra>"
        ))

    else:
        try:
            column = df_local.columns[index - 1]
            growth = df_local[column].iloc[0]
            min_growth = df[column].min()
            max_growth = df[column].max()
            avg_growth = df[column].median()
        except Exception:
            st.warning(t("There is no data for the selected filters"))
            st.stop()

        if quarter is None:
            quarter = ""
        else:
            quarter = f"-{quarter}" 

        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = growth,
            number = {"valueformat": ".2f", "suffix": "%"},
            delta = {
                "reference": avg_growth,
                "position": "bottom",
                "valueformat": ".2f",
                "suffix": t(" vs Median")
            },
            title = _gauge_title(f"{year[0]}{quarter} {title}"),
            gauge = {
                "axis": {
                    "range": [min_growth, max_growth],
                    "tickformat": ".1f"
                },
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [min_growth, avg_growth], "color": "lightgray"},
                    {"range": [avg_growth, max_growth], "color": "#e5f5e0"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": avg_growth
                }
            }
        ))

        fig.update_layout(margin=dict(t=_top_margin(), b=20, l=30, r=30), height=400)
    return fig


def render_chart(fig):
    if isinstance(fig, (pd.DataFrame, pd.Series)):
        st.dataframe(fig)
        return
    fig.update_layout(separators=",." if get_lang() == "es" else ".,")
    st.plotly_chart(fig)
    msg = st.session_state.pop("chart_warning", None)
    if msg:
        template, kw = msg
        st.warning(t(template).format(**kw))

def indicator(data: pd.DataFrame, full_series: pd.Series, reference: float, info: list):
    title, valueformat, suffix, delta_suffix = t(info[0]), info[1], t(info[2]), t(info[3])

    value = data.iloc[0, 0]
    base = full_series.dropna()
    vmin, vmax = base.min(), base.max()

    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        number = {"valueformat": valueformat, "suffix": suffix},
        delta = {
            "reference": reference,
            "position": "bottom",
            "valueformat": valueformat,
            "suffix": delta_suffix
        },
        title = _gauge_title(title),
        gauge = {
            "axis": {
                "range": [vmin, vmax],
                "tickformat": valueformat
            },
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [vmin, reference], "color": "lightgray"},
                {"range": [reference, vmax], "color": "#e5f5e0"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": reference
            }
        }
    ))

    fig.update_layout(margin=dict(t=_top_margin(), b=20, l=30, r=30), height=400)
    return fig

def choropleth_map(data: pd.DataFrame, col: str, info: list):
    info = [t(info[0]), t(info[1]), t(info[2]), *info[3:]]
    # Traveler counts are hugely skewed (median ~1e3, max ~1e7): color on a log
    # scale so mid-size countries stay distinguishable, hover shows the raw value.
    data = data.assign(_log=np.log10(data[col].clip(lower=1)))
    fig = px.choropleth(
        data,
        locations="Location",
        locationmode="country names",
        color="_log",
        hover_name=data["Location"].map(t),
        custom_data=[col],
        color_continuous_scale="Blues",
        labels={"_log": info[2]},
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" + info[2] + ": %{customdata[0]:,.0f}<extra></extra>"
    )
    if st.context.theme.type == "dark":
        geo_colors = dict(oceancolor="rgb(15, 30, 50)", landcolor="rgb(45, 45, 45)",
                          coastlinecolor="rgb(80, 80, 80)")
    else:
        geo_colors = dict(oceancolor="#C9D8E4", landcolor="#DDD8C9",
                          coastlinecolor="#B5AE9A")
    fig.update_geos(
        showocean=True,
        showland=True,
        showframe=False,
        showcoastlines=True,
        projection_type="natural earth",
        lataxis_range=[-58, 88],
        **geo_colors,
    )
    layout = _map_layout(info[2])
    max_exp = int(data["_log"].max())
    ticks = list(range(0, max_exp + 1))
    labels_1k = ["1", "10", "100", "1K", "10K", "100K", "1M", "10M", "100M"]
    layout["coloraxis_colorbar"].update(tickvals=ticks, ticktext=labels_1k[:len(ticks)])
    fig.update_layout(
        title=_title(info[0]),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        **layout,
    )
    return fig

def colombia_choropleth(data: pd.DataFrame, geojson: dict, feature_key: str, col: str, info: list,
                        val_fmt: str = ",.0f"):
    info = [t(info[0]), t(info[1]), t(info[2]), *info[3:]]
    fig = px.choropleth(
        data,
        geojson=geojson,
        featureidkey=feature_key,
        locations="Code",
        color=col,
        hover_name="Name",
        color_continuous_scale="Blues",
        labels={col: info[2]},
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" + info[2] + ": %{z:" + val_fmt + "}<extra></extra>"
    )
    # Grey base layer so departments without data still show (Plotly skips NaN-z polygons).
    prop = feature_key.split(".")[-1]
    codes = [f["properties"][prop] for f in geojson["features"]]
    base = go.Choropleth(geojson=geojson, featureidkey=feature_key, locations=codes,
                         z=[0] * len(codes), showscale=False, hoverinfo="skip",
                         colorscale=[[0, "#d9d9d9"], [1, "#d9d9d9"]], marker_line_color="white")
    fig.add_trace(base)
    fig.data = fig.data[::-1]
    fig.update_geos(visible=False, lonaxis_range=MAINLAND_LON_RANGE, lataxis_range=MAINLAND_LAT_RANGE)
    fig.update_layout(
        title=_title(info[0]),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        **_map_layout(info[2]),
    )
    return fig

def projection_line(data: pd.DataFrame, info: list, split_year: int, highlight: str = None, labels: dict = None):
    """Line chart where each series is solid up to `split_year` and dashed after it
    (projected years)."""
    info = [t(info[0]), t(info[1]), t(info[2]), *info[3:]]
    highlight = t(highlight)
    data = cap_series(data)
    if isinstance(data, pd.Series):
        data = data.to_frame()
    labels = labels or {}
    palette = px.colors.qualitative.Plotly

    fig = go.Figure()
    for i, col in enumerate(data.columns):
        name = t(labels.get(col, col))
        color = palette[i % len(palette)]
        if highlight and name != highlight:
            color = "rgba(180,180,180,0.3)"
        s = data[col].dropna()
        obs = s[s.index <= split_year]
        proj = s[s.index >= split_year]
        fig.add_trace(go.Scatter(
            x=[str(j) for j in obs.index], y=obs.values, mode="lines", name=name,
            line=dict(color=color),
            hovertemplate=f"<b>{name}</b><br>{info[1]}: %{{x}}<br>{info[2]}: %{{y:,.0f}}<extra></extra>",
        ))
        if len(proj) > 1:
            fig.add_trace(go.Scatter(
                x=[str(j) for j in proj.index], y=proj.values, mode="lines", name=name,
                line=dict(color=color, dash="dash"), showlegend=False,
                hovertemplate=f"<b>{name} {t('(projected)')}</b><br>{info[1]}: %{{x}}<br>{info[2]}: %{{y:,.0f}}<extra></extra>",
            ))

    fig.update_layout(
        height=_chart_height(len(data.columns)),
        title=_title(info[0]),
        margin=dict(l=50, r=20, t=_top_margin(), b=_bottom_margin(len(data.columns))),
        xaxis_title=info[1], yaxis_title=info[2],
        xaxis_title_font=dict(size=15), yaxis_title_font=dict(size=15),
        legend_title_text="",
        legend=_legend(len(data.columns)),
    )
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor="rgba(255, 255, 255, 0.1)",
                     tickfont=dict(size=15), tickformat=",.0f")
    fig.update_xaxes(type="category", showgrid=False, **_category_ticks(len(data)))
    return fig

def population_pyramid(men: pd.Series, women: pd.Series, info: list):
    """Diverging horizontal bars: men to the left (negative), women to the right.

    info = [title, value_label, valueformat]"""
    title, value_label, valueformat = t(info[0]), t(info[1]), info[2]
    men = men.rename(t(men.name))
    women = women.rename(t(women.name))
    groups = list(men.index)
    maxv = max(men.max(), women.max()) or 1
    ticks = [(-maxv) + (2 * maxv) * k / 6 for k in range(7)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=groups, x=[-v for v in men.values], orientation="h", name=men.name,
        marker_color=MEN_COLOR, customdata=list(men.values),
        hovertemplate=f"<b>{men.name}</b><br>{t('Age')}: %{{y}}<br>{value_label}: %{{customdata:{valueformat}}}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=groups, x=list(women.values), orientation="h", name=women.name,
        marker_color=WOMEN_COLOR,
        hovertemplate=f"<b>{women.name}</b><br>{t('Age')}: %{{y}}<br>{value_label}: %{{x:{valueformat}}}<extra></extra>",
    ))
    fig.update_layout(
        barmode="overlay", bargap=0.1, height=600,
        title=_title(title),
        margin=dict(l=50, r=20, t=_top_margin(), b=0),
        xaxis_title=value_label, yaxis_title=t("Age group"),
        xaxis_title_font=dict(size=15), yaxis_title_font=dict(size=15),
        legend_title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(tickvals=ticks, ticktext=[f"{abs(t):{valueformat}}" for t in ticks],
                     showgrid=False, gridwidth=0.5, gridcolor="rgba(255, 255, 255, 0.1)",
                     tickfont=dict(size=14))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=13), automargin=True)
    return fig
