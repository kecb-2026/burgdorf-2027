# -*- coding: utf-8 -*-
"""Ansicht: Admin_Panel"""
import streamlit as st
from core.imports import HANDY_LOCK_KEY, reset_keep_protected
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    display_header_with_logo("⚙️ Admin-Konsole")
    
    _reset_ok = st.checkbox("Ja, wirklich ALLE Stimmen und Status löschen", key="confirm_reset_all")
    _keep_imp = st.checkbox("PDF-Importlisten (Abwesende / Nominierte) behalten", value=True, key="reset_keep_imports")
    if st.button("ALLE DATEN ZURÜCKSETZEN", disabled=not _reset_ok):
        reset_keep_protected(store, keep=_keep_imp)
        store.active_overlay = None
        store.save_backup()
        st.success("Speicher geleert!")

    # --- NOTAUSKNOPF: Handy-Ansicht fuer Aussteller sperren ---
    st.markdown("---")
    st.subheader("🛑 Notausknopf Handy-Ansicht")
    st.write("Wenn der Server zu stark belastet wird: Sperrt die Handy-Seite für alle Aussteller. "
             "Sie sehen nur noch einen Hinweis, es werden keine Katzendaten mehr geladen und die Seite "
             "aktualisiert sich nur noch alle 5 Minuten. Richter, Steward und Dashboard sind nicht betroffen.")
    _locked = bool(store.data.get(HANDY_LOCK_KEY, False))
    _new = st.toggle("Handy-Ansicht für Aussteller sperren", value=_locked, key="handy_lock_toggle")
    if _new != _locked:
        store.data[HANDY_LOCK_KEY] = _new
        store.save_backup()
        st.rerun()
    if _locked:
        st.error("🛑 Die Handy-Ansicht ist GESPERRT. Aussteller sehen nur den Hinweis.")
    else:
        st.success("✅ Die Handy-Ansicht ist freigegeben.")

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
