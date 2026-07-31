import re
import textwrap
import streamlit as st

def is_mobile() -> bool:
    ua = st.context.headers.get("User-Agent", "")
    return bool(re.search(r"Mobile|Android|iPhone", ua))

def _wrap_title(text: str, width: int = 28) -> str:
    """Break a title into multiple lines via <br> so mobile's narrow
    viewport doesn't clip Plotly's title, which never wraps on its own."""
    if not is_mobile():
        return text
    return "<br>".join(textwrap.wrap(text, width=width)) or text

def _title(text: str, size: int = 25) -> dict:
    return {
        "text": _wrap_title(text),
        "font": {"size": 16 if is_mobile() else size},
        "x": 0,
        "xanchor": "left",
    }

def _top_margin(base: int = 80) -> int:
    """Extra headroom on mobile so a wrapped multi-line title doesn't
    overlap the plot area."""
    return base + 40 if is_mobile() else base

def _gauge_title(text: str, size: int = 24) -> dict:
    return {
        "text": f"<b>{_wrap_title(text)}</b>",
        "font": {"size": 16 if is_mobile() else size},
    }

def _map_layout(colorbar_title: str) -> dict:
    """Map layout (height/margin/colorbar): on mobile the vertical colorbar eats a
    big chunk of the narrow width, so move it under the map instead."""
    if is_mobile():
        return dict(
            height=600,
            margin=dict(l=10, r=10, t=_top_margin(70), b=90),
            coloraxis_colorbar=dict(title=colorbar_title, orientation="h", y=-0.15, thickness=12, len=0.9),
        )
    return dict(
        height=600,
        margin=dict(l=50, r=20, t=80, b=0),
        coloraxis_colorbar=dict(title=colorbar_title),
    )

def _legend(n_series: int) -> dict:
    """Legend layout. Desktop: horizontal centered legend. Mobile with several
    series: vertical list below the chart so each entry gets its own
    full-width row instead of wrapping/overlapping."""
    if is_mobile() and n_series > 4:
        return dict(orientation="v", yanchor="top", y=-0.3, xanchor="left", x=0,
                     font=dict(size=11))
    return dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)

def _bottom_margin(n_series: int) -> int:
    """Extra footer room on mobile so a stacked legend doesn't overlap the
    x-axis tick labels. 70px reserved for the ticks themselves before the
    legend rows start."""
    if is_mobile() and n_series > 4:
        return 70 + n_series * 22
    return 0

def _chart_height(n_series: int, base: int = 600) -> int:
    """Total figure height: base plot area plus whatever extra bottom margin
    the stacked mobile legend needs, so the plot area itself doesn't shrink."""
    return base + _bottom_margin(n_series)

def _category_ticks(n: int) -> dict:
    """X-axis tick config for a categorical axis with n categories.
    On mobile, thin the ticks and shrink the font so labels stop overlapping."""
    if is_mobile() and n > 8:
        return dict(dtick=-(-n // 8), tickangle=90, tickfont=dict(size=11))
    return dict(dtick=1, tickangle=45, tickfont=dict(size=15))

if __name__ == "__main__":
    import unittest.mock as mock
    long_title = "A very long chart title that would not fit on a narrow phone screen"
    with mock.patch(f"{__name__}.is_mobile", return_value=True):
        wrapped = _wrap_title(long_title)
        assert "<br>" in wrapped
        assert all(len(line) <= 28 for line in wrapped.split("<br>"))
    with mock.patch(f"{__name__}.is_mobile", return_value=False):
        assert _wrap_title(long_title) == long_title
    print("mobile.py title-wrap self-check passed")
