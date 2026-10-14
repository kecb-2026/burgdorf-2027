# -*- coding: utf-8 -*-
"""Pruefungen der Nominationen (gleiche Regeln wie auf der Seite 'Nominierte Katzen')."""
import pandas as pd

from core.rounds import usable_rounds, round_label


def _show_class(row):
    kl = str(row.get("KLASSE_INTERNAL", row.get("AUSSTELLUNGSKLASSE", row.get("KLASSE", "")))).replace(".0", "")
    g = str(row.get("GESCHLECHT", "")).upper()
    if kl in ("1", "3", "5", "7", "9"):
        return f"Adult {g}"
    if kl in ("2", "4", "6", "8", "10"):
        return f"Neuter {g}"
    if kl == "11":
        return f"Junior 8-12 {g}"
    if kl == "12":
        return f"Kitten 4-8 {g}"
    return "Unbekannt"


def nomination_problems(df, store):
    """Je Runde: {'name', 'n', 'dups', 'overload', 'violation'} (Anzahl Auffaelligkeiten)."""
    out = []
    for n in usable_rounds(store, df):
        col = f"SELECTION {n}"
        rc = f"RICHTER TAG {n}"
        if col not in df.columns:
            continue
        sub = df[df[col].astype(str).str.strip().str.upper() == "X"]
        rows = []
        for _, r in sub.iterrows():
            j = r.get(rc, "")
            j = "-" if (pd.isna(j) or str(j).strip() in ("", "nan")) else str(j).strip()
            rows.append({"nr": str(r.get("KAT_STR", "")), "richter": j, "kat": str(r.get("KATEGORIE", "-")),
                         "sk": _show_class(r)})
        d = pd.DataFrame(rows, columns=["nr", "richter", "kat", "sk"])
        dups = int(d[d.duplicated(subset=["nr"], keep=False)]["nr"].nunique()) if not d.empty else 0
        valid = d[d["richter"] != "-"]
        over = viol = 0
        if not valid.empty:
            load = valid.groupby(["richter", "kat"]).size()
            over = int((load > 8).sum())
            viol = int(valid.groupby(["richter", "kat", "sk"]).filter(lambda x: len(x) > 1)["richter"].nunique())
        out.append({"name": round_label(n, with_emoji=False), "n": n, "noms": len(d),
                    "dups": dups, "overload": over, "violation": viol})
    return out
