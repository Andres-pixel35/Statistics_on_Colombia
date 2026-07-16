import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from pages.helpers.macro import gdp_functions as mf
from generalities.function import cap_series
from generalities.demography_generalities.population import MEN_COLOR, WOMEN_COLOR

def line_chart(data: pd.DataFrame, labels: dict, info: list, highlight: str = None):
    data = cap_series(data)
    fig = px.line(data, labels={data.index.name or "index": info[1], "value": info[2]})
    fig.update_layout(

        height=600,

        title={
            "text": info[0],
            "font": {"size": 25},
            "x": 0,
            "xanchor": "left"
        },

        margin=dict(l=50, r=20, t=80, b=0),
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
        dtick=1,
        tickangle=45,
        showgrid=False,
        tickfont=dict(size=15)
    )

    fig.update_layout(
        xaxis_title_font=dict(size=15),
        yaxis_title_font=dict(size=15),
    )

    fig.for_each_trace(lambda t: t.update(name = labels.get(t.name, t.name),
                                          hovertemplate = f"<b>%{{fullData.name}}</b><br>{info[1]}: %{{x}}<br>{info[2]}: %{{y:,.2f}}<extra></extra>"))

    if highlight:
        for trace in fig.data:
            if trace.name != highlight:
                trace.update(line=dict(color="rgba(180,180,180,0.3)"))

    fig.update_layout(legend_title_text="")

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            entrywidth=0,
            entrywidthmode="pixels"
        ),
        margin=dict(t=80)
    )
    return fig

def bar_chart(data: pd.DataFrame, labels: dict, info: list, highlight: str = None):
    data = cap_series(data)
    fig = px.bar(data, barmode="group", labels={data.index.name or "index": info[1], "value": info[2]})
    fig.update_layout(
        height=600,
        title={
            "text": info[0],
            "font": {"size": 25},
            "x": 0,
            "xanchor": "left"
        },
        margin=dict(l=50, r=20, t=80, b=0),
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
        dtick=1,
        tickangle=45,
        showgrid=False,
        tickfont=dict(size=15)
    )

    fig.update_layout(
        xaxis_title_font=dict(size=15),
        yaxis_title_font=dict(size=15),
    )

    fig.for_each_trace(lambda t: t.update(name=labels.get(t.name, t.name),
                                          hovertemplate=f"<b>%{{fullData.name}}</b><br>{info[1]}: %{{x}}<br>{info[2]}: %{{y:,.2f}}<extra></extra>"))

    if highlight:
        for trace in fig.data:
            if trace.name != highlight:
                trace.update(marker=dict(color="rgba(180,180,180,0.3)"))

    fig.update_layout(legend_title_text="")

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            entrywidth=0,
            entrywidthmode="pixels"
        ),
        margin=dict(t=80)
    )
    return fig


def line_or_bar(chart_type, data, info, labels=None, highlight=None,
                force_bar=False, bar_if_single=True):

    single_row = isinstance(data, pd.DataFrame) and len(data) == 1

    if chart_type == "Bar" or force_bar or (bar_if_single and single_row):
        if single_row:
            series = data.iloc[0]
            if labels:
                series.index = [labels.get(c, c) for c in series.index]
            return ranked_bar_chart(series, [info[0], info[2], ""])
        return bar_chart(data, labels or {}, info, highlight=highlight)

    return line_chart(data, labels or {}, info, highlight=highlight)


def ranked_bar_chart(series: pd.Series, info: list):
    data = series.sort_values(ascending=True)
    fmt = ",.0f" if (data == data.round()).all() else ",.2f"
    fig = px.bar(
        x=data.values,
        y=data.index.astype(str),
        orientation="h",
        labels={"x": info[1], "y": info[2]},
    )
    fig.update_layout(
        height=max(450, 42 * len(data)),
        title={"text": info[0], "font": {"size": 25}, "x": 0, "xanchor": "left"},
        margin=dict(l=50, r=20, t=80, b=0),
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
    df, df_local = mf.clean_annual_growth(df, year, president, index, quarter)
    if len(df_local) > 1:
        plot = px.bar if chart_type == "Bar" else px.line
        fig = plot(df_local, labels={"value": "Growth (%)", "Fecha": "Year"})

        fig.update_layout(

            height=600,

            title={
                "text": title,
                "font": {"size": 25},
                "x": 0,
                "xanchor": "left"
            },

            showlegend=False,
            margin=dict(l=50, r=20, t=80, b=0),
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
            dtick=1,
            tickangle=45,
            showgrid=False,
            tickfont=dict(size=15)
        )

        fig.update_layout(
            xaxis_title_font=dict(size=15),
            yaxis_title_font=dict(size=15),
        )

        fig.for_each_trace(lambda t: t.update(
            hovertemplate="<br>Year: %{x}<br>Growth (%): %{y:.2f}<extra></extra>"
        ))

    else:
        try:
            column = df_local.columns[index - 1]
            growth = df_local[column].iloc[0]
            min_growth = df[column].min()
            max_growth = df[column].max()
            avg_growth = df[column].median()
        except Exception:
            st.warning("There is no data for the selected filters")
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
                "suffix": " vs Median"
            },
            title = {"text": f"<b>{year[0]}{quarter} {title}</b>", "font": {"size": 24}},
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

        fig.update_layout(margin=dict(t=80, b=20, l=30, r=30), height=400)
    return fig


