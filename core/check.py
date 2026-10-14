# -*- coding: utf-8 -*-
"""Ansicht: Check – Technik und Ausstellung auf einen Blick (laeuft beim Oeffnen)."""
import streamlit as st

from core.store import get_store
from core.syscheck import technik, ausstellung
from core.ui import display_header_with_logo, set_view

_ICON = {"ok": "✅", "warn": "⚠️", "err": "❌", "info": "ℹ️"}
_PAGE = {"Alters_Check": "Alters-Check", "Nominated_Cats": "Nominierte Katzen", "Import_PDF": "PDF-Import",
         "Admin_Panel": "Admin-Konsole", "Excel_Upload": "Excel-Upload", "Live_Admin": "Live-Admin",
         "Rundenmanager": "Rundenmanager"}


def _zeilen(items, prefix):
    for i, (status, text, page) in enumerate(items):
        c1, c2 = st.columns([6, 1])
        c1.markdown(f"{_ICON[status]} {text}")
        if page and status in ("warn", "err"):
            if c2.button(f"→ {_PAGE.get(page, page)}", key=f"chk_{prefix}_{i}"):
                set_view(page)


def render():
    store = get_store()
    display_header_with_logo("🩺 Check")
    t, df = technik(store)
    a = ausstellung(store, df)
    allr = t + a
    errs = sum(1 for s, _, _ in allr if s == "err")
    warns = sum(1 for s, _, _ in allr if s == "warn")
    if errs:
        st.error(f"❌ {errs} Fehler und {warns} Warnung(en): bitte unten nachsehen.")
    elif warns:
        st.warning(f"⚠️ {warns} Punkt(e) prüfen.")
    else:
        st.success("✅ Alles in Ordnung.")

    st.subheader("Technik")
    _zeilen(t, "t")
    st.subheader("Ausstellung")
    _zeilen(a, "a")
    st.caption("Die Prüfung läuft bei jedem Öffnen der Seite neu. Alter wird an beiden Ausstellungstagen geprüft.")
    if st.button("🔄 Erneut prüfen", key="chk_again"):
        st.cache_data.clear()
        st.rerun()
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_check"):
        set_view("Home")
