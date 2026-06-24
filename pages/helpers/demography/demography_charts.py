import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from generalities.function import cap_series
from generalities.demography_generalities.population import MEN_COLOR, WOMEN_COLOR

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

def population_pyramid(men: pd.Series, women: pd.Series, info: list, projected: bool = False):
    """Diverging horizontal bars: men to the left (negative), women to the right.

    info = [title, value_label, valueformat]"""
    title, value_label, valueformat = info
    groups = list(men.index)
    title = title + (" — projected" if projected else "")
    maxv = max(men.max(), women.max()) or 1
    ticks = [(-maxv) + (2 * maxv) * k / 6 for k in range(7)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=groups, x=[-v for v in men.values], orientation="h", name="Men",
        marker_color=MEN_COLOR, customdata=list(men.values),
        hovertemplate=f"<b>Men</b><br>Age: %{{y}}<br>{value_label}: %{{customdata:{valueformat}}}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=groups, x=list(women.values), orientation="h", name="Women",
        marker_color=WOMEN_COLOR,
        hovertemplate=f"<b>Women</b><br>Age: %{{y}}<br>{value_label}: %{{x:{valueformat}}}<extra></extra>",
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
