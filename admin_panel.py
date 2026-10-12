# -*- coding: utf-8 -*-
"""Ansicht: Admin_Panel"""
import streamlit as st
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    display_header_with_logo("⚙️ Admin-Konsole")
    
    _reset_ok = st.checkbox("Ja, wirklich ALLE Stimmen und Status löschen", key="confirm_reset_all")
    if st.button("ALLE DATEN ZURÜCKSETZEN", disabled=not _reset_ok):
        store.data = {}
        store.active_overlay = None
        store.save_backup()
        st.success("Speicher geleert!")

    # --- HIER IST DER NEUE BUTTON SAUBER EINIGERÜCKT ---


    # --- HIER IST DER NEUE BUTTON SAUBER EINIGERÜCKT ---
    st.markdown("---")  # Eine kleine Trennlinie für die Optik
    st.subheader("🔄 Excel-Cache")
    st.write("Die Excel-Datei wird automatisch alle 10 Minuten neu eingelesen. Hier kannst du das Laden sofort erzwingen:")
    
    if st.button("🔥 Excel-Daten JETZT sofort neu einlesen", key="clear_cache_button"):
        st.cache_data.clear()  # Löscht den 10-Minuten-Cache sofort
        st.success("Der Cache wurde geleert! Die Excel-Datei wird beim nächsten Aufruf frisch geladen.")
        st.rerun()
    st.markdown("---")
        
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_admin"):
        set_view("Home")


		
# --- NEUER MENÜPUNKT: JUDGE LIST ---
