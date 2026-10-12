# -*- coding: utf-8 -*-
"""Ansicht: Live_Admin"""
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import streamlit as st
import time
from core.data import class_mask, load_labels
from core.rounds import active_rounds, default_round, round_label, tag_of
from core.bis import cat_status, set_manual_ready
from core.config import NO_CLASS_CATEGORIES, NO_CLASS_LABEL
from core.gate import cat_key, get_bis_order, get_bis_start, set_bis_start, get_show_day, is_open as is_cat_open, set_bis_order
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    # NEU: Diese Funktionen schreiben NUR, wenn jemand ein Feld wirklich angeklickt hat.
    # Eine zweite oder vergessene Admin-Seite kann dadurch nichts mehr zurücksetzen.
    def _store_set(store_key, widget_key):
        store.data[store_key] = st.session_state[widget_key]
        store.save_backup()

    def _live_vote_changed(widget_key, cat, label, tag):
        if st.session_state[widget_key]:
            store.data["test_live_cat"] = cat
            store.data["test_live_label"] = label
            store.data["test_live_tag"] = tag
        elif (store.data.get("test_live_cat") == cat
              and store.data.get("test_live_label") == label
              and store.data.get("test_live_tag") == tag):
            store.data["test_live_cat"] = None
            store.data["test_live_label"] = None
            store.data["test_live_tag"] = None
        store.save_backup()

    # --- AUTOMATISCHER REFRESH FÜR ECHTEZEIT-ANZEIGE ---
    # Aktualisiert das Admin-Panel alle 2000 Millisekunden (2 Sekunden) von selbst.
    # Da wir nur das RAM abfragen, ist das extrem performant und flackerfrei!
    st_autorefresh(interval=2000, key="live_admin_auto_refresh")

    display_header_with_logo("👑 BIS Admin Control")
    df_full = load_labels()
    
    if df_full is not None:
        # --- HIER DIE NEUE RADIO-BOX FÜR DIE TAGE EINFÜGEN ---
        _runden = active_rounds(store)
        _std = default_round(store)
        def _round_changed():
            # Rundenwechsel: BIS-Bildschirm mitnehmen, falls 'automatisch' eingeschaltet ist
            if store.data.get("bis_follow"):
                _t = tag_of(st.session_state["admin_round_selector"])
                _c = st.session_state.get(f"admin_sel_cat_{_t}")
                if _c is None:
                    _c = sorted(df_full['KATEGORIE'].unique())[0]
                store.data["bis_public_tag"] = _t
                store.data["bis_public_cat"] = _c.item() if hasattr(_c, "item") else _c
                store.save_backup()

        admin_round = st.radio("Runde verwalten:", _runden, index=_runden.index(_std) if _std in _runden else 0,
                               format_func=round_label, horizontal=True, key="admin_round_selector", on_change=_round_changed)
        admin_tag = tag_of(admin_round)
        
        # Spaltenname dynamisch bestimmen (SELECTION 1 oder SELECTION 2)
        sel_col = f"SELECTION {admin_tag.replace('TAG ', '')}"
        
        # Wir überschreiben temporär im geladenen Dataframe die 'SELECTION' Spalte,
        # damit alle nachfolgenden Filter im originalen Code (pool = df_full[df_full['SELECTION']...]) unverändert weiterlaufen!
        if sel_col in df_full.columns:
            df_full['SELECTION'] = df_full[sel_col]
        # -----------------------------------------------------

    if df_full is not None:
        # Auch die Kategorie-Auswahl braucht einen tagesabhängigen Key
        def _push_to_bis_screen(_tag=admin_tag):
            """Schreibt Runde + Kategorie auf den BIS-Bildschirm, aber nur wenn 'automatisch' eingeschaltet ist."""
            if store.data.get("bis_follow"):
                _c = st.session_state.get(f"admin_sel_cat_{_tag}")
                store.data["bis_public_tag"] = _tag
                store.data["bis_public_cat"] = None if _c is None else (_c.item() if hasattr(_c, "item") else _c)
                store.save_backup()

        def _follow_changed(_tag=admin_tag):
            if st.session_state["bis_follow_cb"]:
                store.data["bis_follow"] = True
                _push_to_bis_screen(_tag)
            else:
                store.data["bis_follow"] = False
                store.data["bis_public_tag"] = None
                store.data["bis_public_cat"] = None
                store.save_backup()
                
        sel_cat = st.selectbox("Kategorie verwalten:", sorted(df_full['KATEGORIE'].unique()), key=f"admin_sel_cat_{admin_tag}",
                               on_change=_push_to_bis_screen)
        st.session_state["bis_follow_cb"] = bool(store.data.get("bis_follow", False))
        st.checkbox("📺 BIS-Bildschirm folgt automatisch dieser Runde und Kategorie", key="bis_follow_cb", on_change=_follow_changed)
        if store.data.get("bis_follow"):
            st.caption(f"BIS-Bildschirm zeigt: {round_label(int(str(store.data.get('bis_public_tag') or admin_tag).split()[-1]))}, Kategorie {store.data.get('bis_public_cat')}. "
                       "Beim Wechseln der Kategorie oben schaltet er automatisch mit. Häkchen entfernen = Besucher wählen selbst.")
        # --- Reihenfolge der Kategorien beim BIS (wird vor der BIS durchgegeben) ---
        _all_cats = [str(c).replace(".0", "") for c in sorted(df_full['KATEGORIE'].unique())]
        _ord_key = f"bis_order_ms_{admin_tag}"
        def _order_changed(_tag=admin_tag, _k=_ord_key):
            set_bis_order(store, _tag, st.session_state[_k])
        def _next_cat(_tag=admin_tag):
            _order = get_bis_order(store, _tag, _all_cats)
            _cur = str(st.session_state.get(f"admin_sel_cat_{_tag}")).replace(".0", "")
            _nxt = _order[(_order.index(_cur) + 1) % len(_order)] if _cur in _order else _order[0]
            _opts = sorted(df_full['KATEGORIE'].unique())
            _val = [o for o in _opts if str(o).replace(".0", "") == _nxt][0]
            st.session_state[f"admin_sel_cat_{_tag}"] = _val
            _push_to_bis_screen(_tag)
        _raw = store.data.get("bis_order")
        _raw = _raw.get(admin_tag) if isinstance(_raw, dict) else None
        if _ord_key not in st.session_state:
            st.session_state[_ord_key] = [c for c in (_raw or _all_cats) if c in _all_cats]
        _st_key = f"bis_start_in_{admin_tag}"
        def _start_changed(_tag=admin_tag, _k=_st_key):
            set_bis_start(store, _tag, st.session_state[_k].strip())
        if _st_key not in st.session_state:
            st.session_state[_st_key] = get_bis_start(store, admin_tag)
        with st.expander("📋 Reihenfolge der Kategorien beim BIS (Ansicht «BIS_Ablauf»)", expanded=False):
            st.multiselect("Reihenfolge (Kategorien in der durchgegebenen Reihenfolge anklicken; weggelassene Kategorien werden übersprungen):",
                           _all_cats, key=_ord_key, on_change=_order_changed)
            st.text_input("Best in Show startet um (z. B. 15:30):", key=_st_key, on_change=_start_changed)
            _cur_order = get_bis_order(store, admin_tag, _all_cats)
            st.caption("Aktuell: " + " ➜ ".join(f"Kat {c}" for c in _cur_order))
        st.button("➡️ Nächste Kategorie (nach dieser Reihenfolge)", key=f"next_cat_{admin_tag}", on_click=_next_cat)

        if not is_cat_open(store, admin_round, sel_cat):
            st.error(f"🔒 Kategorie {sel_cat} ist in {round_label(admin_round)} ({get_show_day(store)}) nicht freigegeben. Freigabe im Rundenmanager (Kategorien-Freigabe).")
            st.stop()
        _st = cat_status(store, df_full, admin_round, sel_cat)
        _mk = f"bis_manual_{admin_tag}_{sel_cat}"
        def _cb_manual(_n=admin_round, _c=sel_cat, _k=_mk):
            set_manual_ready(store, _n, _c, st.session_state[_k])
        if _st["ready"]:
            st.success(f"✅ BIS bereit: Kategorie {sel_cat} in {round_label(admin_round)}" + (" (von Hand gesetzt)" if _st["manual"] else f" – alle {_st['total']} Katzen gerichtet"))
        else:
            _o = ", ".join(_st["open"][:12]) + (" …" if len(_st["open"]) > 12 else "")
            st.warning(f"⏳ Noch nicht bereit: {len(_st['open'])} von {_st['total']} Katzen offen ({_o})")
        st.session_state[_mk] = _st["manual"] or bool(store.data.get(f"bis_ready_{admin_tag}_{sel_cat}", False))
        st.checkbox("Von Hand als «BIS bereit» markieren", key=_mk, on_change=_cb_manual)
        bis_defs = [("Adult Male", [1,3,5,7,9], "M"), ("Adult Female", [1,3,5,7,9], "W"), ("Neuter Male", [2,4,6,8,10], "M"), ("Neuter Female", [2,4,6,8,10], "W"), ("Junior 8-12 Male", [11], "M"), ("Junior 8-12 Female", [11], "W"), ("Kitten 4-8 Male", [12], "M"), ("Kitten 4-8 Female", [12], "W")]
        
        if cat_key(sel_cat) in NO_CLASS_CATEGORIES:
            bis_defs = [(NO_CLASS_LABEL, None, None)]   # keine Klassen: eine Gruppe 'Nominierte Katzen' (mit Abstimmung)

        # --- Sammelknopf: Nominationen aller Klassen dieser Kategorie auf einmal anzeigen/ausblenden ---
        def _reveal_all(value, _tag=admin_tag, _cat=sel_cat, _labels=[d[0] for d in bis_defs]):
            for _l in _labels:
                store.data[f"reveal_{_tag}_{_cat}_{_l}"] = value
            store.save_backup()

        _labels_all = [d[0] for d in bis_defs]
        _n_on = sum(1 for _l in _labels_all if store.data.get(f"reveal_{admin_tag}_{sel_cat}_{_l}", False))
        st.markdown("<style>.alle-nom-btn div.stButton > button { height: 70px; font-size: 22px; font-weight: 900; }</style>", unsafe_allow_html=True)
        st.markdown("<div class='alle-nom-btn'>", unsafe_allow_html=True)
        _c1, _c2 = st.columns([2, 1])
        _c1.button(f"👁️ NOMINATIONEN ALLER KLASSEN ANZEIGEN (Kategorie {sel_cat})", key=f"reveal_all_on_{admin_tag}_{sel_cat}",
                   on_click=_reveal_all, args=(True,), disabled=(_n_on == len(_labels_all)))
        _c2.button("Alle ausblenden", key=f"reveal_all_off_{admin_tag}_{sel_cat}",
                   on_click=_reveal_all, args=(False,), disabled=(_n_on == 0))
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption(f"Zurzeit angezeigt: {_n_on} von {len(_labels_all)} Klassen. Einzelne Klassen kannst du unten weiterhin separat ein- und ausblenden.")

        for label, klassen, geschl in bis_defs:
            # Der Expander-Key wird tagesabhängig, damit der Auf-/Zuklapp-Status nicht vermischt wird
            with st.expander(f"KLASSE: {label} ({round_label(admin_round)})", expanded=True):
                c_ctrl, c_votes = st.columns([1, 1.2])
                
                # Der v_prefix enthält jetzt den Tag, damit die Stimmen von Tag 1 und Tag 2 getrennt gesucht werden
                v_prefix = f"v_{admin_tag}_{sel_cat}_{label}_"
                
                with c_ctrl:
                    st.markdown("**Steuerung**")
                    
                    # Die Datenschlüssel im store.data erhalten den Tag, damit Werte getrennt gespeichert werden
                    key_reveal = f"reveal_{admin_tag}_{sel_cat}_{label}"
                    key_winner_reveal = f"winner_reveal_{admin_tag}_{sel_cat}_{label}"
                    key_override = f"override_{admin_tag}_{sel_cat}_{label}"
                    
                    # Interaktionen abfangen und geänderte Zustände direkt persistieren (ohne Rerun-Konflikt)
                    # NEU: Anzeige immer aus dem Speicher, geschrieben wird nur bei echtem Klick
                    st.session_state[f"cb1_{key_reveal}"] = store.data.get(key_reveal, False)
                    st.checkbox("Nominationen anzeigen", key=f"cb1_{key_reveal}",
                                on_change=_store_set, args=(key_reveal, f"cb1_{key_reveal}"))
                    
                    # --- ANFANG DER NEUEN ZUSÄTZLICHEN CHECKBOX ---
                    # HIER PRÜFEN WIR, OB DIESE KLASSE GERADE ALS AKTIVE TEST-RUNDE GESPEICHERT IST
                    is_live_now = (store.data.get("test_live_cat") == sel_cat) and (store.data.get("test_live_label") == label) and (store.data.get("test_live_tag") == admin_tag)
                    
                    # NEU: Anzeige immer aus dem Speicher, geschrieben wird nur bei echtem Klick
                    _lv_key = f"live_vote_{admin_tag}_{sel_cat}_{label}"
                    st.session_state[_lv_key] = is_live_now
                    st.checkbox("🟢 Diese Klasse für Richter freischalten (Live-Voting)", key=_lv_key,
                                on_change=_live_vote_changed, args=(_lv_key, sel_cat, label, admin_tag))
                    # --- ENDE DER NEUEN ZUSÄTZLICHEN CHECKBOX ---


                    # --- NEU: COMPAKTE CHECKBOX STATT RADIO BOX ---
                    # KOMMENTAR: Wir erstellen den eindeutigen Schlüssel für den Speicher
                    key_voting_closed = f"voting_closed_{admin_tag}_{sel_cat}_{label}"
                    # NEU: Anzeige immer aus dem Speicher, geschrieben wird nur bei echtem Klick
                    _cl_key = f"cb_closed_{admin_tag}_{sel_cat}_{label}"
                    st.session_state[_cl_key] = store.data.get(key_voting_closed, False)
                    st.checkbox("🛑 Abstimmung beenden (Richter sperren) ", key=_cl_key,
                                on_change=_store_set, args=(key_voting_closed, _cl_key))
                    # --- ENDE NEU ---

                    # --- BIS GEWINNER ANZEIGEN (Ganz ans Ende verschoben) ---
                    # NEU: Anzeige immer aus dem Speicher, geschrieben wird nur bei echtem Klick
                    st.session_state[f"cb2_{key_winner_reveal}"] = store.data.get(key_winner_reveal, False)
                    st.checkbox("BIS Gewinner anzeigen", key=f"cb2_{key_winner_reveal}",
                                on_change=_store_set, args=(key_winner_reveal, f"cb2_{key_winner_reveal}"))
					
                    pool = df_full[(df_full['SELECTION'].astype(str).str.upper() == 'X') & (df_full['KATEGORIE'] == sel_cat) & class_mask(df_full, klassen, geschl)]
                    options = ["Automatisch (Stimmen)"] + sorted(pool['KAT_STR'].unique().tolist())
                    
                    # NEU: Anzeige immer aus dem Speicher, geschrieben wird nur bei echtem Klick
                    _ov = store.data.get(key_override, "Automatisch (Stimmen)")
                    st.session_state[f"sb_{key_override}"] = _ov if _ov in options else "Automatisch (Stimmen)"
                    st.selectbox("Gewinner festlegen:", options, key=f"sb_{key_override}",
                                 on_change=_store_set, args=(key_override, f"sb_{key_override}"))

                    final_nr = None
                    if store.data.get(key_override, "Automatisch (Stimmen)") != "Automatisch (Stimmen)": 
                        final_nr = store.data.get(key_override, "Automatisch (Stimmen)")
                    elif "votes" in store.data:
                        # Für die automatische Ermittlung des Gewinners zählen NUR "bestaerkt" (bestätigte) Stimmen!
                        vts = []
                        for k, v in store.data["votes"].items():
                            if k.startswith(v_prefix) and v != "Keine Wahl" and v != "Keine Wahl/Not chosen yet":
                                if isinstance(v, dict) and v.get("status") == "bestaerkt":
                                    vts.append(v.get("katze"))
                                elif isinstance(v, str): # Kompatibilität für alte Plain-Strings
                                    vts.append(v)
                        if vts: 
                            final_nr = pd.Series(vts).value_counts().index[0]

                    if final_nr and st.button(f"🏆 OVERLAY ZEIGEN (#{final_nr})", key=f"btn_ov_{admin_tag}_{sel_cat}_{label}"):
                        w_match = df_full[df_full['KAT_STR'] == str(final_nr)]
                        if not w_match.empty:
                            store.active_overlay = w_match.iloc[0].to_dict()
                            store.overlay_start_time = time.time()
                            if "local_overlay_end" in st.session_state:
                                st.session_state.local_overlay_end = 0
                        st.success(f"Overlay für #{final_nr} wurde gestartet!")
        
                with c_votes:
                    st.markdown("**Stimmen-Details**")
                    
                    if "votes" in store.data:
                        rows = []
                        confirmed_votes_for_summary = []
                        _tbd = store.data.get(f"tiebreak_{admin_tag}_{sel_cat}_{label}")
                        _tbd = _tbd if isinstance(_tbd, dict) else {}
                        _tbj = set(_tbd.get("judges", []))
                        
                        for k, v in store.data["votes"].items():
                            if k.startswith(v_prefix) and v != "Keine Wahl" and v != "Keine Wahl/Not chosen yet":
                                r_name = k.replace(v_prefix, "")
                                
                                # Struktur aufdröseln (Dict vs. Alt-String)
                                if isinstance(v, dict):
                                    kat_nr = v.get("katze", "N/A")
                                    status = v.get("status", "wählt")
                                
                                # Status-Emoji bestimmen
                                status_emoji = "✅ Bestätigt" if status == "bestaerkt" else "⏳ Wählt..."
                                
                                if r_name in _tbj:
                                    _ov0 = (_tbd.get("old") or {}).get(r_name)
                                    if _ov0 is not None:
                                        # Ursprüngliche Stimme bleibt als normale Zeile stehen (zählt nicht mehr)
                                        _oc0 = _ov0.get("katze", "N/A") if isinstance(_ov0, dict) else _ov0
                                        rows.append({"Richter": r_name, "Wahl (Kat Nr.)": f"#{_oc0}", "Status": "✅ Bestätigt"})
                                    rows.append({
                                        "Richter": f"{r_name} (Stichentscheid)",
                                        "Wahl (Kat Nr.)": f"#{kat_nr}",
                                        "Status": status_emoji
                                    })
                                else:
                                    rows.append({
                                        "Richter": r_name, 
                                        "Wahl (Kat Nr.)": f"#{kat_nr}",
                                        "Status": status_emoji
                                    })
                                
                                # Für die mathematische Zusammenfassung zählen nur bestätigte Stimmen
                                if status == "bestaerkt":
                                    confirmed_votes_for_summary.append(kat_nr)
                        
                        if rows:
                            vote_df = pd.DataFrame(rows)
                            
                            # Schickes farbliches Highlight-Styling für die Tabelle (Grün für Bestätigt, Gelb für Entwurf)
                            def highlight_status(row):
                                if "(Stichentscheid)" in str(row["Richter"]) and "✅" in str(row["Status"]):
                                    return ['background-color: #f5b301; color: #1a1a1a; font-weight: bold'] * len(row)
                                if "✅" in str(row["Status"]):
                                    return ['background-color: #d4edda; color: #155724'] * len(row)
                                return ['background-color: #fff3cd; color: #856404'] * len(row)
                            
                            styled_df = vote_df.style.apply(highlight_status, axis=1)
                            st.dataframe(styled_df, use_container_width=True, hide_index=True)
                            
                            st.write("**Gezählte Zwischenstände (Nur bestätigte Stimmen):**")
                            if confirmed_votes_for_summary:
                                summary = pd.Series(confirmed_votes_for_summary).value_counts()
                                for nr, count in summary.items(): 
                                    # Name der Katze aus der geladenen Excel-Tabelle auslesen
                                    cat_name = "Unbekannt"
                                    match = df_full[df_full['KAT_STR'] == str(nr)]
                                    if not match.empty:
                                        cat_name = str(match.iloc[0].get('NAME', 'Unbekannt'))
                                        
                                    st.write(f"Katze #{nr} ({cat_name}): **{count} Stimme(n)**")

                            else:
                                st.info("Es wurden noch keine Stimmen final bestätigt.")



                    # --- RESET-BUTTON: WEISSER HINTERGRUND, NUR TEXT & ICON ---
                    st.markdown("---")
                    
                    # CSS-Anpassung, damit dieser spezielle Button einen weißen Hintergrund und dunklen Text bekommt
                    st.markdown("""
                        <style>
                        div.stButton > button[kind="secondary"] {
                            background-color: white !important;
                            color: #31333F !important;
                            border: 1px solid #cccccc !important;
                        }
                        div.stButton > button[kind="secondary"]:hover {
                            background-color: #f0f2f6 !important;
                            color: #31333F !important;
                            border: 1px solid #b5b5b5 !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)

                    confirm_key = f"confirm_reset_{admin_tag}_{sel_cat}_{label}"
                    
                    if not st.session_state.get(confirm_key, False):
                        if st.button("🔄 Stimmen zurücksetzen", key=f"btn_init_reset_{admin_tag}_{sel_cat}_{label}",type="secondary"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("⚠️ Wirklich löschen?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("Ja", key=f"btn_confirm_yes_{admin_tag}_{sel_cat}_{label}", type="primary"):
                                if "votes" in store.data:
                                    keys_to_delete = [k for k in store.data["votes"].keys() if k.startswith(v_prefix)]
                                    for k in keys_to_delete:
                                        del store.data["votes"][k]
                                    store.save_backup()
                                st.session_state[confirm_key] = False
                                st.success("Zurückgesetzt!")
                                st.rerun()
                        with col_no:
                            if st.button("Nein", key=f"btn_confirm_no_{admin_tag}_{sel_cat}_{label}"):
                                st.session_state[confirm_key] = False
                                st.rerun()
                    # -------------------------------------------------------------
                                
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_bisadmin"):
        set_view("Home")


# ==============================================================================
# NEU: MODERATOR-ANSICHT (nur Anzeige + ein Knopf "Gewinner zeigen")
# ==============================================================================
