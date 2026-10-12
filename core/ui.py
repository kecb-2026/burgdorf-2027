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


def judge_header_html(name, all_names, bg=None, fg=None, border=None, sub=None, extra_class=""):
    """Richter-Kopf: Vorname / Nachname in 2 Zeilen, gleiche Schrift fuer alle, kein Umbruch mitten im Wort.
    Die Schriftgroesse richtet sich (via Container-Query) nach dem laengsten Wort aller Richter und der Spaltenbreite."""
    import html as _h
    def split(n):
        parts = str(n).split()
        if len(parts) <= 1:
            return str(n), ""
        return parts[0], " ".join(parts[1:])
    longest = max([max(len(w) for w in str(n).split()) if str(n).split() else 1 for n in all_names] + [6])
    fs = min(13.0, 88.0 / (0.72 * longest))  # cqw
    a, b = split(name)
    style = ""
    if bg: style += f"background-color:{bg};"
    if fg: style += f"color:{fg};"
    if border: style += f"border-color:{border};"
    sub_html = f"<div class='jh-sub'>{_h.escape(sub)}</div>" if sub else ""
    return (f"<div class='jh-wrap'><div class='jh-box {extra_class}' style='{style}--jhfs:{fs:.2f}cqw;'>"
            f"<div class='jh-first'>{_h.escape(a)}</div><div class='jh-last'>{_h.escape(b)}</div>{sub_html}</div></div>")


def round_banner(tag, big=False):
    """Farbiger Balken mit der aktiven Runde (tag z. B. 'TAG 2')."""
    import re as _re
    from core.rounds import round_color, round_label, round_on_color
    m = _re.search(r"(\d+)", str(tag))
    n = int(m.group(1)) if m else 1
    fs = "clamp(26px, 3vw, 46px)" if big else "clamp(20px, 2.2vw, 32px)"
    st.markdown(
        f"<div style='background:{round_color(n)}; color:{round_on_color(n)}; border-radius:12px; "
        f"padding:{'12px' if big else '8px'} 16px; margin:4px 0 14px 0; text-align:center; "
        f"font-weight:900; text-transform:uppercase; letter-spacing:.06em; font-size:{fs}; line-height:1.15;'>"
        f"{round_label(n)}</div>",
        unsafe_allow_html=True)
