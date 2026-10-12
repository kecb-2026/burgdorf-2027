# -*- coding: utf-8 -*-
"""Excel laden und Katzen-Label-Texte."""
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
    return _load_labels_cached(store.data.get("admin_selected_day", "Tag 1"))


@st.cache_data(ttl=600)
def _load_labels_cached(day_selector):
    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl', header=0)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.fillna("-")
        df['KLASSE_INTERNAL'] = df['AUSSTELLUNGSKLASSE'] if 'AUSSTELLUNGSKLASSE' in df.columns else df.get('KLASSE', '')
        if 'KATALOG-NR' in df.columns:
            df['KAT_STR'] = df['KATALOG-NR'].astype(str).str.replace('.0', '', regex=False)

       # --- NEU: ABSOLUT RISIKO-FREIE WEICHE FÜR TAG 1 & TAG 2 ---
        # Wir prüfen, welcher Tag im globalen Sidebar-Radio-Button gewählt ist
        # Falls der Selector auf "Tag 2" steht, nehmen wir SELECTION 2, sonst SELECTION 1
        #day_selector = st.session_state.get("judge_day_selector", "Tag 1")
        
       # if "2" in str(day_selector):
        #    df['SELECTION'] = df['SELECTION 2'] if 'SELECTION 2' in df.columns else df.get('SELECTION', '-')
       # else:
        #    df['SELECTION'] = df['SELECTION 1'] if 'SELECTION 1' in df.columns else df.get('SELECTION', '-')
        # -----------------------------------------------------------
# --- NEU: FEHLERTOLERANTE WEICHE FÜR TAG 1 & TAG 2 ---
        #day_selector = st.session_state.get("judge_day_selector", "Tag 1")
        
        if "2" in str(day_selector):
            if 'SELECTION 2' in df.columns:
                df['SELECTION'] = df['SELECTION 2'].astype(str).str.strip().str.upper()
            else:
                df['SELECTION'] = df.get('SELECTION', '-').astype(str).str.strip().str.upper()
        else:
            if 'SELECTION 1' in df.columns:
                df['SELECTION'] = df['SELECTION 1'].astype(str).str.strip().str.upper()
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
