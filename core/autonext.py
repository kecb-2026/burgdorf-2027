# -*- coding: utf-8 -*-
"""Automatisch zur naechsten Klasse weiterschalten, nachdem der Moderator den Gewinner gezeigt hat.

Ablauf: Gewinner zeigen -> nach N Sekunden (Standard 30) wird fuer die Richter die naechste
Klasse freigegeben (Reihenfolge: Kitten W/M, Junior W/M, Kastraten W/M, Adult W/M). Ist eine
Kategorie durch, geht es mit der naechsten Kategorie der BIS-Reihenfolge weiter (wieder bei
Kitten W). Klassen ohne nominierte Katzen oder mit bereits gezeigtem Gewinner werden uebersprungen.

Der Admin hat immer Vorrang: Jede Aenderung der Freigabe von Hand (oder ein anderer aktiver
Stand als beim Planen) bricht den geplanten Wechsel ab.
"""
import time

from core.config import NO_CLASS_CATEGORIES, NO_CLASS_LABEL
from core.data import class_mask, load_labels, with_selection
from core.gate import cat_key, get_bis_order

AUTO_KEY = "bis_auto"            # {"enabled": bool, "delay": int}   (ueberlebt den Reset)
PENDING_KEY = "bis_auto_pending"  # {"tag","cat","label","due"}  (fluechtig)
DEFAULT_DELAY = 30

# Reihenfolge der Klassen beim BIS: (Label, Klassen, Geschlecht)
CLASS_ORDER = [
    ("Kitten 4-8 Female", [12], "W"),
    ("Kitten 4-8 Male", [12], "M"),
    ("Junior 8-12 Female", [11], "W"),
    ("Junior 8-12 Male", [11], "M"),
    ("Neuter Female", [2, 4, 6, 8, 10], "W"),
    ("Neuter Male", [2, 4, 6, 8, 10], "M"),
    ("Adult Female", [1, 3, 5, 7, 9], "W"),
    ("Adult Male", [1, 3, 5, 7, 9], "M"),
]


def get_cfg(store):
    d = store.data.get(AUTO_KEY)
    d = d if isinstance(d, dict) else {}
    try:
        delay = int(d.get("delay", DEFAULT_DELAY))
    except (TypeError, ValueError):
        delay = DEFAULT_DELAY
    return {"enabled": bool(d.get("enabled", True)), "delay": max(5, min(300, delay))}


def set_cfg(store, enabled=None, delay=None):
    cur = get_cfg(store)
    if enabled is not None:
        cur["enabled"] = bool(enabled)
    if delay is not None:
        cur["delay"] = max(5, min(300, int(delay)))
    store.data[AUTO_KEY] = cur
    if not cur["enabled"]:
        store.data.pop(PENDING_KEY, None)
    store.save_backup()


def _live(store):
    return (store.data.get("test_live_tag"), store.data.get("test_live_cat"), store.data.get("test_live_label"))


def get_pending(store):
    p = store.data.get(PENDING_KEY)
    return p if isinstance(p, dict) else None


def cancel(store, save=True):
    if store.data.pop(PENDING_KEY, None) is not None and save:
        store.save_backup()


def schedule(store, tag, cat, label):
    """Wird aufgerufen, wenn der Gewinner einer Klasse gezeigt wird. Plant den Wechsel nur,
    wenn genau diese Klasse gerade fuer die Richter freigegeben ist."""
    cfg = get_cfg(store)
    if not cfg["enabled"]:
        return
    if _live(store) != (tag, cat, label):
        return
    store.data[PENDING_KEY] = {"tag": tag, "cat": cat, "label": label, "due": time.time() + cfg["delay"]}
    # kein save_backup noetig: der Aufrufer speichert direkt danach


def _classes_of(cat):
    if cat_key(cat) in NO_CLASS_CATEGORIES:
        return [(NO_CLASS_LABEL, None, None)]
    return CLASS_ORDER


