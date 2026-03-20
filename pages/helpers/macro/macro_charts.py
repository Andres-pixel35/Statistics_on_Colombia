import plotly.express as px
import pandas as pd

def total_gdp_line(data: pd.DataFrame):
    fig = px.line(data, labels={"index": "Year", "value": "Billions (COP)"}, title="GDP per Year")
    fig.update_layout(

        height=600,

        title={
            "text": "GDP per Year",
            "font": {"size": 25}, 
            "x": 0,            
            "xanchor": 'left'
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

    return fig

