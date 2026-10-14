# -*- coding: utf-8 -*-
"""Check: sammelt Ergebnisse als Liste von (status, text, hinweis_seite).
status: 'ok' | 'warn' | 'err' | 'info'.  hinweis_seite: Name der Ansicht fuer den Knopf (oder None)."""
import importlib.util

import streamlit as st

from core.access import key_required, using_default_passwords
from core.autonext import get_cfg
from core.backup import get_auto_copy
from core.config import EXCEL_FILE, SHOW_DATES, MIN_AGE_MONTHS
from core.gate import get_show_day
from core.imports import HANDY_LOCK_KEY, last_import
from core.rounds import usable_rounds, round_label


def _has(mod):
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def technik(store):
    res = []
    # Datenbank: lesen + den aktuellen Stand zurueckschreiben (aendert nichts, prueft aber das Schreiben)
    try:
        store._fetch_remote()
        ok_read = True
    except Exception as e:
        ok_read = False
        res.append(("err", f"Datenbank nicht lesbar: {e}", None))
    if ok_read:
        if not store.loaded_ok:
            res.append(("err", "Datenbank erreichbar, aber der Stand wurde beim Start nicht geladen.", None))
        elif store.save_backup():
            res.append(("ok", "Datenbank erreichbar (lesen und schreiben)", None))
        else:
            res.append(("err", f"Datenbank lesbar, aber Schreiben fehlgeschlagen. {store.last_error or ''}", None))
    # Pakete
    miss = [n for n, m in (("pypdf", "pypdf"), ("reportlab", "reportlab"), ("qrcode", "qrcode"),
                           ("openpyxl", "openpyxl"), ("streamlit-autorefresh", "streamlit_autorefresh")) if not _has(m)]
    if miss:
        res.append(("err", "Fehlende Pakete (requirements.txt): " + ", ".join(miss), None))
    else:
        res.append(("ok", "PDF-Import, PDF-Erstellung, QR-Codes und Auto-Aktualisierung bereit", None))
    # Excel
    from core.data import load_labels
    df = load_labels()
    if df is None:
        res.append(("err", f"Excel-Datei {EXCEL_FILE} nicht lesbar", "Excel_Upload"))
    else:
        res.append(("ok", f"Excel-Datei gelesen: {len(df)} Katzen", None))
    # Secrets
    if key_required():
        res.append(("ok", "Zugriffsschutz aktiv (ACCESS_KEY gesetzt)", None))
    else:
        res.append(("err", "Zugriffsschutz fehlt: ACCESS_KEY ist nicht gesetzt", None))
    if using_default_passwords():
        res.append(("warn", "Es gelten noch Standard-Passwörter (PW_ADMIN, PW_STEWARD, PW_RICHTER fehlen)", None))
    try:
        has_gh = bool(st.secrets.get("GITHUB_TOKEN")) and bool(st.secrets.get("GITHUB_REPO"))
    except Exception:
        has_gh = False
    res.append(("ok", "GitHub-Zugang für Excel-Upload vorhanden", None) if has_gh
               else ("warn", "GITHUB_TOKEN/GITHUB_REPO fehlen: Excel-Upload und Live-Editor speichern nicht", None))
    # Sicherung
    ac = get_auto_copy(store)
    res.append(("ok", f"Automatische Kopie vorhanden ({ac['time']})", None) if ac
               else ("info", "Noch keine automatische Kopie (entsteht vor Reset/Wiederherstellen). Tipp: Sicherung herunterladen.", "Admin_Panel"))
    return res, df


