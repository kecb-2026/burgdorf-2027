# -*- coding: utf-8 -*-
"""Ansicht: Hilfe – Anleitung je Modul (Admin kann die Texte bearbeiten)."""
import streamlit as st

from core.help_texts import get_help, reset_help, set_help
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    display_header_with_logo("Hilfe und Anleitungen")
    is_admin = st.session_state.get("user_role") == "Admin"
    st.caption("Kurze Anleitung zu jedem Modul." + (" Als Admin kannst du die Texte unten bearbeiten." if is_admin else ""))
    for key, title, text in get_help(store):
        with st.expander(title):
            st.markdown(text)
            if is_admin:
                if st.toggle("Text bearbeiten", key=f"help_edit_{key}"):
                    st.text_area("Text (Markdown)", value=text, key=f"help_ta_{key}", height=200)
                    c1, c2 = st.columns(2)
                    if c1.button("Speichern", key=f"help_save_{key}"):
                        set_help(store, key, st.session_state[f"help_ta_{key}"])
                        st.rerun()
                    if c2.button("Standardtext wiederherstellen", key=f"help_reset_{key}"):
                        reset_help(store, key)
                        st.session_state.pop(f"help_ta_{key}", None)
                        st.rerun()
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_help"):
        set_view("Home")
