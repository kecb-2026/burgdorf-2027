# -*- coding: utf-8 -*-
"""Ansicht: Live_Handy – schlanke Aufruf-Ansicht fuer Aussteller auf dem Handy (ohne Login).
Oben ein Auswahlfeld fuer den Richter, darunter dessen aufgerufene Katzen untereinander."""
import html as _h
import time
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo('Europe/Zurich')
except Exception:
    _TZ = None
from streamlit_autorefresh import st_autorefresh
import streamlit as st
from core.data import get_full_label, load_labels
from core.imports import is_absent
from core.rounds import all_judges, judge_cats, judge_round, round_color, round_label, round_on_color, round_tint, tag_of
from core.store import get_store

TAG_TEXT = {"Wird gerichtet": ("Am Richtertisch", "#ff9800", "white"),
            "Zum Richten": ("Aufgerufen", "#007bff", "white"),
            "BIV": ("BIV", "#28a745", "white"),
            "NOM": ("Nominiert", "#ffc107", "black")}


def _by_judge(store, df_full):
    judges = [j for j in all_judges(df_full) if not judge_cats(df_full, j, judge_round(store, j), gated=True).empty]
    if not judges:
        st.info("Zurzeit läuft keine Runde.")
        return

    pre = st.session_state.get("url_judge", "--")
    idx = judges.index(pre) + 1 if pre in judges else 0
    j = st.selectbox("Welchen Richter möchten Sie sehen?", ["--"] + judges, index=idx, key="live_handy_judge")
    if j == "--":
        st.info("Bitte oben einen Richter wählen.")
        return

    rn = judge_round(store, j)
    df_tag = judge_cats(df_full, j, rn, gated=True)
    st.markdown(
        f"<div style='background:{round_color(rn)}; color:{round_on_color(rn)}; border-radius:10px; padding:8px 12px; "
        f"font-weight:900; font-size:20px; text-align:center; margin:6px 0 12px 0;'>{_h.escape(j)} · {round_label(rn)}</div>",
        unsafe_allow_html=True)

    entries = []
    for k, v in store.data.items():
        if not (isinstance(k, str) and "|" in k and isinstance(v, dict)):
            continue
        nr, judge = k.split("|", 1)
        if judge != j:
            continue
        m = df_tag[df_tag["KAT_STR"] == nr]
        if m.empty:
            continue
        flags = v.get("flags", {}) if isinstance(v.get("flags"), dict) else {}
        if flags.get("Gerichtet"):
            continue
        tags = []
        if flags.get("Wird gerichtet"):
            tags.append("Wird gerichtet")
        elif flags.get("Zum Richten"):
            tags.append("Zum Richten")
        for t in ("BIV", "NOM"):
            if flags.get(t):
                tags.append(t)
        if tags:
            entries.append((0 if "Wird gerichtet" in tags else 1, v.get("timestamp", 0), nr, m.iloc[0], tags))
    entries.sort(key=lambda e: (e[0], e[1]))

    if not entries:
        st.info("Zurzeit ist bei diesem Richter keine Katze aufgerufen.")
    for _, _, nr, row, tags in entries:
        chips = "".join(
            f"<span style='background:{TAG_TEXT[t][1]}; color:{TAG_TEXT[t][2]}; padding:3px 10px; border-radius:6px; "
            f"font-weight:bold; font-size:15px; margin:2px;'>{TAG_TEXT[t][0]}</span>" for t in tags)
        st.markdown(
            f"<div style='background:{round_tint(rn)}; border:2px solid {round_color(rn)}; border-radius:14px; "
            f"padding:10px; margin-bottom:10px; text-align:center;'>"
            f"<div style='font-size:48px; font-weight:900; color:#1a4a9e; line-height:1.0;'>{_h.escape(nr)}</div>"
            f"<div style='font-size:18px; font-weight:bold; color:#333; margin:4px 0;'>{_h.escape(get_full_label(row))}</div>"
            f"<div>{chips}</div></div>",
            unsafe_allow_html=True)
    st.caption("Die Anzeige aktualisiert sich automatisch.")


