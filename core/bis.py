# -*- coding: utf-8 -*-
"""BIS 'bereit' je Runde und Kategorie.
Bereit = alle Katzen dieser Kategorie in dieser Runde sind gerichtet (Steward-Knopf GERICHTET)
oder abwesend. Die Ausstellungsleitung kann zusaetzlich von Hand 'bereit' setzen."""
from core.gate import cat_key
from core.imports import is_absent
from core.rounds import tag_of


def _manual_key(n, cat):
    return f"bis_ready_{tag_of(n)}_{cat_key(cat)}"


def cat_status(store, df, n, cat):
    """Gibt dict zurueck: total, open (Liste Katzennummern), ready (bool), manual (bool)."""
    tag, rc = tag_of(n), f"RICHTER TAG {n}"
    manual = bool(store.data.get(_manual_key(n, cat), False))
    if df is None or tag not in df.columns or rc not in df.columns:
        return {"total": 0, "open": [], "ready": manual, "manual": manual}
    sub = df[(df[tag].astype(str).str.strip().str.upper() == "X") & (df["KATEGORIE"].apply(cat_key) == cat_key(cat))]
    open_nrs, total = [], 0
    for _, r in sub.iterrows():
        nr, judge = str(r["KAT_STR"]), str(r[rc]).strip()
        if is_absent(store, nr):
            continue
        total += 1
        v = store.data.get(f"{nr}|{judge}")
        flags = v.get("flags", {}) if isinstance(v, dict) else {}
        if not (isinstance(flags, dict) and flags.get("Gerichtet")):
            open_nrs.append(nr)
    auto = total > 0 and not open_nrs
    return {"total": total, "open": open_nrs, "ready": auto or manual, "manual": manual and not auto}


def set_manual_ready(store, n, cat, val):
    store.data[_manual_key(n, cat)] = bool(val)
    store.save_backup()
