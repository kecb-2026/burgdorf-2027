# -*- coding: utf-8 -*-
"""Kleine UI-Helfer."""
import streamlit as st
from core.config import LOGO_URL, SHOW_YEAR
from core.store import get_store


def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = "Public"
    st.session_state.view = "Dashboard"
    st.query_params.clear() # Löscht die Login-Parameter aus der URL beim Logout
    st.rerun()


def display_header_with_logo(text):
    col_text, col_logo = st.columns([5, 1]) 
    with col_text:
        st.markdown(f"<p class='header-text'>{text}</p>", unsafe_allow_html=True)
    with col_logo:
        st.markdown("<div style='display: flex; justify-content: flex-end;'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=100)
        st.markdown("</div>", unsafe_allow_html=True)


def render_overlay_html(row):
    kat_nr = str(row.get('KATALOG-NR', '')).replace('.0', '')
    rasse = row.get('RASSE', '')
    farbe = row.get('FARBE', '')
    name_gross = str(row.get('NAME', '')).upper()
    besitzer = f"{row.get('BESITZER VORNAME', '')} {row.get('BESITZER NACHNAME', '')}"
    return f"""
        <div class="overlay-backdrop"></div>
        <div class="winner-overlay">
            <div class="ov-header">{kat_nr}. {rasse} {farbe}</div>
            <div class="ov-cat-name">{name_gross}</div>
            <div class="ov-owner">{besitzer}</div>
            <div style="margin-top: 50px;">
            <div style="font-weight: bold; font-size: 22px; color: #1a4a9e; margin-top: 10px;">KECB BURGDORF {SHOW_YEAR}</div>
            </div>
        </div>
    """


def set_view(name):
    store = get_store()
    store.active_overlay = None   
    st.session_state.view = name
    st.rerun()
