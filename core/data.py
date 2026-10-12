# -*- coding: utf-8 -*-
"""Excel laden und Katzen-Label-Texte."""
import re
import pandas as pd
import streamlit as st
from core.config import EXCEL_FILE
from core.store import get_store


def roman_to_numeric(text):
    if pd.isna(text) or text == "": 
        return ""
    return str(text)


def load_labels():
    store = get_store()
    day = store.data.get("admin_selected_day", "Tag 1")
    df = _load_labels_cached(day)
    if df is None:
        return None
    # Importierte Nominierungslisten (PDF) ueberschreiben SELECTION n
    from core.imports import apply_nom_overrides
    df = apply_nom_overrides(df, store)
    m_sel = re.search(r"\d+", str(day))
    sel_col = f"SELECTION {m_sel.group() if m_sel else 1}"
    if sel_col in df.columns:
        df = df.copy() if df is not None else df
        df['SELECTION'] = df[sel_col].astype(str).str.strip().str.upper()
    return df


load_labels.clear = lambda: _load_labels_cached.clear()


@st.cache_data(ttl=600)
def _load_labels_cached(day_selector):
    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl', header=0)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.fillna("-")
        df['KLASSE_INTERNAL'] = df['AUSSTELLUNGSKLASSE'] if 'AUSSTELLUNGSKLASSE' in df.columns else df.get('KLASSE', '')
        if 'KATALOG-NR' in df.columns:
            df['KAT_STR'] = df['KATALOG-NR'].astype(str).str.replace('.0', '', regex=False)

        # SELECTION gehoert zur Runde: 'Tag 1' -> SELECTION 1, 'Tag 2' -> SELECTION 2, 'Tag 3' -> SELECTION 3
        m_sel = re.search(r"\d+", str(day_selector))
        sel_col = f"SELECTION {m_sel.group() if m_sel else 1}"
        if sel_col in df.columns:
            df['SELECTION'] = df[sel_col].astype(str).str.strip().str.upper()
        else:
            df['SELECTION'] = df.get('SELECTION', '-').astype(str).str.strip().str.upper()
        # -----------------------------------------------------------
		
        return df
    except:
        return None


def get_full_label(row):
    r = str(row.get('RASSE_KURZ', row.get('RASSE', ''))).strip()
    fg_col = [c for c in row.index if "FARBGRUPPE" in c or "FARB-GRUPPE" in c]
    fg_val = row[fg_col[0]] if fg_col else row.get('FARBGRUPPE', '')
    g = roman_to_numeric(fg_val)
    e = str(row.get('FARBE', '')).strip()
    
    g_str = str(g).strip() if g is not None else ""
    
    if g_str and g_str != "-" and g_str.lower() != "nan":
        return f"{r} {g_str}, {e}".strip()
    else:
        return f"{r} {e}".strip()


def real_judges(series):
    """Echte Richternamen aus einer Excel-Spalte (ohne leere Felder, nan und -)."""
    names = {str(r).strip() for r in series.unique()}
    return sorted(n for n in names if n and n.lower() != "nan" and n != "-")


def with_selection(df, tag):
    """Kopie des Dataframes, in der 'SELECTION' zur Runde gehoert (z. B. tag='TAG 2' -> SELECTION 2)."""
    n = re.search(r"\d+", str(tag))
    col = f"SELECTION {n.group() if n else 1}"
    out = df.copy()
    if col in out.columns:
        out['SELECTION'] = out[col].astype(str).str.strip().str.upper()
    return out
