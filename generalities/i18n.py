import re
import streamlit as st
from generalities.translations import UI_ES, OVERRIDES, REVERSED_DICTS

def _clean(sp: str) -> str:
    """Make a raw Spanish CSV value presentable."""
    sp = re.sub(r"^\d+\s+", "", str(sp))    # leading DANE codes: "101 Enfermedades…"
    sp = re.sub(r"[\^*]+$", "", sp)          # trailing footnote markers: "…desechos^"
    return re.sub(r"\s+", " ", sp).strip()

def _build() -> dict:
    es = dict(UI_ES)
    for d in REVERSED_DICTS:                 # {spanish_csv: english} term dicts
        for sp, en in d.items():
            es.setdefault(en, _clean(sp))    # setdefault: many-to-one keeps first
    es.update(OVERRIDES)                     # curated always wins
    # Safety: a Spanish output must never itself be an EN key with a different
    # translation, or t() output would re-translate. Assert at import time.
    for en, sp in es.items():
        assert es.get(sp, sp) == sp, f"double-translation risk: {en!r} -> {sp!r}"
    return es

_ES = _build()
_ES_SEP = str.maketrans(",.", ".,")

def get_lang() -> str:
    if "lang" not in st.session_state:
        loc = st.context.locale or ""
        st.session_state["lang"] = "es" if loc.lower().startswith("es") else "en"
    return st.session_state["lang"]

def t(s):
    if get_lang() == "en" or not isinstance(s, str):
        return s
    return _ES.get(s, s)

def language_selector() -> None:
    get_lang()  # ensure detection ran
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover(":material/language:"):
            st.radio("Language / Idioma", ["en", "es"], key="lang",
                     format_func={"en": "English", "es": "Español"}.get)

def fmt_num(x, spec: str = ",.0f") -> str:
    out = format(x, spec)
    return out.translate(_ES_SEP) if get_lang() == "es" else out

def fmt_date(d, fmt: str) -> str:
    """strftime that renders month names in the active language (process locale untouched)."""
    out = d.strftime(fmt)
    if get_lang() == "es":
        full_en = d.strftime("%B")
        full_es = _ES.get(full_en, full_en)
        if "%B" in fmt:
            out = out.replace(full_en, full_es)
        if "%b" in fmt:
            out = out.replace(d.strftime("%b"), full_es[:3])  # Spanish 3-letter abbrev = first 3 letters
    return out
