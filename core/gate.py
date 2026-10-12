# -*- coding: utf-8 -*-
"""Kategorien-Freigabe (Sperre) je Tag und Runde. Standard: alles freigegeben.
Gespeichert wird nur, was GESPERRT ist. Ueberlebt den Admin-Reset."""
from core.imports import GATE_KEY, SHOWDAY_KEY

DAYS = ("Samstag", "Sonntag")


def cat_key(cat):
    return str(cat).replace(".0", "").strip()


def categories(df):
    """Alle Kategorien aus dem Excel (sortiert, Zahlen zuerst)."""
    vals = {cat_key(c) for c in df["KATEGORIE"].unique() if str(c).strip() not in ("", "nan", "-")}
    return sorted(vals, key=lambda x: (0, int(x)) if x.isdigit() else (1, x))


def get_show_day(store):
    d = store.data.get(SHOWDAY_KEY)
    return d if d in DAYS else DAYS[0]


def set_show_day(store, day):
    store.data[SHOWDAY_KEY] = day if day in DAYS else DAYS[0]
    store.save_backup()


def blocked_cats(store, n, day=None):
    day = day or get_show_day(store)
    gate = store.data.get(GATE_KEY)
    if not isinstance(gate, dict):
        return set()
    return set(gate.get(day, {}).get(str(int(n)), []))


def is_open(store, n, cat, day=None):
    return cat_key(cat) not in blocked_cats(store, n, day)


def set_open(store, day, n, cat, open_):
    gate = store.data.get(GATE_KEY)
    gate = dict(gate) if isinstance(gate, dict) else {}
    dg = dict(gate.get(day, {}))
    cur = set(dg.get(str(int(n)), []))
    (cur.discard if open_ else cur.add)(cat_key(cat))
    dg[str(int(n))] = sorted(cur)
    gate[day] = dg
    store.data[GATE_KEY] = gate
    store.save_backup()


def set_row(store, day, n, cats, open_cats):
    """Eine ganze Runde setzen: nur open_cats sind frei, alle anderen gesperrt."""
    gate = store.data.get(GATE_KEY)
    gate = dict(gate) if isinstance(gate, dict) else {}
    dg = dict(gate.get(day, {}))
    dg[str(int(n))] = sorted(cat_key(c) for c in cats if cat_key(c) not in {cat_key(o) for o in open_cats})
    gate[day] = dg
    store.data[GATE_KEY] = gate
    store.save_backup()