def render_chart(fig):
    st.plotly_chart(fig)
    msg = st.session_state.pop("chart_warning", None)
    if msg:
        st.warning(msg)

def indicator(data: pd.DataFrame, full_series: pd.Series, reference: float, info: list):
    title, valueformat, suffix, delta_suffix = info

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
        title = {"text": f"<b>{title}</b>", "font": {"size": 24}},
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

    fig.update_layout(margin=dict(t=80, b=20, l=30, r=30), height=400)
    return fig

def choropleth_map(data: pd.DataFrame, col: str, info: list):
    fig = px.choropleth(
        data,
        locations="Location",
        locationmode="country names",
        color=col,
        hover_name="Location",
        color_continuous_scale="Blues",
        labels={col: info[2]},
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" + info[2] + ": %{z:,.0f}<extra></extra>"
    )
    fig.update_geos(
        showocean=True,
        oceancolor="rgb(15, 30, 50)",
        showland=True,
        landcolor="rgb(45, 45, 45)",
        showframe=False,
        showcoastlines=True,
        coastlinecolor="rgb(80, 80, 80)",
    )
    fig.update_layout(
        height=600,
        title={"text": info[0], "font": {"size": 25}, "x": 0, "xanchor": "left"},
        margin=dict(l=50, r=20, t=80, b=0),
        coloraxis_colorbar=dict(title=info[2]),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def colombia_choropleth(data: pd.DataFrame, geojson: dict, feature_key: str, col: str, info: list,
                        val_fmt: str = ",.0f"):
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
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        height=600,
        title={"text": info[0], "font": {"size": 25}, "x": 0, "xanchor": "left"},
        margin=dict(l=50, r=20, t=80, b=0),
        coloraxis_colorbar=dict(title=info[2]),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig

def projection_line(data: pd.DataFrame, info: list, split_year: int, highlight: str = None, labels: dict = None):
    """Line chart where each series is solid up to `split_year` and dashed after it
    (projected years)."""
    data = cap_series(data)
    if isinstance(data, pd.Series):
        data = data.to_frame()
    labels = labels or {}
    palette = px.colors.qualitative.Plotly

    fig = go.Figure()
    for i, col in enumerate(data.columns):
        name = labels.get(col, col)
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
                hovertemplate=f"<b>{name} (projected)</b><br>{info[1]}: %{{x}}<br>{info[2]}: %{{y:,.0f}}<extra></extra>",
            ))

    fig.update_layout(
        height=600,
        title={"text": info[0], "font": {"size": 25}, "x": 0, "xanchor": "left"},
        margin=dict(l=50, r=20, t=80, b=0),
        xaxis_title=info[1], yaxis_title=info[2],
        xaxis_title_font=dict(size=15), yaxis_title_font=dict(size=15),
        legend_title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor="rgba(255, 255, 255, 0.1)",
                     tickfont=dict(size=15), tickformat=",.0f")
    fig.update_xaxes(type="category", dtick=1, tickangle=45, showgrid=False, tickfont=dict(size=15))
    return fig

def population_pyramid(men: pd.Series, women: pd.Series, info: list):
    """Diverging horizontal bars: men to the left (negative), women to the right.

    info = [title, value_label, valueformat]"""
    title, value_label, valueformat = info
    groups = list(men.index)
    maxv = max(men.max(), women.max()) or 1
    ticks = [(-maxv) + (2 * maxv) * k / 6 for k in range(7)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=groups, x=[-v for v in men.values], orientation="h", name=men.name,
        marker_color=MEN_COLOR, customdata=list(men.values),
        hovertemplate=f"<b>{men.name}</b><br>Age: %{{y}}<br>{value_label}: %{{customdata:{valueformat}}}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=groups, x=list(women.values), orientation="h", name=women.name,
        marker_color=WOMEN_COLOR,
        hovertemplate=f"<b>{women.name}</b><br>Age: %{{y}}<br>{value_label}: %{{x:{valueformat}}}<extra></extra>",
    ))
    fig.update_layout(
        barmode="overlay", bargap=0.1, height=600,
        title={"text": title, "font": {"size": 25}, "x": 0, "xanchor": "left"},
        margin=dict(l=50, r=20, t=80, b=0),
        xaxis_title=value_label, yaxis_title="Age group",
        xaxis_title_font=dict(size=15), yaxis_title_font=dict(size=15),
        legend_title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(tickvals=ticks, ticktext=[f"{abs(t):{valueformat}}" for t in ticks],
                     showgrid=False, gridwidth=0.5, gridcolor="rgba(255, 255, 255, 0.1)",
                     tickfont=dict(size=14))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=13), automargin=True)
    return fig
