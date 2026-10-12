# -*- coding: utf-8 -*-
"""Ansicht: Steward_Panel"""
import pandas as pd
import streamlit as st
import time
from core.config import FIFe_KLASSEN_NAMEN
from core.data import get_full_label, load_labels, real_judges
from core.store import get_store
from core.ui import display_header_with_logo


def render():
    store = get_store()
    display_header_with_logo("📝 Steward-Pult")
    df_full = load_labels()
    
    if df_full is not None:
        # 1. Prüfen, ob ein Richter via QR-Code übergeben wurde
        url_judge_name = st.session_state.get("url_judge", "--")
        
        # 2. Automatisch ermitteln, welcher Tag gilt (Standard ist der sichere ADMIN-TAG)
        admin_day = store.data.get("admin_selected_day", "Tag 1")
        calculated_tag = "TAG 2" if "2" in str(admin_day) else "TAG 1"
        
        # Falls in der URL explizit ein Tag steht (?day=2), überschreibt dieser den Admin-Tag
        url_day = st.query_params.get("day", None)
        if url_day == "1":
            calculated_tag = "TAG 1"
        elif url_day == "2":
            calculated_tag = "TAG 2"
        
        # 3. Wenn ein Richtername übergeben wurde, deine originale Logik prüfen:
        if url_judge_name != "--":
            j_t1 = real_judges(df_full['RICHTER TAG 1']) if 'RICHTER TAG 1' in df_full.columns else []
            j_t2 = real_judges(df_full['RICHTER TAG 2']) if 'RICHTER TAG 2' in df_full.columns else []
            
            if url_judge_name in j_t2 and url_judge_name not in j_t1:
                calculated_tag = "TAG 2"
        
        # Finale Zuweisung an die Variable tag für die Spaltennamen
        tag = calculated_tag.upper()
        
        # Nur noch eine passive Info-Anzeige in der Sidebar statt einem störenden Radio-Button
        st.sidebar.info(f"📅 Aktiver Ausstellungstag: {tag}")
        
        r_col = f"RICHTER {tag}"
        all_j = sorted(real_judges(df_full[df_full[tag].astype(str).str.upper() == 'X'][r_col]))
        
        # Berechnen des Default-Index für die Richter-Selectbox
        default_idx = 0
        if url_judge_name in all_j:
            default_idx = all_j.index(url_judge_name) + 1 # +1 wegen dem "--" Eintrag
            
        mein_richter = st.selectbox("Richter wählen:", ["--"] + all_j, index=default_idx)

        # --- WARNHINWEIS FÜR ABWEICHENDEN RICHTER ---
        if url_judge_name != "--" and mein_richter != "--" and mein_richter != url_judge_name:
            st.error(
                f"🚨 **ACHTUNG! Sie verlassen gerade Ihren zugewiesenen Richter!**\n\n"
                f"Sie sind ursprünglich eingeloggt für **{url_judge_name}**, "
                f"steuern aber aktuell die Katzenliste für **{mein_richter}**."
            )

        if mein_richter != "--":
            df_richter_alle = df_full[(df_full[tag].astype(str).str.upper() == 'X') & (df_full[r_col] == mein_richter)]
            verfuegbare_kategorien = sorted(list(set([str(cat).replace('.0', '') for cat in df_richter_alle['KATEGORIE'].unique() if pd.notna(cat)])))
            meine_kategorie = st.selectbox("Kategorie wählen:", verfuegbare_kategorien)
            
            df_j = df_richter_alle[df_richter_alle['KATEGORIE'].astype(str).str.replace('.0', '') == meine_kategorie].sort_values('KATALOG-NR')
            st.divider()
            
            for _, row in df_j.iterrows():
                nr = row['KAT_STR']
                k = f"{nr}|{mein_richter}"
                
                # Spalten flexibel auslesen
                klasse = row.get('KLASSE_INTERNAL', row.get('AUSSTELLUNGSKLASSE', row.get('KLASSE', 'N/A')))
                try:
                    klasse_int = int(str(klasse).replace('.0', ''))
                    klasse_anzeige = FIFe_KLASSEN_NAMEN.get(klasse_int, str(klasse))
                except (ValueError, TypeError):
                    klasse_anzeige = str(klasse)


                fg_cols = [c for c in row.index if "FARBGRUPPE" in c or "FARB-GRUPPE" in c]
                farbgruppe = row[fg_cols[0]] if fg_cols else row.get('FARBGRUPPE', 'N/A')
                if pd.isna(farbgruppe) or str(farbgruppe).strip().lower() == "nan": farbgruppe = "N/A"
                
                

                geschlecht = row.get('GESCHLECHT', 'N/A')
				#geschlecht = row.get('GESCHLECHT', 'N/A')

                # --- NEU: Prüfen, ob die Katze kastriert ist ---
                kastriert_wert = str(row.get('KASTRIERT', '')).strip()
                # Wenn in der Spalte ein Wert steht (z.B. ein 'X' oder 'Ja'), bauen wir den Vermerk zusammen
                is_kastriert = kastriert_wert != '' and kastriert_wert != '-' and kastriert_wert.lower() != 'nan'
                geschlecht_anzeige = f"{geschlecht} (kastriert)" if is_kastriert else geschlecht

                

				
                geb_cols = [c for c in row.index if "GEB" in c or "GEBURT" in c]
                geb_datum = row[geb_cols[0]] if geb_cols else row.get('GEB_DATUM', 'N/A')
                if isinstance(geb_datum, pd.Timestamp): geb_datum = geb_datum.strftime('%d.%m.%Y')
                elif pd.isna(geb_datum) or str(geb_datum).strip().lower() == "nan": geb_datum = "N/A"
                
                # --- STRUKTUR INITIALISIEREN (Dashboard-konform) ---
                # Wenn die Katze noch gar nicht im Store existiert, als Dict anlegen
                if k not in store.data or not isinstance(store.data[k], dict):
                    store.data[k] = {}
                
                # Falls "flags" fehlt oder kein Dict ist, sauber initialisieren
                if "flags" not in store.data[k] or not isinstance(store.data[k]["flags"], dict):
                    store.data[k]["flags"] = {
                        "Zum Richten": False, 
                        "Wird gerichtet": False, 
                        "BIV": False, 
                        "NOM": False, 
                        "Gerichtet": False
                    }
                
                if "timestamp" not in store.data[k]:
                    store.data[k]["timestamp"] = 0.0
                
                # Lokale Referenz für einfachere Handhabung im UI-Code
                flags = store.data[k]["flags"]
                card_class = "steward-card-wrapper gerichtet" if flags.get("Gerichtet") else "steward-card-wrapper"
                
                # START DES GRAUEN RECHTECKS
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="card-header-row">
                        <span class="card-cat-number">Nr. {nr}</span>
                        <span class="card-meta-main">{get_full_label(row)}</span>
                    </div>
                    <div class="grid-container">
                        <span class="card-meta-sub"><span class="meta-label">Klasse:</span> {klasse_anzeige}</span>
                        <span class="card-meta-sub"><span class="meta-label">Farbgruppe:</span> {farbgruppe}</span>
                        <span class="card-meta-sub"><span class="meta-label">Geschlecht:</span> {geschlecht_anzeige}</span>
                        <span class="card-meta-sub"><span class="meta-label">Geboren:</span> {geb_datum}</span>
                    </div>
                    <div style="border-top: 1px solid #e2e2e2; padding-top: 10px; margin-top: 12px; margin-bottom: 8px;"></div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3, c4, c5 = st.columns(5, vertical_alignment="center")
                
                # BUTTON 1: AUFRUFEN (Blau)
                is_rich = flags.get("Zum Richten")
                with c1:
                    if is_rich and not flags.get("Wird gerichtet"): st.markdown('<div class="st-blink-btn">', unsafe_allow_html=True)
                    if st.button("⚠️ [ AKTIV ] AUFGERUFEN ⚠️" if (is_rich and not flags.get("Wird gerichtet")) else "AUFRUFEN", key=f"btn_rich_{k}"):
                        store.data[k]["flags"]["Zum Richten"] = not is_rich
                        if store.data[k]["flags"]["Zum Richten"]:
                            store.data[k]["flags"]["Gerichtet"] = False
                            store.data[k]["timestamp"] = time.time()
                        else:
                            store.data[k]["flags"]["Wird gerichtet"] = False
                        
                        store.save_backup()
                        st.rerun()
                    if is_rich and not flags.get("Wird gerichtet"): st.markdown('</div>', unsafe_allow_html=True)
                
                # BUTTON 2: WIRD GERICHTET (Orange)
                is_busy = flags.get("Wird gerichtet")
                with c2:
                    if is_busy: st.markdown('<div class="st-blink-btn">', unsafe_allow_html=True)
                    if st.button("⏳ TISCH / RICHTEN ⏳" if is_busy else "WIRD GERICHTET", key=f"btn_busy_{k}"):
                        store.data[k]["flags"]["Wird gerichtet"] = not is_busy
                        if store.data[k]["flags"]["Wird gerichtet"]:
                            store.data[k]["flags"]["Zum Richten"] = True 
                            store.data[k]["flags"]["Gerichtet"] = False
                            store.data[k]["timestamp"] = time.time()
                        
                        store.save_backup()
                        st.rerun()
                    if is_busy: st.markdown('</div>', unsafe_allow_html=True)

                # BUTTON 3: BIV (Grün)
                is_biv = flags.get("BIV")
                with c3:
                    if is_biv: st.markdown('<div class="st-blink-btn">', unsafe_allow_html=True)
                    if st.button("⚠️ [ AKTIV ] BIV ⚠️" if is_biv else "BIV", key=f"btn_biv_{k}"):
                        store.data[k]["flags"]["BIV"] = not is_biv
                        store.data[k]["timestamp"] = time.time()
                        
                        store.save_backup()
                        st.rerun()
                    if is_biv: st.markdown('</div>', unsafe_allow_html=True)
                
                # BUTTON 4: NOMINIEREN (Gelb)
                is_nom = flags.get("NOM")
                with c4:
                    if is_nom: st.markdown('<div class="st-blink-btn">', unsafe_allow_html=True)
                    if st.button("⚠️ [ AKTIV ] NOM ⚠️" if is_nom else "NOM", key=f"btn_nom_{k}"):
                        store.data[k]["flags"]["NOM"] = not is_nom
                        if store.data[k]["flags"]["NOM"]:
                            store.data[k]["timestamp"] = time.time()
                        
                        store.save_backup()
                        st.rerun()
                    if is_nom: st.markdown('</div>', unsafe_allow_html=True)
                
                # BUTTON 5: GERICHTET (Grau)
                is_done = flags.get("Gerichtet")
                with c5:
                    if st.button("[ ERLEDIGT ] GERICHTET" if is_done else "GERICHTET", key=f"btn_done_{k}"):
                        if not is_done:
                            store.data[k]["flags"]["Zum Richten"] = False
                            store.data[k]["flags"]["Wird gerichtet"] = False
                            store.data[k]["flags"]["Gerichtet"] = True
                        else:
                            store.data[k]["flags"]["Gerichtet"] = False
                        
                        store.save_backup()
                        st.rerun()
                                
                # ENDE DES GRAUEN RECHTECKS
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown('<hr style="border: none; border-top: 2px solid #000; margin-top: 0px; margin-bottom: 30px;">', unsafe_allow_html=True)

# JUDGE VOTING
