# -*- coding: utf-8 -*-
"""Ansicht: BIS_Public"""
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import streamlit as st
import time
from core.data import get_full_label, load_labels, real_judges
from core.store import get_store
from core.config import NO_CLASS_CATEGORIES, NO_CLASS_LABEL
from core.data import class_mask
from core.gate import cat_key, get_bis_order
from core.ui import display_header_with_logo, render_overlay_html, judge_header_html, round_banner, order_strip


def render():
    store = get_store()
    # --- SCHALTWEICHE 1: OVERLAY AKTIVIERUNG PRÜFEN ---
    is_overlay_active = hasattr(store, 'active_overlay') and store.active_overlay is not None
    if is_overlay_active:
        elapsed = time.time() - store.overlay_start_time
        remaining = 20 - elapsed
        
        # Prüfen, ob die 20 Sekunden abgelaufen sind
        if remaining <= 0:
            store.active_overlay = None
            st.rerun()  
        else:
            # Overlay-HTML rendern (bleibt jetzt komplett stabil ohne Sekundentakt-Flackern)
            st.markdown(render_overlay_html(store.active_overlay), unsafe_allow_html=True)
            
            # Löst exakt nach der verbleibenden Restzeit (in Millisekunden) genau einmal aus
            remaining_ms = int(remaining * 1000)
            st_autorefresh(interval=max(500, remaining_ms), key="overlay_exact_timer")
            
            # Verhindert, dass der Rest der Seite unter dem Overlay gerendert wird!
            st.stop()

    def get_initials(name):
        parts = str(name).split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return str(name)[:2].upper()

    display_header_with_logo("🏆 Best in Show")
    df_full = load_labels()
    
    if df_full is not None:
        df_full = df_full.drop_duplicates() # Füge dies hinzu, um Geisterzeilen zu vermeiden
        # --- ANFANG DER ÄNDERUNG: AUTOMATISCHE TAGES-SYNCHRONISATION FÜR DAS PUBLIKUM ---
        # Zentral gesteuert (BIS Admin): Runde und Kategorie dieses Bildschirms
        global_admin_day = store.data.get("bis_public_tag") or store.data.get("test_live_tag") or store.data.get("admin_selected_day", "Tag 1")
        current_tag = global_admin_day.upper()
        
        st.session_state['bis_stable_tag'] = current_tag
        # --- ENDE DER ÄNDERUNG ---
        
        # --- STABILE WIDGET-INITIALISIERUNG ---
        available_cats = sorted(df_full['KATEGORIE'].unique())
        current_cat = st.session_state.get('bis_stable_cat', available_cats[0])

        tag_index = ["TAG 1", "TAG 2", "TAG 3"].index(current_tag) if current_tag in ["TAG 1", "TAG 2", "TAG 3"] else 0
        cat_index = available_cats.index(current_cat) if current_cat in available_cats else 0

        st.sidebar.info(f"📅 Aktiver Ausstellungstag: {current_tag}")
        tag = current_tag

        _forced = store.data.get("bis_public_cat")
        _match = [c for c in available_cats if _forced is not None and str(c).replace(".0", "") == str(_forced).replace(".0", "")]
        if _match:
            sel_cat = _match[0]
            st.markdown(f"<div style='font-size:15px; color:#555; margin-bottom:6px;'>Kategorie <b>{sel_cat}</b></div>", unsafe_allow_html=True)
        else:
            sel_cat = st.selectbox("Kategorie:", available_cats, index=cat_index)
        
        st.session_state['bis_stable_tag'] = tag
        st.session_state['bis_stable_cat'] = sel_cat
        round_banner(tag, big=True, cat=sel_cat)
        order_strip(get_bis_order(store, tag, available_cats), sel_cat)
        _noclass = cat_key(sel_cat) in NO_CLASS_CATEGORIES

        # --- DYNAMISCHE SPALTEN-WEICHE FÜR DIE 2 TAGE ---
        sel_col = f"SELECTION {tag.replace('TAG ', '')}"
        if sel_col in df_full.columns:
            df_full['SELECTION'] = df_full[sel_col]

        bis_defs = [
            ("Adult Male", [1,3,5,7,9], "M"), ("Adult Female", [1,3,5,7,9], "W"), 
            ("Neuter Male", [2,4,6,8,10], "M"), ("Neuter Female", [2,4,6,8,10], "W"), 
            ("Junior 8-12 Male", [11], "M"), ("Junior 8-12 Female", [11], "W"), 
            ("Kitten 4-8 Male", [12], "M"), ("Kitten 4-8 Female", [12], "W")
        ]
        
        r_col = f"RICHTER {tag}"
        judges = sorted(real_judges(df_full[df_full[tag].astype(str).str.strip().str.upper() == 'X'][r_col]))

        cats_in_this_cat = df_full[
            (df_full['SELECTION'].astype(str).str.strip().str.upper() == 'X') & 
            (df_full['KATEGORIE'] == sel_cat)
        ]

        if cats_in_this_cat.empty:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.info(f"ℹ️ In der Kategorie {sel_cat} sind für {tag} aktuell keine Katzen für die Best in Show nominiert.")
            st.markdown("<div style='min-height: 400px;'></div>", unsafe_allow_html=True)

        # --- CSS-LOGIK FÜR GRÜNE RICHTER IM HEADER & HELLROTE GEWINNER-KARTE ---
        style_rules = ""
        for label, klassen, geschl in bis_defs:
            if not store.data.get(f"winner_reveal_{tag}_{sel_cat}_{label}", False):
                prefix = f"v_{tag}_{sel_cat}_{label}_"
                abgestimmte = []
                for key, val in store.data.get("votes", {}).items():
                    if key.startswith(prefix) and val != "Keine Wahl" and val != "Keine Wahl/Not chosen yet":
                        if isinstance(val, dict):
                            if val.get("katze") not in ["Keine Wahl", "Keine Wahl/Not chosen yet"]:
                                abgestimmte.append(key.replace(prefix, ""))
                        elif str(val) not in ["Keine Wahl", "Keine Wahl/Not chosen yet"]:
                            abgestimmte.append(key.replace(prefix, ""))
                
                for j in abgestimmte:
                    style_rules += f".judge-{str(j).replace(' ', '_')} {{ background-color: #28a745 !important; }}"

        # --- HELLROTER RAHMEN FÜR DIE GEWINNERKATZE IN DEN RICHTER-SPALTEN ---
        style_rules += """
        div.winner-card {
            background-color: #ffcccc !important;  
            border: 2px solid #ff4d4d !important;  
            color: #b21f2d !important;             
        }
        div.winner-card div.cat-number {
            color: #b21f2d !important;             
            font-weight: bold !important;
        }
        div.winner-card div.cat-details {
            color: #333333 !important;
        }
        """

        st.markdown(f"<style>{style_rules}</style>", unsafe_allow_html=True)

        # --- STATISCHER HEADER (OHNE BIS-SPALTE) ---
        cols = st.columns([0.8] + [1.2]*len(judges))
        cols[0].empty()
        for i, j in enumerate(judges):
            clean_id = str(j).replace(" ", "_")
            cols[i+1].markdown(judge_header_html(j, judges, extra_class=f"judge-{clean_id}"), unsafe_allow_html=True)

        # --- KATZEN-ZEILEN (OHNE BIS-SPALTE) ---
        _rows_defs = [(NO_CLASS_LABEL, None, None)] if _noclass else bis_defs
        for label, klassen, geschl in _rows_defs:
            r_cols = st.columns([0.8] + [1.2]*len(judges))
            r_cols[0].markdown(f"<div class='class-label-box'>{label}</div>", unsafe_allow_html=True)
            
            show_noms = store.data.get(f"reveal_{tag}_{sel_cat}_{label}", False)
            winner_revealed = store.data.get(f"winner_reveal_{tag}_{sel_cat}_{label}", False)

            # --- GEWINNER-KATZENNUMMER VORAB ERMITTELN ---
            row_winner_nr = None
            if winner_revealed:
                prefix = f"v_{tag}_{sel_cat}_{label}_"
                row_winner_nr = store.data.get(f"override_{tag}_{sel_cat}_{label}", "Automatisch (Stimmen)")
                if row_winner_nr == "Automatisch (Stimmen)" and "votes" in store.data:
                    vts = []
                    for k, v in store.data["votes"].items():
                        if k.startswith(prefix) and v != "Keine Wahl" and v != "Keine Wahl/Not chosen yet":
                            if isinstance(v, dict):
                                if v.get("status") == "bestaerkt":
                                    vts.append(v.get("katze"))
                            else:
                                vts.append(v)
                    if vts:
                        row_winner_nr = str(pd.Series(vts).value_counts().index[0])
                else:
                    row_winner_nr = str(row_winner_nr)
            
            for i, j in enumerate(judges):
                with r_cols[i+1]:
                    if show_noms:
                        m = df_full[(df_full['SELECTION'].astype(str).str.upper() == 'X') & (df_full[r_col] == j) & (df_full['KATEGORIE'] == sel_cat) & class_mask(df_full, klassen, geschl)]
                        if not m.empty:
                            _cards = [m.iloc[0]] if klassen is not None else [r_ for _, r_ in m.iterrows()]   # ohne Klassen: alle Nominierten
                            for _card in _cards:
                                kat_nr = str(_card['KAT_STR'])
                                circles_html = ""
                                if winner_revealed:
                                    prefix = f"v_{tag}_{sel_cat}_{label}_"
                                    all_votes = store.data.get("votes", {})
                                    voters = []
                                    for v_key, v_val in all_votes.items():
                                        if v_key.startswith(prefix):
                                            voted_cat = v_val.get("katze") if isinstance(v_val, dict) else v_val
                                            if str(voted_cat) == str(kat_nr):
                                                voters.append(v_key.replace(prefix, ""))
                                    if voters:
                                        circles = "".join([f"<div class='judge-circle' title='{v}'>{get_initials(v)}</div>" for v in voters])
                                        circles_html = f"<div class='judge-initials-container'>{circles}</div>"

                                card_css_class = "cat-card winner-card" if (winner_revealed and row_winner_nr and kat_nr == row_winner_nr) else "cat-card"

                                st.markdown(f"<div class='{card_css_class} bis-card'><div class='bis-top'><div class='cat-number'>{kat_nr}</div><div class='cat-details'>{get_full_label(_card)}</div></div>{circles_html}</div>", unsafe_allow_html=True)
                        else: st.markdown("<div class='placeholder-box'>–</div>", unsafe_allow_html=True)
                    else: st.markdown("<div class='placeholder-box'>🔒</div>", unsafe_allow_html=True)

    # --- SCHALTWEICHE 2: REFRESH NUR LADEN, WENN KEIN OVERLAY AKTIV ---
    if not is_overlay_active:
        st_autorefresh(interval=3000, key="bis_refresh")


# LIVE DASHBOARD
