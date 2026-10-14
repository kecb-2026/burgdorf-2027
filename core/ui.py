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
    import re as _re
    text = _re.sub(r"^[^\w<]+", "", str(text)).strip() or str(text)   # Emojis/Symbole vor dem Titel weglassen
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


def round_banner(tag, big=False, cat=None):
    """Farbiger Balken mit der aktiven Runde (tag z. B. 'TAG 2')."""
    import re as _re
    from core.rounds import round_color, round_label, round_on_color
    m = _re.search(r"(\d+)", str(tag))
    n = int(m.group(1)) if m else 1
    fs = "clamp(15px, 1.5vw, 22px)" if big else "clamp(13px, 1.2vw, 17px)"
    st.markdown(
        f"<div style='background:{round_color(n)}; color:{round_on_color(n)}; border-radius:12px; "
        f"padding:{'5px' if big else '3px'} 12px; margin:2px 0 8px 0; text-align:center; "
        f"font-weight:900; text-transform:uppercase; letter-spacing:.05em; font-size:{fs}; line-height:1.15;'>"
        f"{round_label(n)}{' – Kategorie ' + str(cat).replace('.0', '') if cat not in (None, '') else ''}</div>",
        unsafe_allow_html=True)


def order_strip(order, current=None):
    """Kleine Leiste: Reihenfolge der Kategorien beim BIS, aktuelle Kategorie hervorgehoben."""
    cur = str(current).replace(".0", "") if current is not None else None
    parts = []
    for i, c in enumerate(order, 1):
        on = (c == cur)
        parts.append(
            f"<span style='display:inline-block; padding:2px 10px; border-radius:8px; margin:0 3px; font-weight:{'900' if on else '600'}; "
            f"background:{'#1a4a9e' if on else '#e9ecef'}; color:{'white' if on else '#333'};'>{i}. Kat {c}</span>")
    st.markdown("<div style='text-align:center; font-size:15px; margin:0 0 8px 0; color:#555;'>Reihenfolge: "
                + " ➜ ".join(parts) + "</div>", unsafe_allow_html=True)
