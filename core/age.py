# -*- coding: utf-8 -*-
"""Alters-Check: Mindestalter der Katzen am Ausstellungstag (Standard: 4 Monate)."""
import calendar
from datetime import date, datetime

import pandas as pd


def parse_birth(x):
    """Geburtsdatum aus Excel (Text 'TT.MM.JJJJ', Timestamp oder date) -> date oder None."""
    if x is None:
        return None
    if isinstance(x, pd.Timestamp):
        return None if pd.isna(x) else x.date()
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    t = str(x).strip()
    if not t or t.lower() in ("nan", "nat", "-", "none"):
        return None
    d = pd.to_datetime(t, dayfirst=True, errors="coerce")
    return None if pd.isna(d) else d.date()


def add_months(d, n):
    """d + n Monate; faellt der Tag nicht in den Zielmonat (z. B. 31.), gilt der letzte Tag des Monats."""
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def old_enough(birth, on_day, months=4):
    return birth is not None and on_day >= add_months(birth, months)


def age_text(birth, on_day):
    """Alter am Stichtag als 'x Mon. y Tage'."""
    if birth is None:
        return "–"
    if on_day < birth:
        return "noch nicht geboren"
    m = (on_day.year - birth.year) * 12 + on_day.month - birth.month
    if add_months(birth, m) > on_day:
        m -= 1
    rest = (on_day - add_months(birth, m)).days
    return f"{m} Mon. {rest} T."


def check(df, day1, day2, months=4):
    """Liefert DataFrame mit Alter an beiden Tagen und Status je Katze."""
    rows = []
    for _, r in df.iterrows():
        b = parse_birth(r.get("GEBURTSDATUM"))
        ok1, ok2 = old_enough(b, day1, months), old_enough(b, day2, months)
        if b is None:
            status = "❓ Geburtsdatum fehlt/ungültig"
        elif not ok1 and not ok2:
            status = "❌ an beiden Tagen zu jung"
        elif not ok1:
            status = "⚠️ nur am 2. Tag alt genug"
        else:
            status = "✅ OK"
        fehlt = ""
        if b is not None and not ok2:
            fehlt = f"ab {add_months(b, months).strftime('%d.%m.%Y')}"
        rows.append({
            "Nr.": str(r.get("KAT_STR", "")),
            "Name": str(r.get("NAME", "")),
            "Besitzer": f"{r.get('BESITZER VORNAME', '')} {r.get('BESITZER NACHNAME', '')}".strip(),
            "Klasse": str(r.get("AUSSTELLUNGSKLASSE", "")),
            "Geboren": b.strftime("%d.%m.%Y") if b else "–",
            f"Alter {day1.strftime('%d.%m.')}": age_text(b, day1),
            f"Alter {day2.strftime('%d.%m.')}": age_text(b, day2),
            "Zugelassen": fehlt or ("ab Tag 1" if status == "✅ OK" else ("ab Tag 2" if ok2 else "–")),
            "Status": status,
        })
    out = pd.DataFrame(rows)
    out["_n"] = out["Nr."].apply(lambda x: int(x) if str(x).isdigit() else 99999)
    return out.sort_values("_n").drop(columns="_n").reset_index(drop=True)