def ausstellung(store, df):
    res = []
    if df is None:
        return [("err", "Ohne Excel-Daten keine Prüfung möglich", "Excel_Upload")]
    # Anzahl
    runden = usable_rounds(store, df)
    teile = []
    for n in runden:
        col = f"SELECTION {n}"
        k = int((df[col].astype(str).str.strip().str.upper() == "X").sum()) if col in df.columns else 0
        teile.append(f"{round_label(n, with_emoji=False)}: {k} nominiert")
    res.append(("info", f"{len(df)} Katzen gesamt · " + " · ".join(teile), None))
    # Alter
    from core.age import check, class_age_check
    d1, d2 = SHOW_DATES
    if "GEBURTSDATUM" not in df.columns:
        res.append(("err", "Spalte GEBURTSDATUM fehlt in der Excel-Datei", "Alters_Check"))
    else:
        a = check(df, d1, d2, MIN_AGE_MONTHS)
        bad = int((~a["Status"].str.startswith("✅")).sum())
        res.append(("ok", f"Alle Katzen mindestens {MIN_AGE_MONTHS} Monate alt", None) if bad == 0
                   else ("warn", f"{bad} Katze(n) mit Alters-Auffälligkeit (zu jung oder Datum fehlt)", "Alters_Check"))
        c = class_age_check(df, d1, d2)
        cbad = 0 if c.empty else int((~c["Status"].str.startswith("✅")).sum())
        res.append(("ok", "Alter passt zu Klasse 12 (4–8 Mon.) und Klasse 11 (8–12 Mon.)", None) if cbad == 0
                   else ("warn", f"{cbad} Katze(n) passen altersmässig nicht zur Klasse 11/12", "Alters_Check"))
    # Nominationen
    from core.nomcheck import nomination_problems
    probs = nomination_problems(df, store)
    v = sum(p["violation"] for p in probs)
    dp = sum(p["dups"] for p in probs)
    ov = sum(p["overload"] for p in probs)
    res.append(("ok", "Keine Klassen-Verstösse bei den Nominationen", None) if v == 0
               else ("warn", f"Klassen-Verstösse bei den Nominationen ({v} Richter betroffen)", "Nominated_Cats"))
    if dp:
        res.append(("warn", f"{dp} Katze(n) mehrfach nominiert", "Nominated_Cats"))
    if ov:
        res.append(("warn", f"{ov} Richter-Kategorie(n) über dem Limit von 8", "Nominated_Cats"))
    # Importlisten
    for n in runden:
        ab_t, nom_t, ab_n, nom_n = last_import(store, n)
        rn = round_label(n, with_emoji=False)

        def fmt(t):
            return "kein Importzeitpunkt gespeichert (älterer Import)" if t == "" else f"zuletzt importiert {t}"
        res.append(("ok" if nom_t else "warn",
                    f"{rn} · Nominierte: " + (f"{nom_n} Katzen, {fmt(nom_t)}" if nom_t is not None else "keine PDF-Liste importiert (es gilt die Excel-Nomination)"),
                    None if nom_t else "Import_PDF"))
        res.append(("ok" if ab_t else "warn",
                    f"{rn} · Abwesende: " + (f"{ab_n} Katzen, {fmt(ab_t)}" if ab_t is not None else "keine PDF-Liste importiert"),
                    None if ab_t else "Import_PDF"))
    # Einstellungen
    locked = bool(store.data.get(HANDY_LOCK_KEY, False))
    cfg = get_cfg(store)
    res.append(("warn" if locked else "ok", "Notausknopf: Handy-Ansicht GESPERRT" if locked else "Notausknopf: Handy-Ansicht frei",
                "Admin_Panel" if locked else None))
    res.append(("ok" if cfg["enabled"] else "info",
                f"Automatisches Weiterschalten: an ({cfg['delay']} s)" if cfg["enabled"] else "Automatisches Weiterschalten: aus",
                None if cfg["enabled"] else "Live_Admin"))
    res.append(("info", f"Showtag eingestellt: {get_show_day(store)}", "Rundenmanager"))
    # Probedaten
    votes = store.data.get("votes", {})
    n_votes = len(votes) if hasattr(votes, "__len__") else 0
    n_win = sum(1 for k, v in store.data.items() if str(k).startswith("winner_reveal_") and v)
    n_stew = sum(1 for k, v in store.data.items() if isinstance(k, str) and "|" in k and isinstance(v, dict) and "flags" in v)
    if n_votes or n_win or n_stew:
        res.append(("warn", f"Noch Daten im Speicher: {n_votes} Stimmen, {n_win} gezeigte Gewinner, {n_stew} Steward-Einträge. Vor der Show im Admin zurücksetzen, falls es Probedaten sind.", "Admin_Panel"))
    else:
        res.append(("ok", "Keine Stimmen oder Steward-Einträge im Speicher", None))
    return res
