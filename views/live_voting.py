# -*- coding: utf-8 -*-
"""Ansicht: Live_Voting"""
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import streamlit as st
from core.data import get_full_label, load_labels, real_judges
from core.store import get_store
from core.ui import display_header_with_logo


def render():
    store = get_store()
    st_autorefresh(interval=4000, key="test_live_voting_refresh")
    display_header_with_logo("🗳️  Judge Live Voting")
   
    df_full = load_labels()
    if df_full is not None:
        # AUTOMATISCHE TAGES-SYNCHRONISATION
        global_admin_day = store.data.get("admin_selected_day", "Tag 1")
        st.session_state["judge_day_selector"] = global_admin_day
        st.sidebar.info(f"📅 Aktiver Ausstellungstag: {global_admin_day}")
        tag = global_admin_day.upper()
        
        r_col = f"RICHTER {tag}"
        all_judges = sorted(real_judges(df_full[r_col]))
        
        # 1. LIVE-WERTE AUS DEM TEST-ADMIN AUSLESEN
        active_cat = store.data.get("test_live_cat")
        active_label = store.data.get("test_live_label")
        active_tag = store.data.get("test_live_tag")
        
        # 2. DER PRÜFMECHANISMUS: RUNDEN-WECHSEL IM HINTERGRUND ERKENNEN
        current_round_identifier = f"{active_tag}_{active_cat}_{active_label}"
        if "last_seen_round" not in st.session_state:
            st.session_state.last_seen_round = current_round_identifier
            
        # Wenn der Admin im Hintergrund eine andere Runde freigibt, wird automatisch aktualisiert
        if st.session_state.last_seen_round != current_round_identifier:
            st.session_state.last_seen_round = current_round_identifier
            st.rerun()


        # 2. WENN NOCH KEIN HÄKCHEN IM TEST-ADMIN GESETZT WURDE -> WARTE-BILDSCHIRM
        if not active_cat or not active_label:
            st.info("⏳ **Bitte warten...** Die Ausstellungsleitung hat für den Test aktuell noch keine Abstimmungsrunde freigeschaltet. Please wait, the Admin will release the voting shortly.")
            st.stop()
            
        # 3. GELBER LIVE-BANNER FÜR DEN RICHTER
        st.markdown(
            f"<div style='background-color:#fff3cd; padding:15px; border-radius:8px; border-left:5px solid #ffc107; margin-bottom:20px;'>"
            f"📢 <b>AKTIVE RUNDE - ACTIVE ROUND:</b><br>"
            f"<span style='font-size:20px; color:#856404;'><b>Kategorie - Category {active_cat} — {active_label}</b></span>"
            f"</div>", 
            unsafe_allow_html=True
        )

        # PRÜFEN OB DIE ABSTIMMUNG FÜR DIESE KLASSE BEENDET IST
        key_voting_closed = f"voting_closed_{tag}_{active_cat}_{active_label}"
        is_voting_closed = store.data.get(key_voting_closed, False)

        if is_voting_closed:
            st.error("🛑 **Abstimmung beendet!** / **Voting closed!**")
            st.stop()

        # --- NEU: PRÜFEN OB DER BIS-GEWINNER VOM ADMIN AUFGEDECKT WURDE ---
        key_winner_reveal = f"winner_reveal_{tag}_{active_cat}_{active_label}"
        is_winner_revealed = store.data.get(key_winner_reveal, False)

        if is_winner_revealed:
            # Ermitteln, welcher Gewinner feststeht (entweder manueller Override oder die stimmenstärkste Katze)
            key_override = f"override_{tag}_{active_cat}_{active_label}"
            winning_nr = store.data.get(key_override, "Automatisch (Stimmen)")
            
            v_prefix = f"v_{tag}_{active_cat}_{active_label}_"
            if winning_nr == "Automatisch (Stimmen)" and "votes" in store.data:
                vts = []
                for k, v in store.data["votes"].items():
                    if k.startswith(v_prefix) and v != "Keine Wahl" and v != "Keine Wahl/Not chosen yet":
                        if isinstance(v, dict) and v.get("status") == "bestaerkt":
                            vts.append(v.get("katze"))
                        elif isinstance(v, str):
                            vts.append(v)
                if vts:
                    winning_nr = pd.Series(vts).value_counts().index[0]
            
            # Gewinner-Details aus der Excel-Tabelle auslesen
            winner_details_text = ""
            winner_owner_text = ""
            if winning_nr and winning_nr != "Automatisch (Stimmen)":
                w_match = df_full[df_full['KAT_STR'] == str(winning_nr)]
                if not w_match.empty:
                    w_row = w_match.iloc[0]
                    winner_details_text = get_full_label(w_row)
                    winner_owner_text = f"{w_row.get('BESITZER VORNAME', '')} {w_row.get('BESITZER NACHNAME', '')}"
            
            # Schicke Goldene Gewinner-Ansicht für die Richter
            st.markdown(
                f"<div style='background-color:#fff3cd; padding:30px; border-radius:15px; border:4px solid #d4af37; text-align:center; margin-top:20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>"
                f"<div style='font-size:16px; font-weight:bold; color:#856404; text-transform:uppercase; letter-spacing:2px;'>🏆 Best in Show Winner 🏆</div>"
                f"<div style='font-size:65px; font-weight:900; color:#b21f2d; margin:10px 0;'>#{winning_nr}</div>"
                f"<div style='font-size:22px; font-weight:bold; color:#333; margin-bottom:5px;'>{winner_details_text}</div>"
                f"<div style='font-size:18px; font-style:italic; color:#555;'>{winner_owner_text}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.stop() # Hält den restlichen Stimmzettel für den Richter an, da das Ergebnis da ist



        
        # Richter-Identität ermitteln (entweder via URL oder Box)
        c1, _ = st.columns([2, 2])
        url_judge_name = st.session_state.get("url_judge", "--")
        
        if url_judge_name in all_judges and st.session_state.user_role != "Admin":
            active_j = url_judge_name
            c1.markdown(f"<div><b>Eingeloggt als Richter - Logged in as:</b> <span style='color:#1a4a9e; font-size:18px;'>{active_j}</span></div>", unsafe_allow_html=True)
        else:
            active_j = c1.selectbox("Identität/Identity wählen:", ["--"] + all_judges, key="test_live_vote_j_box")

        # Wenn ein Richter gewählt/eingeloggt ist, zeigen wir EXKLUSIV die eine aktive Klasse
        if active_j != "--":
            # ÄNDERUNG: SICHERSTELLEN, DASS DER VOTES-KEY IM SPEICHER EXISTIERT
            if "votes" not in store.data or not isinstance(store.data["votes"], dict): 
                store.data["votes"] = {}
                store.save_backup() # Änderung sofort in DB sichern
                
            bis_defs = [
                ("Adult Male", [1,3,5,7,9], "M"), ("Adult Female", [1,3,5,7,9], "W"), 
                ("Neuter Male", [2,4,6,8,10], "M"), ("Neuter Female", [2,4,6,8,10], "W"), 
                ("Junior 8-12 Male", [11], "M"), ("Junior 8-12 Female", [11], "W"), 
                ("Kitten 4-8 Male", [12], "M"), ("Kitten 4-8 Female", [12], "W")
            ]
            
            for label, klassen, geschl in bis_defs:
                # DIE MAGISCHE WEICHE: NUR WENN ES DIE VOM TEST-ADMIN FREIGEGEBENE KLASSE IST!
                if label == active_label:
                    with st.expander(f"Wahl für/Choice for {label}", expanded=True):
                        pool = df_full[(df_full['SELECTION'].astype(str).str.strip().str.upper() == 'X') & (df_full['KATEGORIE'] == active_cat) & (df_full['KLASSE_INTERNAL'].isin(klassen)) & (df_full['GESCHLECHT'].astype(str).str.upper() == geschl)]
                        
                        if not pool.empty:
                            # --------------------------------------------------
                            # 1. DETAIL-ERMITTLUNG (SCHLEIFE FÜR DATUM & GESCHLECHT)
                            # --------------------------------------------------
                            opts = {}
                            # Den passenden Richter-Spaltennamen für den aktuellen Tag ermitteln (z.B. "RICHTER TAG 1")
                            r_col_name = f"RICHTER {tag}"
                            
                            for _, r in pool.iterrows():
                                # Geburtsdatum-Spalte flexibel ermitteln
                                geb_cols = [c for c in r.index if "GEB" in str(c) or "GEBURT" in str(c)]
                                geb_datum = r[geb_cols[0]] if geb_cols else r.get('GEB_DATUM', 'N/A')
                                
                                # Datum formatieren, falls es ein Timestamp ist
                                if isinstance(geb_datum, pd.Timestamp):
                                    geb_datum = geb_datum.strftime('%d.%m.%Y')
                                elif pd.isna(geb_datum) or str(geb_datum).strip().lower() == "nan":
                                    geb_datum = "N/A"
                                
                                geschlecht_val = r.get('GESCHLECHT', 'N/A')
                                rasse_gruppe = get_full_label(r)
                                
                                # --- NEU: RICHTERNAMEN AUSLESEN ---
                                nom_richter = r.get(r_col_name, '-')
                                if pd.isna(nom_richter) or str(nom_richter).strip().lower() == "nan" or str(nom_richter).strip() == "":
                                    nom_richter = "-"
                                
                                # Label für den Radio-Button mit "Nominated by" erweitern
                                full_option_text = f"#{r['KAT_STR']} - {rasse_gruppe} [{geschlecht_val}, *{geb_datum}] (Nominated by {nom_richter})"
                                
                                # Strukturiert speichern für die spätere Anzeige in der Box (inklusive Richter für das große Banner)
                                opts[full_option_text] = {
                                    "kat_nr": r['KAT_STR'],
                                    "details": f"{rasse_gruppe} [{geschlecht_val}, *{geb_datum}] — <i>Nominated by {nom_richter}</i>"
                                }

                            
                            v_key = f"v_{tag}_{active_cat}_{label}_{active_j}"
                            curr_raw = store.data["votes"].get(v_key, "Keine Wahl")
                            
                            # Extrahiere die reine Kat-Nummer, egal ob Dict oder String geliefert wird
                            if isinstance(curr_raw, dict):
                                curr = curr_raw.get("katze", "Keine Wahl")
                            else:
                                curr = curr_raw
                            
                            # --------------------------------------------------
                            # 2. DEINE ABSTURZ-SICHERUNG
                            # --------------------------------------------------
                            default_index = 0
                            current_option_text = "Keine Wahl/Not chosen yet"
                            
                            try:
                                # Reine Katalognummern für die Index-Suche extrahieren
                                pure_numbers = [info["kat_nr"] for info in opts.values()]
                                if curr in pure_numbers:
                                    default_index = pure_numbers.index(curr) + 1
                                    current_option_text = list(opts.keys())[default_index - 1]
                            except (ValueError, IndexError):
                                default_index = 0
                                current_option_text = "Keine Wahl/Not chosen yet"

                            # --------------------------------------------------
                            # 4. RADIO-BUTTON & SPEICHER-LOGIK
                            # --------------------------------------------------
                            # Hilfsfunktion: Feuert live bei Klick und setzt den Status zurück!
                            def on_radio_change(v_key=v_key, opts=opts):
                                _wk = f"r_test_{v_key}"
                                if _wk not in st.session_state:
                                    return
                                current_radio_val = st.session_state[_wk]
                                if current_radio_val != "Keine Wahl/Not chosen yet":
                                    if current_radio_val not in opts:
                                        return
                                    kat_nummer = opts[current_radio_val]["kat_nr"]
                                    # Bei jeder Änderung überschreiben wir die Bestätigung und setzen zurück auf "wählt"
                                    store.data["votes"][v_key] = {
                                        "katze": kat_nummer,
                                        "status": "wählt"
                                    }

                                else:
                                    store.data["votes"][v_key] = "Keine Wahl/Not chosen yet"
                                store.save_backup()
                                # ÄNDERUNG: Sofortiger Rerun, damit Admin und Banner die Änderung live registrieren!
                                #st.rerun()

                            # Radio-Button steuert den Live-Zustand an
                            sel = st.radio(
                                "Favorit wählen / Choose favorite:", 
                                ["Keine Wahl/Not chosen yet"] + list(opts.keys()), 
                                index=default_index, 
                                key=f"r_test_{v_key}",
                                on_change=on_radio_change
                            )

                            # --------------------------------------------------
                            # 3. GEWÄHLTE KATZE GROSS ANZEIGEN (REAKTIV)
                            # --------------------------------------------------
                            if sel != "Keine Wahl/Not chosen yet" and sel in opts:
                                selected_data = opts[sel]
                                
                                # Status ermitteln
                                current_status = "wählt"
                                if isinstance(store.data["votes"].get(v_key), dict):
                                    current_status = store.data["votes"][v_key].get("status", "wählt")
                                
                                if current_status == "bestaerkt":
                                    banner_title = "✅ BESTÄTIGTE STIMME / CONFIRMED VOTE:"
                                    bg_color = "#d4edda" # Grün
                                    border_color = "#28a745"
                                    text_color = "#155724"
                                else:
                                    banner_title = "⏳ AUSGEWÄHLT (NOCH NICHT BESTÄTIGT) / SELECTED (NOT CONFIRMED YET):"
                                    bg_color = "#fff3cd" # Gelb/Orange
                                    border_color = "#ffc107"
                                    text_color = "#856404"

                                st.markdown(
                                    f"<div style='background-color:{bg_color}; padding:15px; border-radius:8px; border-left:5px solid {border_color}; margin-bottom:20px; text-align:center; color:{text_color};'>"
                                    f"<div style='font-size:14px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;'>{banner_title}</div>"
                                    f"<div style='font-size:54px; font-weight:900; line-height:1; margin:10px 0;'>#{selected_data['kat_nr']}</div>"
                                    f"<div style='font-size:16px; font-weight:500;'>{selected_data['details']}</div>"
                                    f"</div>", 
                                    unsafe_allow_html=True
                                )
                            else:
                                # Neutrale Graubox, wenn noch nichts gewählt wurde
                                st.markdown(
                                    f"<div style='background-color:#e2e3e5; padding:12px; border-radius:8px; border-left:5px solid #6c757d; margin-bottom:20px; text-align:center; color:#383d41; font-style:italic;'>"
                                    f"Noch keine Stimme abgegeben / No vote cast yet."
                                    f"</div>", 
                                    unsafe_allow_html=True
                                )
                            
                            # Bestätigungs-Button wird nur eingeblendet, wenn eine Katze gewählt ist
                            if sel != "Keine Wahl/Not chosen yet":
                                st.write("") 
                                if st.button("🚀 Stimme offiziell bestätigen / Confirm Vote", key=f"btn_confirm_{v_key}", use_container_width=True):
                                    finale_katze = opts[sel]["kat_nr"]
                                    
                                    store.data["votes"][v_key] = {
                                        "katze": finale_katze,
                                        "status": "bestaerkt"
                                    }
                                    store.save_backup()
                                    st.success(f"Katze #{finale_katze} erfolgreich bestätigt!")
                                    st.rerun()
                        else:
                            st.info("ℹ️ Keine nominierten Katzen in dieser Klasse vorhanden.")



# ==============================================================================
# NEUER SEPARATER MENÜPUNKT: 🎛️ [Test] Live-Admin
# (FIX: Checkboxen schreiben nur noch bei echtem Klick, siehe Kommentare "# NEU")
# ==============================================================================
