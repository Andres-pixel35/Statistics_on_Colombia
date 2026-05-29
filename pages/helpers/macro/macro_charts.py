import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from pages.helpers.macro import macro_functions as mf

def line_chart(data: pd.DataFrame, labels: dict, info: list, highlight: str = None):
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

def ranked_bar_chart(series: pd.Series, info: list):
    data = series.sort_values(ascending=True)
    fig = px.bar(
        x=data.values,
        y=data.index.astype(str),
        orientation="h",
        labels={"x": info[1], "y": info[2]},
    )
    fig.update_layout(
        height=max(400, 18 * len(data)),
        title={"text": info[0], "font": {"size": 25}, "x": 0, "xanchor": "left"},
        margin=dict(l=50, r=20, t=80, b=0),
        showlegend=False,
        xaxis_title_font=dict(size=15),
        yaxis_title_font=dict(size=15),
    )
    fig.update_xaxes(
        showgrid=True, gridwidth=0.5, gridcolor="rgba(255, 255, 255, 0.1)",
        tickfont=dict(size=15), tickformat=",.0f",
    )
    fig.update_yaxes(showgrid=False, tickfont=dict(size=13))
    fig.update_traces(
        marker_color="darkblue",
        hovertemplate=f"<b>%{{y}}</b><br>{info[1]}: %{{x:,.0f}}<extra></extra>",
    )
    return fig

def colombia_choropleth(data: pd.DataFrame, geojson: dict, feature_key: str, col: str, info: list):
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
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" + info[2] + ": %{z:,.0f}<extra></extra>"
    )
    fig.update_layout(
        height=600,
        title={"text": info[0], "font": {"size": 25}, "x": 0, "xanchor": "left"},
        margin=dict(l=50, r=20, t=80, b=0),
        coloraxis_colorbar=dict(title=info[2]),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig

def gdp_growth(df: pd.DataFrame, year: list, president: str, index: int, quarter: str|None):
    df, df_local = mf.clean_annual_growth(df, year, president, index, quarter)
    if len(df_local) > 1:
        fig = px.line(df_local, labels={"value": "Growth (%)", "Fecha": "Year"})

        fig.update_layout(

            height=600,

            title={
                "text": "Real Annual GDP Growth",
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
            st.warning("Remember to press 'Show all years' if you want to select a year prior to 2000")
            st.stop()

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
            title = {"text": f"<b>{year[0]}-{quarter} GDP Growth</b>", "font": {"size": 24}},
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