def next_target(store, df, tag, cat, label):
    """(cat, label) der naechsten Klasse nach (cat, label) oder None, wenn die BIS durch ist."""
    d = with_selection(df, tag)
    d = d[d["SELECTION"] == "X"]
    raw_cats = {cat_key(c): c for c in df["KATEGORIE"].unique() if str(c).strip() not in ("", "nan", "-")}
    all_cats = sorted(raw_cats, key=lambda x: (0, int(x)) if x.isdigit() else (1, x))
    order = get_bis_order(store, tag, all_cats)
    ck = cat_key(cat)

    def usable(c, lab, kl, g):
        if store.data.get(f"winner_reveal_{tag}_{c}_{lab}", False):
            return False   # Gewinner dieser Klasse wurde schon gezeigt
        sub = d[(d["KATEGORIE"] == raw_cats[c]) & class_mask(d, kl, g)]
        return not sub.empty

    # 1. Rest der aktuellen Kategorie
    classes = _classes_of(cat)
    labels = [c[0] for c in classes]
    start = labels.index(label) + 1 if label in labels else 0
    for lab, kl, g in classes[start:]:
        if ck in raw_cats and usable(ck, lab, kl, g):
            return raw_cats[ck], lab
    # 2. Folgende Kategorien der BIS-Reihenfolge
    pos = order.index(ck) + 1 if ck in order else 0
    for c in order[pos:]:
        if c not in raw_cats:
            continue
        for lab, kl, g in _classes_of(c):
            if usable(c, lab, kl, g):
                return raw_cats[c], lab
    return None


def _py(x):
    return x.item() if hasattr(x, "item") else x


def jump_to_next(store, df=None):
    """Sofort zur naechsten Klasse wechseln (geplant oder von Hand). True, wenn gewechselt wurde."""
    if df is None:
        df = load_labels()
    tag, cat, label = _live(store)
    if df is None or not tag or cat is None or not label:
        return False
    tgt = next_target(store, df, tag, cat, label)
    store.data.pop(PENDING_KEY, None)
    if tgt is None:
        store.save_backup()
        return False
    ncat, nlabel = _py(tgt[0]), tgt[1]
    store.data["test_live_tag"] = tag
    store.data["test_live_cat"] = ncat
    store.data["test_live_label"] = nlabel
    store.data["live_auto_ts"] = time.time()   # Zeitpunkt des Wechsels (Schutz vor veralteten Haken in Admin-Seiten)
    if store.data.get("bis_follow"):
        store.data["bis_public_tag"] = tag
        store.data["bis_public_cat"] = ncat
    store.save_backup()
    return True


def process(store):
    """Von allen Live-Seiten bei jedem Lauf aufgerufen: fuehrt einen faelligen Wechsel aus."""
    p = get_pending(store)
    if not p:
        return
    if not get_cfg(store)["enabled"]:
        cancel(store)
        return
    if _live(store) != (p.get("tag"), p.get("cat"), p.get("label")):
        cancel(store)      # Admin hat inzwischen von Hand etwas anderes freigegeben
        return
    if time.time() < float(p.get("due", 0)):
        return
    jump_to_next(store)


def single_nominee(df, tag, cat, label):
    """Ist in dieser Klasse genau EINE Katze nominiert, ist sie automatisch die Gewinnerin
    (die Richter haetten keine Wahl). Gibt deren Katalognummer (Text) oder None zurueck."""
    d = with_selection(df, tag)
    d = d[(d["SELECTION"] == "X") & (d["KATEGORIE"] == cat)]
    spec = {l: (kl, g) for l, kl, g in CLASS_ORDER}
    if label == NO_CLASS_LABEL:
        kl, g = None, None
    elif label in spec:
        kl, g = spec[label]
    else:
        return None
    d = d[class_mask(d, kl, g)]
    nrs = d["KAT_STR"].astype(str).unique().tolist()
    return nrs[0] if len(nrs) == 1 else None