def _called_info(store, nr, judge):
    """HTML-Zeile 'Aufgerufen um HH:MM (vor N Min.)' oder ''. Ab 10 Min. rot/Warnung."""
    v = store.data.get(f"{nr}|{judge}")
    if not isinstance(v, dict):
        return ""
    ts = v.get("called_at") or v.get("timestamp") or 0
    if not ts:
        return ""
    mins = max(0, int((time.time() - float(ts)) // 60))
    clock = datetime.fromtimestamp(float(ts), _TZ).strftime("%H:%M")
    late = mins >= 10
    warn = " ⚠️ Bitte sofort zum Richtertisch!" if late else ""
    col = "#b71c1c" if late else "#333"
    return (f"<br><span style='color:{col}; font-weight:{'900' if late else 'bold'};'>"
            f"🕒 Aufgerufen um {clock} Uhr (vor {mins} Min.){warn}</span>")


def _status_of(store, nr, judge):
    v = store.data.get(f"{nr}|{judge}")
    flags = v.get("flags", {}) if isinstance(v, dict) and isinstance(v.get("flags"), dict) else {}
    if flags.get("Gerichtet"):
        return "done", "Gerichtet ✔"
    if flags.get("Wird gerichtet"):
        return "table", "Am Richtertisch"
    if flags.get("Zum Richten"):
        return "called", "Aufgerufen – bitte zum Richtertisch"
    return "wait", "Noch nicht aufgerufen"


def _my_cats(store, df_full):
    opts_df = df_full.copy()
    opts_df["_n"] = opts_df["KAT_STR"].apply(lambda x: int(x) if str(x).isdigit() else 99999)
    opts_df = opts_df.sort_values("_n")
    labels = {str(r["KAT_STR"]): f"{r['KAT_STR']} · {get_full_label(r)}" for _, r in opts_df.iterrows()}
    if "lh_cats" not in st.session_state:
        raw = st.query_params.get("cat", "")
        st.session_state["lh_cats"] = [c for c in str(raw).replace(" ", "").split(",") if c in labels]
    st.multiselect("Meine Katzen (Nummer eingeben oder auswählen):", list(labels), key="lh_cats",
                   format_func=lambda c: labels.get(c, c))
    mine = st.session_state["lh_cats"]
    st.query_params["cat"] = ",".join(mine)
    if not mine:
        st.info("Wählen Sie oben Ihre Katze(n). Tipp: Speichern Sie diese Seite als Lesezeichen oder auf dem Home-Bildschirm, dann bleibt Ihre Auswahl erhalten.")
        return

    alerts = []
    cards = []
    for nr in mine:
        m = df_full[df_full["KAT_STR"] == nr]
        if m.empty:
            continue
        row = m.iloc[0]
        lines = []
        for n in (1, 2, 3):
            tag, rc = tag_of(n), f"RICHTER TAG {n}"
            if tag not in df_full.columns or str(row.get(tag, "")).strip().upper() != "X":
                continue
            judge = str(row.get(rc, "")).strip()
            kind, text = _status_of(store, nr, judge)
            if is_absent(store, nr, n):
                kind, text = "absent", "🚫 Als abwesend gemeldet"
            if kind in ("called", "table"):
                alerts.append((nr, judge, kind))
            col = {"called": "#d32f2f", "table": "#ff9800", "done": "#2e7d32", "wait": "#555", "absent": "#666"}[kind]
            lines.append(
                f"<div style='margin-top:6px; padding:6px 8px; border-left:8px solid {round_color(n)}; background:{round_tint(n)}; "
                f"border-radius:6px; text-align:left;'><b>{round_label(n)}</b> · {_h.escape(judge)}<br>"
                f"<span style='color:{col}; font-weight:bold;'>{text}</span>{_called_info(store, nr, judge) if kind in ('called','table') else ''}</div>")
        cards.append((nr, row, "".join(lines)))

    if alerts:
        txt = " · ".join(f"Katze {nr} ({_h.escape(j)})" for nr, j, _ in alerts)
        st.markdown(
            "<style>@keyframes lhblink{50%{opacity:.35}}</style>"
            f"<div style='background:#d32f2f; color:white; border-radius:12px; padding:14px; margin:8px 0 14px 0; text-align:center; "
            f"font-size:22px; font-weight:900; animation:lhblink 1s linear infinite;'>🔔 {txt}<br>wird aufgerufen – bitte zum Richtertisch!</div>",
            unsafe_allow_html=True)
        sig = ",".join(f"{a[0]}{a[2]}" for a in alerts)
        st.components.v1.html(
            "<script>try{navigator.vibrate&&navigator.vibrate([400,200,400,200,400]);}catch(e){}"
            "try{var c=new (window.AudioContext||window.webkitAudioContext)();var o=c.createOscillator();o.frequency.value=880;"
            "o.connect(c.destination);o.start();setTimeout(function(){o.stop();},500);}catch(e){}"
            f"/* {sig} */</script>", height=0)

    for nr, row, lines in cards:
        st.markdown(
            f"<div style='border:2px solid #1a4a9e; border-radius:14px; padding:10px; margin-bottom:10px;'>"
            f"<div style='text-align:center;'><span style='font-size:40px; font-weight:900; color:#1a4a9e;'>{_h.escape(nr)}</span>"
            f"<div style='font-size:17px; font-weight:bold; color:#333;'>{_h.escape(get_full_label(row))}</div></div>{lines}</div>",
            unsafe_allow_html=True)


def render():
    store = get_store()
    st_autorefresh(interval=60000, key="live_handy_refresh")
    st.markdown("<style>.block-container{padding-top:1rem; max-width:560px;}</style>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:22px; font-weight:900; color:#1a4a9e; margin-bottom:6px;'>📢 Katzenaufruf</div>", unsafe_allow_html=True)

    df_full = load_labels()
    if df_full is None:
        st.error("Daten momentan nicht verfügbar.")
        return

    # Mit Richter-QR (judge=...) startet die Ansicht beim Richter, sonst bei "Meine Katzen"
    has_judge = st.session_state.get("url_judge", "--") != "--"
    modes = ["⭐ Meine Katzen", "👩‍⚖️ Nach Richter"]
    mode = st.radio("Ansicht", modes, index=1 if has_judge else 0, horizontal=True, key="lh_mode", label_visibility="collapsed")
    if mode == modes[0]:
        _my_cats(store, df_full)
    else:
        _by_judge(store, df_full)
