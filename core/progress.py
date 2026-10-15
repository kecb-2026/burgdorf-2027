# -*- coding: utf-8 -*-
"""Fortschritt: wie viele Katzen hat welcher Richter in welcher Runde noch zu richten?"""
from core.imports import is_absent
from core.rounds import all_judges, judge_cats, judge_round, tag_of, usable_rounds


def _done(store, nr, judge):
    v = store.data.get(f"{nr}|{judge}")
    flags = v.get("flags", {}) if isinstance(v, dict) else {}
    return bool(isinstance(flags, dict) and flags.get("Gerichtet"))


def judge_round_progress(store, df, judge, n):
    """(gerichtet, total) fuer den Richter in Runde n. Abwesende Katzen zaehlen nicht mit. total == 0: keine Katzen."""
    rows = judge_cats(df, judge, n, gated=False)
    if rows.empty:
        return 0, 0
    nrs = {str(x) for x in rows["KAT_STR"].tolist()}
    nrs = {x for x in nrs if not is_absent(store, x, n)}
    return sum(1 for x in nrs if _done(store, x, judge)), len(nrs)


def table(store, df):
    """[(richter, {runde: (done, total)}, aktuelle_runde)] fuer alle Richter."""
    rounds = usable_rounds(store, df)
    out = []
    for j in all_judges(df):
        out.append((j, {n: judge_round_progress(store, df, j, n) for n in rounds}, judge_round(store, j)))
    return rounds, out


def round_summary(store, df, n):
    """(anzahl_richter_aktuell_in_runde, gerichtet, total) ueber alle Richter mit Runde n als aktueller Runde."""
    cnt = d = t = 0
    for j in all_judges(df):
        if judge_round(store, j) == n:
            dn, tt = judge_round_progress(store, df, j, n)
            if tt:
                cnt += 1
            d += dn
            t += tt
    return cnt, d, t
