import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pages.helpers.macro import macro_functions as mf

def total_gdp_line(data: pd.DataFrame, labels: dict):
    fig = px.line(data, labels={"index": "Year", "value": "Billions (COP)"})
    fig.update_layout(

        height=600,

        title={
            "text": "GDP per Year",
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
                                          hovertemplate = "<b>%{fullData.name}</b><br>Year: %{x}<br>Billions (COP): %{y}<extra></extra>"))

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

def total_gdp_bar(data: pd.DataFrame, labels: dict):
    fig = px.bar(data, barmode="group", labels={"index": "Year", "value": "Billions (COP)"})
    fig.update_layout(
        height=600,
        title={
            "text": "GDP per Year",
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

    fig.for_each_trace(lambda t: t.update(name=labels.get(t.name, t.name),
                                          hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Billions (COP): %{y}<extra></extra>"))

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

def gdp_growth(df: pd.DataFrame, year: list, presiden: str, index: int, quarter: str|None):
    df, df_local = mf.clean_annual_growth(df, year, presiden, index, quarter)
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
        column = df_local.columns[index - 1] 
        growth = df_local[column].iloc[0]
        min_growth = df[column].min()
        max_growth = df[column].max()
        avg_growth = df[column].median()

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
            title = {"text": f"<b>{year[0]} GDP Growth</b>", "font": {"size": 24}},
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
