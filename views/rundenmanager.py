# -*- coding: utf-8 -*-
"""Ansicht: Rundenmanager (Ausstellungsleitung): pro Richter die aktuelle Runde Gelb/Grün/Rot festlegen."""
from streamlit_autorefresh import st_autorefresh
import streamlit as st
from core.config import DEFAULT_SHOWTYPE, SHOWTYPES
from core.data import load_labels
from core.rounds import active_rounds, all_judges, default_round, judge_cats, judge_round, round_color, round_label, round_tint, set_default_round, set_judge_round
from core.bis import cat_status
from core.gate import DAYS, blocked_cats, categories, get_show_day, set_open, set_row, set_show_day
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    st_autorefresh(interval=5000, key="rundenmanager_refresh")
    display_header_with_logo("🎛️ Rundenmanager")

    df_full = load_labels()
    if df_full is None:
        st.error("Die Excel-Daten konnten nicht geladen werden.")
        st.stop()

    rounds = active_rounds(store)

    # ---- Callbacks: schreiben NUR bei einem echten Klick ----
    def _cb_showtype():
        store.data["showtype"] = st.session_state["rm_showtype"]
        store.save_backup()

    def _cb_default():
        set_default_round(store, st.session_state["rm_default"])

    def _cb_judge(j):
        set_judge_round(store, j, st.session_state[f"rm_judge_{j}"])

    def _cb_all(n):
        set_default_round(store, n, reset_judges=True)

    def _fmt(n):
        return round_label(n)

    # ---- 1. Showtyp ----
    st.subheader("1. Showtyp")
    names = list(SHOWTYPES.keys())
    cur = store.data.get("showtype", DEFAULT_SHOWTYPE)
    st.session_state["rm_showtype"] = cur if cur in names else DEFAULT_SHOWTYPE
    st.selectbox("Welche Runden gibt es in dieser Ausstellung?", names, key="rm_showtype", on_change=_cb_showtype)
    st.caption("Aktive Runden: " + ", ".join(round_label(n) for n in rounds))

    # ---- 2. Standard-Runde ----
    st.subheader("2. Standard-Runde")
    dflt = default_round(store)
    st.session_state["rm_default"] = dflt if dflt in rounds else rounds[0]
    st.radio("Diese Runde gilt für alle Richter ohne eigene Einstellung (und für den BIS-Bildschirm):",
             rounds, format_func=_fmt, horizontal=True, key="rm_default", on_change=_cb_default)
    cols = st.columns(len(rounds))
    for col, n in zip(cols, rounds):
        with col:
            st.button(f"Alle Richter auf {round_label(n)} setzen", key=f"rm_all_{n}", on_click=_cb_all, args=(n,))

    # ---- 3. Richter ----
    st.subheader("3. Richter")
    judges = all_judges(df_full)
    if not judges:
        st.info("Keine Richter im Excel gefunden.")
    for j in judges:
        n = judge_round(store, j)
        n_show = n if n in rounds else rounds[0]
        c_name, c_sel, c_info = st.columns([1.2, 2.2, 1.6], vertical_alignment="center")
        with c_name:
            st.markdown(
                f"<div style='border-left:10px solid {round_color(n_show)}; background:{round_tint(n_show)};"
                f"padding:8px 12px; border-radius:8px; font-weight:bold; font-size:18px;'>{j}</div>",
                unsafe_allow_html=True,
            )
        with c_sel:
            st.session_state[f"rm_judge_{j}"] = n_show
            st.radio(f"Runde für {j}", rounds, format_func=_fmt, horizontal=True,
                     key=f"rm_judge_{j}", label_visibility="collapsed",
                     on_change=_cb_judge, args=(j,))
        with c_info:
            cats = judge_cats(df_full, j, n_show)
            st.caption(f"{len(cats)} Katzen in dieser Runde")

    # ---- 4. Kategorien-Freigabe ----
    st.subheader("4. Kategorien-Freigabe (Sperre)")
    st.caption("Häkchen = Kategorie wird in dieser Runde gerichtet. Ohne Häkchen ist sie für alle Richter gesperrt. Jeder Tag hat seine eigene Tabelle; es gilt der aktive Tag.")
    cats = categories(df_full)

    def _cb_day():
        set_show_day(store, st.session_state["rm_showday"])

    def _cb_gate(day, n, c):
        set_open(store, day, n, c, st.session_state[f"gate_{day}_{n}_{c}"])

    def _cb_row(day, n, open_cats):
        set_row(store, day, n, cats, open_cats)

    st.session_state["rm_showday"] = get_show_day(store)
    st.radio("Aktiver Tag (gilt jetzt):", DAYS, horizontal=True, key="rm_showday", on_change=_cb_day)
    tabs = st.tabs([f"{d}" + (" (aktiv)" if d == get_show_day(store) else "") for d in DAYS])
    for day, tab in zip(DAYS, tabs):
        with tab:
            hdr = st.columns([1.6] + [1] * len(cats) + [3])
            hdr[0].markdown("**Runde**")
            for i, c in enumerate(cats):
                hdr[i + 1].markdown(f"**Kat {c}**")
            for n in rounds:
                row = st.columns([1.6] + [1] * len(cats) + [3], vertical_alignment="center")
                row[0].markdown(
                    f"<div style='border-left:8px solid {round_color(n)}; background:{round_tint(n)}; padding:6px 10px; "
                    f"border-radius:6px; font-weight:bold;'>{round_label(n)}</div>", unsafe_allow_html=True)
                bl = blocked_cats(store, n, day)
                for i, c in enumerate(cats):
                    k = f"gate_{day}_{n}_{c}"
                    st.session_state[k] = c not in bl
                    row[i + 1].checkbox(f"Kat {c}", key=k, label_visibility="collapsed", on_change=_cb_gate, args=(day, n, c))
                with row[-1]:
                    b = st.columns(3)
                    b[0].button("Alle", key=f"gate_all_{day}_{n}", on_click=_cb_row, args=(day, n, cats))
                    odd = [c for c in cats if c.isdigit() and int(c) % 2 == 1]
                    even = [c for c in cats if c.isdigit() and int(c) % 2 == 0]
                    b[1].button("Nur 1+3", key=f"gate_odd_{day}_{n}", on_click=_cb_row, args=(day, n, odd))
                    b[2].button("Nur 2+4", key=f"gate_even_{day}_{n}", on_click=_cb_row, args=(day, n, even))

    # ---- 5. BIS-Status ----
    st.subheader("5. BIS-Status (aktiver Tag)")
    st.caption("✅ bereit = alle Katzen gerichtet · ⏳ n offen · 🔒 Kategorie gesperrt · – keine Katzen")
    _rows = []
    for n in rounds:
        r = {"Runde": round_label(n)}
        for c in cats:
            if c in blocked_cats(store, n):
                r[f"Kat {c}"] = "🔒"
                continue
            stt = cat_status(store, df_full, n, c)
            r[f"Kat {c}"] = "–" if stt["total"] == 0 and not stt["ready"] else ("✅" if stt["ready"] else f"⏳ {len(stt['open'])} offen")
        _rows.append(r)
    st.dataframe(_rows, hide_index=True, use_container_width=True)

    # ---- 6. Belegte Katzen ----
    st.subheader("6. Gerade belegte Katzen")
    st.caption("Katzen, die bei einem Richter aufgerufen sind, gerichtet werden, BIV oder Nomination haben.")
    rows = []
    for key, val in list(store.data.items()):
        if not (isinstance(key, str) and "|" in key and isinstance(val, dict)):
            continue
        nr, judge = key.split("|", 1)
        flags = val.get("flags", {})
        if not isinstance(flags, dict) or flags.get("Gerichtet"):
            continue
        active = [t for t in ("Wird gerichtet", "Zum Richten", "BIV", "NOM") if flags.get(t)]
        if active:
            rows.append({"Katze": nr, "Richter": judge, "Status": ", ".join(active)})
    if rows:
        rows.sort(key=lambda r: (r["Richter"], r["Katze"]))
        st.dataframe(rows, hide_index=True, use_container_width=True)
    else:
        st.success("Keine Katze ist gerade belegt.")

    st.divider()
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_rundenmanager"):
        set_view("Home")
