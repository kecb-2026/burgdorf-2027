# -*- coding: utf-8 -*-
"""Runden-Logik: welche Runde gilt global / fuer welchen Richter?

Gespeichert im globalen Store:
  store.data["showtype"]       Name des Showtyps (siehe config.SHOWTYPES)
  store.data["round_default"]  Standard-Runde (Zahl), gilt fuer alle ohne eigene Runde
  store.data["judge_round"]    {Richtername: Rundenzahl}  (nur Abweichungen vom Standard)
  store.data["admin_selected_day"]  wird mitgefuehrt ("Tag n"), damit aeltere Seiten funktionieren
"""
import re

from core.config import ROUNDS, SHOWTYPES, DEFAULT_SHOWTYPE


def active_rounds(store):
    """Liste der Rundenzahlen, die im aktuellen Showtyp existieren."""
    st_name = store.data.get("showtype", DEFAULT_SHOWTYPE)
    return list(SHOWTYPES.get(st_name, SHOWTYPES[DEFAULT_SHOWTYPE]))


def _to_int(value, default=1):
    m = re.search(r"\d+", str(value))
    return int(m.group()) if m else default


def default_round(store):
    """Standard-Runde. Faellt auf das alte Feld admin_selected_day zurueck."""
    if "round_default" in store.data:
        n = _to_int(store.data["round_default"])
    else:
        n = _to_int(store.data.get("admin_selected_day", "Tag 1"))
    return n if n in ROUNDS else 1


def judge_round(store, judge):
    """Aktuelle Runde eines Richters (eigene Einstellung oder Standard)."""
    jr = store.data.get("judge_round", {})
    if isinstance(jr, dict) and judge in jr:
        n = _to_int(jr[judge])
        if n in ROUNDS:
            return n
    return default_round(store)


def set_default_round(store, n, reset_judges=False):
    store.data["round_default"] = int(n)
    store.data["admin_selected_day"] = f"Tag {int(n)}"
    if reset_judges:
        store.data["judge_round"] = {}
    store.save_backup()


def set_judge_round(store, judge, n):
    jr = store.data.get("judge_round")
    if not isinstance(jr, dict):
        jr = {}
    if int(n) == default_round(store):
        jr.pop(judge, None)          # entspricht dem Standard, kein Eintrag noetig
    else:
        jr[judge] = int(n)
    store.data["judge_round"] = jr
    store.save_backup()


def tag_of(n):
    """Rundenzahl -> Spalten-/Schluesselname, z. B. 2 -> 'TAG 2'."""
    return f"TAG {int(n)}"


def round_label(n, with_emoji=True):
    r = ROUNDS.get(int(n), {"name": f"Runde {n}", "emoji": ""})
    txt = f"Runde {r['name']}"
    return f"{r['emoji']} {txt}" if with_emoji and r.get("emoji") else txt


def round_color(n):
    return ROUNDS.get(int(n), ROUNDS[1])["color"]


def round_tint(n):
    return ROUNDS.get(int(n), ROUNDS[1])["tint"]


def all_judges(df):
    """Alle echten Richter ueber alle vorhandenen RICHTER-TAG-Spalten."""
    from core.data import real_judges
    names = set()
    for n in ROUNDS:
        col = f"RICHTER TAG {n}"
        if col in df.columns:
            names.update(real_judges(df[col]))
    return sorted(names)


def judge_cats(df, judge, n, gated=False):
    """Zeilen des Excels, die der Richter in Runde n richtet.
    gated=True: Kategorien, die im Rundenmanager fuer diese Runde gesperrt sind, werden weggelassen."""
    tag, rc = tag_of(n), f"RICHTER TAG {n}"
    if tag not in df.columns or rc not in df.columns:
        return df.iloc[0:0]
    out = df[(df[tag].astype(str).str.strip().str.upper() == "X") & (df[rc].astype(str).str.strip() == judge)]
    if gated and not out.empty:
        from core.gate import blocked_cats, cat_key
        from core.store import get_store
        bl = blocked_cats(get_store(), n)
        if bl:
            out = out[~out["KATEGORIE"].apply(cat_key).isin(bl)]
    return out


def busy_elsewhere(store, nr, judge):
    """Wo ist die Katze gerade belegt (Aufgerufen / Wird gerichtet / BIV / NOM)?
    Gibt eine Liste (anderer_richter, status_text) zurueck. Eigener Eintrag zaehlt nicht."""
    out = []
    prefix = f"{nr}|"
    for key, val in store.data.items():
        if not (isinstance(key, str) and key.startswith(prefix) and "|" in key):
            continue
        other = key.split("|", 1)[1]
        if other == judge or not isinstance(val, dict):
            continue
        flags = val.get("flags", {})
        if not isinstance(flags, dict) or flags.get("Gerichtet"):
            continue
        for fl, txt in (("Wird gerichtet", "wird gerichtet"), ("Zum Richten", "aufgerufen"),
                        ("BIV", "BIV"), ("NOM", "Nomination")):
            if flags.get(fl):
                out.append((other, txt))
                break
    return out


def round_on_color(n):
    """Schriftfarbe, die auf der Rundenfarbe gut lesbar ist."""
    return ROUNDS.get(int(n), ROUNDS[1]).get("on_color", "#ffffff")


def usable_rounds(store, df):
    """Aktive Runden, fuer die das Excel die passenden Spalten hat (TAG n bzw. SELECTION n)."""
    return [n for n in active_rounds(store) if f"TAG {n}" in df.columns or f"SELECTION {n}" in df.columns]
