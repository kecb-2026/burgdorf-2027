# -*- coding: utf-8 -*-
"""Ansicht: Home – Status, Fortschritt der Runden, Menue in Bloecken, Hilfe."""
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from core.config import SHOW_YEAR
try:
    from core.config import COPYRIGHT_TEXT
except ImportError:   # aeltere eigene config.py
    COPYRIGHT_TEXT = f"© {SHOW_YEAR} KECB Burgdorf · Alle Rechte vorbehalten"
from core.data import load_labels
from core.progress import round_summary, table
from core.rounds import default_round, round_color, round_label, round_on_color, round_tint, tag_of, usable_rounds
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def _now_text():
    try:
        from zoneinfo import ZoneInfo
        n = datetime.now(ZoneInfo("Europe/Zurich"))
    except Exception:
        n = datetime.now()
    return n.strftime("%d.%m.%Y"), n.strftime("%H:%M")


def _go(label, view, params=None, key=None):
    """Menueknopf: setzt (wie bisher) die URL-Parameter und wechselt die Ansicht."""
    if st.button(label, key=key or f"home_{view}", use_container_width=True):
        if params:
            st.query_params.update(params)
        set_view(view)


def _adm(view):
    return {"view": view, "auth": "true", "role": "Admin"}


_CSS = """<style>
.st-key-blk_vor button { background:#e8a03a !important; color:#fff !important; border:none !important; }
.st-key-blk_show button { background:#1a4a9e !important; color:#fff !important; border:none !important; }
.st-key-blk_pub button { background:#3d7be0 !important; color:#fff !important; border:none !important; }
.st-key-blk_sys button { background:#6c757d !important; color:#fff !important; border:none !important; }
.home-foot { text-align:center; color:#888; font-size:13px; margin-top:30px; }
</style>"""


def render():
    store = get_store()
    st_autorefresh(interval=30000, key="home_refresh")
    display_header_with_logo(f"KECB Burgdorf {SHOW_YEAR}")
    st.markdown(_CSS, unsafe_allow_html=True)

    # ---------- Statuszeile ----------
    datum, uhr = _now_text()
    _t, _c, _l = store.data.get("test_live_tag"), store.data.get("test_live_cat"), store.data.get("test_live_label")
    if _t and _c is not None:
        _n = int(str(_t).split()[-1])
        live_txt = f"{round_label(_n, with_emoji=False)} · Kategorie {str(_c).replace('.0', '')} · {_l}"
    else:
        live_txt = "keine Klasse freigegeben"
    c1, c2, c3 = st.columns(3)
    c1.metric("Datum / Uhrzeit", f"{uhr} Uhr", datum, delta_color="off")
    c2.metric("Standard-Runde", round_label(default_round(store), with_emoji=False))
    c3.metric("Richter sehen jetzt", live_txt)

    # ---------- Aktive Runden + Fortschritt je Richter ----------
    df = load_labels()
    if df is not None:
        rounds = usable_rounds(store, df)
        st.markdown("##### Runden")
        cols = st.columns(max(1, len(rounds)))
        for col, n in zip(cols, rounds):
            cnt, done, total = round_summary(store, df, n)
            live = (str(_t) == tag_of(n))
            sub = f"{cnt} Richter aktuell · {done} von {total} gerichtet" if total else "keine Katzen"
            col.markdown(
                f"<div style='background:{round_color(n)}; color:{round_on_color(n)}; border-radius:12px; padding:10px 14px;'>"
                f"<div style='font-size:19px; font-weight:900;'>{round_label(n, with_emoji=False)}{' · ▶ Best in Show läuft' if live else ''}</div>"
                f"<div style='font-size:13px; opacity:.95;'>{sub}</div></div>", unsafe_allow_html=True)

        with st.expander("Noch zu richten: je Richter und Runde", expanded=False):
            rnds, rows = table(store, df)
            if not rows:
                st.info("Keine Richter im Excel gefunden.")
            else:
                head = "".join(f"<th style='background:{round_color(n)}; color:{round_on_color(n)}; padding:6px 10px;'>{round_label(n, with_emoji=False)}</th>" for n in rnds)
                body = ""
                for j, prog, cur in rows:
                    cells = ""
                    for n in rnds:
                        d, t = prog[n]
                        if t == 0:
                            txt = "–"
                        elif d >= t:
                            txt = "✅ fertig"
                        else:
                            txt = f"noch {t - d} von {t}"
                        mark = f"background:{round_tint(n)}; font-weight:800;" if n == cur else "color:#666;"
                        cells += f"<td style='padding:6px 10px; text-align:center; {mark}'>{txt}</td>"
                    body += f"<tr><td style='padding:6px 10px; font-weight:700;'>{j}</td>{cells}</tr>"
                st.markdown(f"<table style='width:100%; border-collapse:collapse;'><tr><th></th>{head}</tr>{body}</table>", unsafe_allow_html=True)
                st.caption("Hervorgehoben ist die aktuelle Runde des Richters (Rundenmanager). Abwesende Katzen zählen nicht mit.")

    # ---------- Menue in Bloecken ----------
    st.markdown("##### Vorbereitung")
    with st.container(key="blk_vor"):
        a, b, c = st.columns(3)
        with a:
            _go("🩺 CHECK", "Check")
            _go("📱 QR-CODE-GENERATOR", "QR_Codes_Gen", _adm("qr-gen"))
            _go("🖨️ NOMINATION-LABELS", "Nomination_Labels", _adm("nom-labels"))
        with b:
            _go("⚙️ EXCEL-UPLOAD", "Excel_Upload", _adm("excel-upload"))
            _go("📝 EXCEL LIVE-EDITOR", "Excel_Edit", _adm("excel-edit"))
            _go("📥 PDF-IMPORT", "Import_PDF", _adm("import-pdf"))
        with c:
            _go("🐈 RICHTER-LISTE", "Judge_List", _adm("judge-list"))
            _go("🐈 NOMINIERTE KATZEN", "Nominated_Cats", _adm("nominated"))

    st.markdown("##### Während der Show")
    with st.container(key="blk_show"):
        a, b, c = st.columns(3)
        with a:
            _go("🎛️ LIVE-ADMIN CONTROL", "Live_Admin", _adm("live-admin"))
            _go("🎛️ RUNDENMANAGER", "Rundenmanager", _adm("rundenmanager"), key="home_to_rundenmanager")
        with b:
            _go("📝 STEWARD-PULT", "Steward_Panel", {"view": "steward", "auth": "true", "role": "Steward"})
            _go("🧪 LIVE-VOTING (RICHTER)", "Live_Voting", _adm("live-voting"))
        with c:
            _go("🎤 MODERATOR", "Moderator")

    st.markdown("##### Anzeigen fürs Publikum")
    with st.container(key="blk_pub"):
        a, b, c = st.columns(3)
        with a:
            _go("📢 LIVE-DASHBOARD", "Dashboard", {"view": "katzenaufruf"})
        with b:
            _go("🏆 BEST IN SHOW (PUBLIC)", "BIS_Public", {"view": "bis"})
        with c:
            _go("📋 BIS-ABLAUF", "BIS_Ablauf")

    st.markdown("##### System")
    with st.container(key="blk_sys"):
        a, b, c = st.columns(3)
        with a:
            _go("⚙️ ADMIN-KONSOLE (RESET, BACKUP)", "Admin_Panel", _adm("admin"))
        with b:
            _go("❓ HILFE UND ANLEITUNGEN", "Hilfe")

    st.markdown(f"<div class='home-foot'>{COPYRIGHT_TEXT}</div>", unsafe_allow_html=True)
