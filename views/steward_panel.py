# -*- coding: utf-8 -*-
"""Ansicht: Steward_Panel"""
import pandas as pd
import streamlit as st
import time
from core.config import FIFe_KLASSEN_NAMEN
from core.data import get_full_label, load_labels
from core.rounds import all_judges, busy_elsewhere, judge_cats, judge_round, round_color, round_label, round_tint, tag_of
from core.gate import get_show_day, is_open as is_cat_open
from core.imports import is_absent
from core.store import get_store
from core.ui import display_header_with_logo


def render():
    store = get_store()
    display_header_with_logo("📝 Steward-Pult")
    df_full = load_labels()
    
    if df_full is not None:
        # 1. Prüfen, ob ein Richter via QR-Code übergeben wurde
        url_judge_name = st.session_state.get("url_judge", "--")
        
        # 2. Alle Richter (aus allen Runden). Die Runde ergibt sich spaeter aus dem Rundenmanager.
        all_j = all_judges(df_full)
        
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
            # Runde dieses Richters (vom Rundenmanager gesetzt)
            runde = judge_round(store, mein_richter)
            tag = tag_of(runde)
            r_col = f"RICHTER {tag}"
            r_color, r_tint, r_text = round_color(runde), round_tint(runde), round_label(runde)
            st.sidebar.info(f"🎨 {mein_richter}: {r_text}")
            st.markdown(
                f"<div style='background:{r_tint}; border-left:12px solid {r_color}; padding:10px 16px; "
                f"border-radius:8px; font-size:22px; font-weight:bold;'>{r_text}</div>",
                unsafe_allow_html=True,
            )
            df_richter_alle = judge_cats(df_full, mein_richter, runde)
            verfuegbare_kategorien = sorted(list(set([str(cat).replace('.0', '') for cat in df_richter_alle['KATEGORIE'].unique() if pd.notna(cat)])))
            meine_kategorie = st.selectbox("Kategorie wählen:", verfuegbare_kategorien,
                                           format_func=lambda c: c if is_cat_open(store, runde, c) else f"🔒 {c} (nicht freigegeben)")
            
            df_j = df_richter_alle[df_richter_alle['KATEGORIE'].astype(str).str.replace('.0', '') == meine_kategorie].sort_values('KATALOG-NR')
            if not is_cat_open(store, runde, meine_kategorie):
                st.error(f"🔒 Kategorie {meine_kategorie} ist in dieser Runde ({r_text}, {get_show_day(store)}) nicht freigegeben.")
                df_j = df_j.iloc[0:0]
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
                belegt = busy_elsewhere(store, nr, mein_richter)
                ist_admin = st.session_state.get("user_role") == "Admin"
                abwesend = is_absent(store, nr, runde)
                gedimmt = bool(flags.get("Gerichtet")) or abwesend or bool(belegt)
                card_class = "steward-card-wrapper gerichtet" if gedimmt else "steward-card-wrapper"
                
                # START DES GRAUEN RECHTECKS
                st.markdown(f"""
                <div class="{card_class}" style="background-color:{r_tint} !important; border-left:12px solid {r_color} !important;">
                    <div class="card-header-row">
                        <span class="card-cat-number">Nr. {nr}</span>
                        <span class="card-meta-main">{get_full_label(row)}</span>
                        <span class="card-meta-sub" style="font-weight:bold; color:{r_color};">{r_text}</span>
                    </div>
                    <div class="grid-container">
                        <span class="card-meta-sub"><span class="meta-label">Klasse:</span> {klasse_anzeige}</span>
                        <span class="card-meta-sub"><span class="meta-label">Farbgruppe:</span> {farbgruppe}</span>
                        <span class="card-meta-sub"><span class="meta-label">Geschlecht:</span> {geschlecht_anzeige}</span>
                        <span class="card-meta-sub"><span class="meta-label">Geboren:</span> {geb_datum}</span>
                    </div>
                    <div style="border-top: 1px solid #e2e2e2; padding-top: 10px; margin-top: 12px; margin-bottom: 8px;"></div>
                """, unsafe_allow_html=True)
                
                # --- Sperre: Katze ist bei einem anderen Richter belegt ---
                gesperrt = (bool(belegt) and not ist_admin) or abwesend
                if abwesend:
                    st.error(f"🚫 Katze {nr} ist ABWESEND.")
                if belegt:
                    wo = ", ".join(f"{o} ({t})" for o, t in belegt)
                    st.error(f"🔒 Katze {nr} ist bei {wo} und kann nicht aufgerufen werden.")

                c1, c2, c3, c4, c5 = st.columns(5, vertical_alignment="center")
                
                # BUTTON 1: AUFRUFEN (Blau)
                is_rich = flags.get("Zum Richten")
                with c1:
                    if is_rich and not flags.get("Wird gerichtet"): st.markdown('<div class="st-blink-btn">', unsafe_allow_html=True)
                    if st.button("⚠️ [ AKTIV ] AUFGERUFEN ⚠️" if (is_rich and not flags.get("Wird gerichtet")) else "AUFRUFEN", key=f"btn_rich_{k}", disabled=gesperrt and not flags.get('Zum Richten')):
                        store.data[k]["flags"]["Zum Richten"] = not is_rich
                        if store.data[k]["flags"]["Zum Richten"]:
                            store.data[k]["flags"]["Gerichtet"] = False
                            store.data[k]["timestamp"] = time.time()
                            store.data[k]["called_at"] = time.time()
                        else:
                            store.data[k]["flags"]["Wird gerichtet"] = False
                            store.data[k].pop("called_at", None)
                        
                        store.save_backup()
                        st.rerun()
                    if is_rich and not flags.get("Wird gerichtet"): st.markdown('</div>', unsafe_allow_html=True)
                
                # BUTTON 2: WIRD GERICHTET (Orange)
                is_busy = flags.get("Wird gerichtet")
                with c2:
                    if is_busy: st.markdown('<div class="st-blink-btn">', unsafe_allow_html=True)
                    if st.button("⏳ TISCH / RICHTEN ⏳" if is_busy else "WIRD GERICHTET", key=f"btn_busy_{k}", disabled=gesperrt and not flags.get('Wird gerichtet')):
                        store.data[k]["flags"]["Wird gerichtet"] = not is_busy
                        if store.data[k]["flags"]["Wird gerichtet"]:
                            if not store.data[k]["flags"].get("Zum Richten") or not store.data[k].get("called_at"):
                                store.data[k]["called_at"] = time.time()
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
                    if st.button("⚠️ [ AKTIV ] BIV ⚠️" if is_biv else "BIV", key=f"btn_biv_{k}", disabled=gesperrt and not flags.get('BIV')):
                        store.data[k]["flags"]["BIV"] = not is_biv
                        store.data[k]["timestamp"] = time.time()
                        
                        store.save_backup()
                        st.rerun()
                    if is_biv: st.markdown('</div>', unsafe_allow_html=True)
                
                # BUTTON 4: NOMINIEREN (Gelb)
                is_nom = flags.get("NOM")
                with c4:
                    if is_nom: st.markdown('<div class="st-blink-btn">', unsafe_allow_html=True)
                    if st.button("⚠️ [ AKTIV ] NOM ⚠️" if is_nom else "NOM", key=f"btn_nom_{k}", disabled=gesperrt and not flags.get('NOM')):
                        store.data[k]["flags"]["NOM"] = not is_nom
                        if store.data[k]["flags"]["NOM"]:
                            store.data[k]["timestamp"] = time.time()
                        
                        store.save_backup()
                        st.rerun()
                    if is_nom: st.markdown('</div>', unsafe_allow_html=True)
                
                # BUTTON 5: GERICHTET (Grau)
                is_done = flags.get("Gerichtet")
                with c5:
                    if st.button("[ ERLEDIGT ] GERICHTET" if is_done else "GERICHTET", key=f"btn_done_{k}", disabled=abwesend):
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
