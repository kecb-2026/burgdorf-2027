# -*- coding: utf-8 -*-
"""Ansicht: BIS_Ablauf – Startzeit und Reihenfolge der Best-in-Show-Kategorien (eigene Ansicht, z. B. fuer Handy/Beamer)."""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from core.data import load_labels
from core.gate import get_bis_order, get_bis_start
from core.rounds import ROUNDS, round_color, round_label, round_on_color, round_tint, tag_of
from core.store import get_store
from core.config import NO_CLASS_CATEGORIES


def render():
    store = get_store()
    st_autorefresh(interval=30000, key="bis_ablauf_refresh")
    st.markdown("<style>.block-container{padding-top:1rem; max-width:640px;}</style>", unsafe_allow_html=True)
    df = load_labels()
    if df is None:
        st.error("Daten momentan nicht verfügbar.")
        return
    cats = [str(c).replace(".0", "") for c in sorted(df["KATEGORIE"].unique())]

    cur_tag = str(store.data.get("bis_public_tag") or tag_of(1))
    cur_cat = str(store.data.get("bis_public_cat") or "").replace(".0", "")
    tags = [tag_of(n) for n in sorted(ROUNDS)]
    idx = tags.index(cur_tag) if cur_tag in tags else 0
    tag = st.radio("Runde", tags, index=idx, horizontal=True, key="bis_ablauf_tag",
                   format_func=lambda t: round_label(int(t.split()[-1])))
    n = int(tag.split()[-1])
    start = get_bis_start(store, tag)
    order = get_bis_order(store, tag, cats)

    st.markdown(
        f"<div style='background:{round_color(n)}; color:{round_on_color(n)}; border-radius:14px; padding:14px; text-align:center;'>"
        f"<div style='font-size:20px; font-weight:700;'>Best in Show – {round_label(n)}</div>"
        f"<div style='font-size:44px; font-weight:900; line-height:1.1;'>{('startet um ' + start + ' Uhr') if start else 'Startzeit folgt'}</div></div>",
        unsafe_allow_html=True)
    st.markdown("<div style='font-size:20px; font-weight:800; margin:14px 0 6px 0;'>Reihenfolge der Kategorien</div>", unsafe_allow_html=True)
    for i, c in enumerate(order, 1):
        on = (c == cur_cat and tag == cur_tag)
        name = f"Kategorie {c}" + (" (Hauskatzen)" if c in NO_CLASS_CATEGORIES else "")
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:12px; padding:10px 14px; margin-bottom:6px; border-radius:10px; "
            f"border:2px solid {round_color(n) if on else '#d0d4da'}; background:{round_tint(n) if on else '#f6f7f9'};'>"
            f"<span style='font-size:26px; font-weight:900; color:#1a4a9e; min-width:34px;'>{i}.</span>"
            f"<span style='font-size:22px; font-weight:{'900' if on else '600'};'>{name}</span>"
            f"<span style='margin-left:auto; font-weight:800;'>{'▶ jetzt' if on else ''}</span></div>",
            unsafe_allow_html=True)
    st.caption("Die Anzeige aktualisiert sich automatisch.")
