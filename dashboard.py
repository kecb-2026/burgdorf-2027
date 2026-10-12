# -*- coding: utf-8 -*-
"""Ansicht: Dashboard"""
from streamlit_autorefresh import st_autorefresh
import streamlit as st
from core.data import get_full_label, load_labels
from core.rounds import all_judges, default_round, judge_cats, judge_round, round_color, round_label, round_on_color, round_tint, tag_of
from core.store import get_store
from core.ui import display_header_with_logo, judge_header_html


def render():
    store = get_store()
    display_header_with_logo("📢 Live-Aufruf & Status")
    
    # Jeder Richter hat seine eigene Runde (Rundenmanager). Es koennen mehrere Runden gleichzeitig laufen.
    st.sidebar.info(f"🎛️ Standard-Runde: {round_label(default_round(store))}")
    
    df_full = load_labels()
    if df_full is not None:
        # Nur Richter zeigen, die in ihrer aktuellen Runde Katzen haben
        judges = [j for j in all_judges(df_full) if not judge_cats(df_full, j, judge_round(store, j)).empty]
        if judges:
            cols = st.columns(len(judges))
            for i, j in enumerate(judges):
                rn = judge_round(store, j)
                tag = tag_of(rn)
                r_col = f"RICHTER {tag}"
                df_tag = judge_cats(df_full, j, rn)
                r_color, r_tint, r_on, r_text = round_color(rn), round_tint(rn), round_on_color(rn), round_label(rn, with_emoji=False)
                with cols[i]:
                    st.markdown(judge_header_html(j, judges, bg=r_color, fg=r_on, border=r_color, sub=r_text), unsafe_allow_html=True)
                    
                    judge_entries = []
                    for k, v in store.data.items():
                        if "|" in k and k.split("|")[1] == j:
                            kat_nr = k.split("|")[0]
                            
                            # PRÜFUNG: Existiert die Katze am aktuellen Tag bei diesem Richter?
                            m = df_tag[df_tag['KAT_STR'] == kat_nr]
                            
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
                                <div class='cat-card dash-big' style='background-color:{r_tint}; border-color:{r_color};'>
                                    <div class='cat-number'>{kat_nr}</div>
                                    <div class='cat-details'>{get_full_label(m_row)}</div>
                                    <div class='tag-container'>{tags_html}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            
    st_autorefresh(interval=10000, key="dash_refresh")


# STEWARD PANEL
