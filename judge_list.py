# -*- coding: utf-8 -*-
"""Ansicht: Judge_List"""
import pandas as pd
import streamlit as st
from core.data import load_labels, real_judges
from core.rounds import round_label, usable_rounds
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    display_header_with_logo("📊 Judge Book")
    st.write("Sieh sofort, welche Katzen in den jeweiligen Klassen direkt gegeneinander antreten.")
    
    df_full = load_labels()
    
    if df_full is not None:
        # Funktion zur Tabellen-Generierung, damit kein Code doppelt existiert oder gekürzt wird
        def render_judge_table(tag_key, r_col, suffix):
            # Alle Richter holen, die an diesem Tag aktiv sind
            all_j = sorted(real_judges(df_full[df_full[tag_key].astype(str).str.upper() == 'X'][r_col]))
            
            c1, c2 = st.columns(2)
            mein_richter = c1.selectbox("Richter filtern:", ["--"] + all_j, key=f"jl_judge_{suffix}")
            
            if mein_richter != "--":
                # Kategorien für diesen Richter ermitteln
                df_richter_alle = df_full[(df_full[tag_key].astype(str).str.upper() == 'X') & (df_full[r_col] == mein_richter)]
                verfuegbare_kategorien = sorted(list(set([str(cat).replace('.0', '') for cat in df_richter_alle['KATEGORIE'].unique() if pd.notna(cat)])))
                meine_kategorie = c2.selectbox("Kategorie filtern:", verfuegbare_kategorien, key=f"jl_cat_{suffix}")
                
                # Daten filtern und sortieren nach Katalog-Nr
                df_filtered = df_richter_alle[df_richter_alle['KATEGORIE'].astype(str).str.replace('.0', '') == meine_kategorie].sort_values('KATALOG-NR')
                
                st.divider()
                
                # --- ANZAHL DER KATZEN ANZEIGEN ---
                anzahl_katzen = len(df_filtered)
                st.markdown(f"**Gemeldete Katzen in dieser Auswahl:** {anzahl_katzen}")
                
                # Vorbereitung der Tabellendaten
                table_rows = []
                
                for _, row in df_filtered.iterrows():
                    nr = row['KAT_STR']
                    ems = row.get('RASSE_KURZ', row.get('RASSE', '')) + " " + row.get('FARBE', '')
                    sex = row.get('GESCHLECHT', 'N/A')
                    klasse = str(row.get('KLASSE_INTERNAL', row.get('AUSSTELLUNGSKLASSE', row.get('KLASSE', 'N/A')))).replace('.0', '')
                    
                    # Geburtsdatum formatieren
                    geb_cols = [c for c in row.index if "GEB" in c or "GEBURT" in c]
                    geb_datum = row[geb_cols[0]] if geb_cols else row.get('GEB_DATUM', 'N/A')
                    if isinstance(geb_datum, pd.Timestamp): 
                        geb_datum = geb_datum.strftime('%d.%m.%Y')
                    elif pd.isna(geb_datum) or str(geb_datum).strip().lower() == "nan": 
                        geb_datum = "–"
                    
                    # 8-Spalten Logik initialisieren
                    x_cols = {"Ad ♂": "", "Ad ♀": "", "K ♂": "", "K ♀": "", "11 ♂": "", "11 ♀": "", "12 ♂": "", "12 ♀": ""}
                    
                    # Automatische Zuordnung basierend auf Klasse und Geschlecht (Sex)
                    try:
                        kl_num = int(klasse)
                        
                        sex_clean = str(sex).strip().lower()
                        is_male = (sex_clean == "1,0" or sex_clean == "m")
                        
                        if kl_num in [1, 3, 5, 7, 9]:
                            x_cols["Ad ♂" if is_male else "Ad ♀"] = "X"
                        elif kl_num in [2, 4, 6, 8, 10]:
                            x_cols["K ♂" if is_male else "K ♀"] = "X"
                        elif kl_num == 11:
                            x_cols["11 ♂" if is_male else "11 ♀"] = "X"
                        elif kl_num == 12:
                            x_cols["12 ♂" if is_male else "12 ♀"] = "X"
                    except ValueError:
                        pass
                    
                    # Zeile zusammensetzen
                    row_entry = {
                        "Nr.": nr,
                        "EMS-Code": ems,
                        "Sex": sex,
                        "Kl.": klasse,
                        "Geboren": geb_datum,
                        **x_cols
                    }
                    table_rows.append(row_entry)
                
                if table_rows:
                    df_display = pd.DataFrame(table_rows)
                    
                    # Darstellung als sortierbare Streamlit-Tabelle
                    st.dataframe(
                        df_display, 
                        use_container_width=True, 
                        hide_index=True,
                        height=650,
                        column_config={
                            "Nr.": st.column_config.TextColumn(width="small"),
                            "Sex": st.column_config.TextColumn(width="small"),
                            "Kl.": st.column_config.TextColumn(width="small"),
                            "Ad ♂": st.column_config.TextColumn(alignment="center"),
                            "Ad ♀": st.column_config.TextColumn(alignment="center"),
                            "K ♂": st.column_config.TextColumn(alignment="center"),
                            "K ♀": st.column_config.TextColumn(alignment="center"),
                            "11 ♂": st.column_config.TextColumn(alignment="center"),
                            "11 ♀": st.column_config.TextColumn(alignment="center"),
                            "12 ♂": st.column_config.TextColumn(alignment="center"),
                            "12 ♀": st.column_config.TextColumn(alignment="center"),
                        }
                    )
                    
                    st.caption("💡 Tipp: Klicke auf die Spaltenköpfe (z.B. '12 ♀'), um die Katzen zu sortieren und Konkurrenten direkt im Blick zu haben!")
                else:
                    st.info("Keine Katzen für diese Auswahl gemeldet.")
            else:
                st.info("Bitte wähle einen Richter aus der Liste aus, um die Judge List anzuzeigen.")

        # Ein Tab pro Runde (Gelb / Grün / Rot)
        runden = usable_rounds(store, df_full)
        tabs = st.tabs([round_label(n) for n in runden])
        for tab, n in zip(tabs, runden):
            with tab:
                render_judge_table(f"TAG {n}", f"RICHTER TAG {n}", f"t{n}")
            
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_judgebook"):
        set_view("Home")




# --- EIGENSTÄNDIGE VIEW: NOMINATION LABELS DRUCK ---
