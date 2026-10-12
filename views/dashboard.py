# -*- coding: utf-8 -*-
"""Ansicht: Dashboard"""
from streamlit_autorefresh import st_autorefresh
import streamlit as st
from core.data import get_full_label, load_labels
from core.store import get_store
from core.ui import display_header_with_logo


def render():
    store = get_store()
    display_header_with_logo("📢 Live-Aufruf & Status")
    
    # Holt sich den vom Admin festgesetzten Tag (völlig immun gegen das st_autorefresh)
    admin_day = store.data.get("admin_selected_day", "Tag 1")
    tag = "TAG 2" if "2" in str(admin_day) else "TAG 1"
    
    # Passive Info-Anzeige in der Seitenleiste
    st.sidebar.info(f"📅 Aktiver Ausstellungstag: {tag}")
    
    df_full = load_labels()
    if df_full is not None:
        r_col = f"RICHTER {tag}"
        
        # Filtert das Excel NUR auf Zeilen, die am aktuellen Tag ein 'X' haben
        df_tag = df_full[df_full[tag].astype(str).str.upper() == 'X'].copy()
        
        judges = sorted([r for r in df_tag[r_col].unique() if str(r) != "nan"])
        if judges:
            cols = st.columns(len(judges))
            for i, j in enumerate(judges):
                with cols[i]:
                    st.markdown(f"<div class='judge-header-box'>{j}</div>", unsafe_allow_html=True)
                    
                    judge_entries = []
                    for k, v in store.data.items():
                        if "|" in k and k.split("|")[1] == j:
                            kat_nr = k.split("|")[0]
                            
                            # PRÜFUNG: Existiert die Katze am aktuellen Tag bei diesem Richter?
                            m = df_tag[(df_tag['KAT_STR'] == kat_nr) & (df_tag[r_col] == j)]
                            
                            if not m.empty:  # Nur verarbeiten, wenn sie zum aktuellen Tag gehört!
                                flags = v.get("flags", {}) if isinstance(v, dict) else {}
                                beim_richten = flags.get("Zum Richten", False) and not flags.get("Gerichtet", False)
                                
                                # --- NEU: HOLE DEN STATUS OB DIE KATZE GERADE AUF DEM TISCH IST ---
                                wird_gerichtet = flags.get("Wird gerichtet", False) and not flags.get("Gerichtet", False)
                                # -----------------------------------------------------------------
                                
                                nominiert = flags.get("NOM", False)
                                biv = flags.get("BIV", False)
                                
                                # --- ÄNDERUNG: ERWEITERT UM "WIRD_GERICHTET", DAMIT DIE KARTE GEZEIGT WIRD ---
                                if beim_richten or wird_gerichtet or nominiert or biv:
                                    judge_entries.append({
                                        "key": k, 
                                        "data": v if isinstance(v, dict) else {"flags": {}},
                                        "row_data": m.iloc[0]  # Daten merken fürs spätere Anzeigen
                                    })
                    
                    #judge_entries.sort(key=lambda x: x["data"].get("timestamp", 0))
                    judge_entries.sort(key=lambda x: (not x["data"].get("flags", {}).get("Wird gerichtet", False), x["data"].get("timestamp", 0)))

                    
                    for entry in judge_entries:
                        kat_nr = entry["key"].split("|")[0]
                        flags = entry["data"].get("flags", {})
                        m_row = entry["row_data"]
                        
                        # --- NEU: DESIGN-WEICHE FÜR DAS ORANGE BLINKEN AUF DEM DASHBOARD ---
                        rendered_tags = []
                        for t, val in flags.items():
                            if val and t != "Gerichtet":
                                # LOGIK: FALLS "WIRD GERICHTET" AKTIV IST, BLENDEN WIR DAS BLAUE "ZUM RICHTEN" AUS
                                if t == "Zum Richten" and flags.get("Wird gerichtet"):
                                    continue
                                
                                # ENTFERNT LEERZEICHEN FÜR DEN CSS-KLASSENNAMEN (AUS "Wird gerichtet" WIRD "wirdgerichtet")
                                class_suffix = t.lower().replace(" ", "")
                                rendered_tags.append(f"<span class='tag tag-{class_suffix}'>{t}</span>")
                        
                        tags_html = "".join(rendered_tags)
                        # --------------------------------------------------------------------
                        
                        if tags_html: 
                            st.markdown(f"""
                                <div class='cat-card dash-big'>
                                    <div class='cat-number'>{kat_nr}</div>
                                    <div class='cat-details'>{get_full_label(m_row)}</div>
                                    <div class='tag-container'>{tags_html}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            
    st_autorefresh(interval=10000, key="dash_refresh")


# STEWARD PANEL
