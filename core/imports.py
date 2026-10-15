# -*- coding: utf-8 -*-
"""PDF-Import: abwesende und nominierte Katzen.
Die Listen liegen im Store unter eigenen Schluesseln (PROTECTED_KEYS) und
ueberleben den Admin-Reset ("ALLE DATEN ZURUECKSETZEN"), ausser man waehlt es ausdruecklich."""
import re
from io import BytesIO

ABSENT_KEY = "import_absent"   # {"TAG 1": {"99": {"date": "10.10.2026", "src": "pdf"|"manuell"}}, ...}
NOM_KEY = "import_nom"         # {"TAG 1": {"nrs": ["1","5"], "date": "10.10.2026"}}
GATE_KEY = "cat_gate"         # {"Samstag": {"1": ["2","4"], ...}}  = gesperrte Kategorien je Runde
SHOWDAY_KEY = "show_day"      # "Samstag" | "Sonntag"
HANDY_LOCK_KEY = "handy_locked"  # Notausknopf: Handy-Ansicht fuer Aussteller gesperrt
PROTECTED_KEYS = (ABSENT_KEY, NOM_KEY, GATE_KEY, SHOWDAY_KEY, "bis_order", "bis_start", HANDY_LOCK_KEY, "bis_auto", "help_texts")


def _now():
    """Zeitpunkt des Imports (Schweizer Zeit) als Text 'TT.MM.JJJJ HH:MM'."""
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Zurich")).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d.%m.%Y %H:%M")


def last_import(store, n):
    """(abwesend_zeit, nominiert_zeit, abwesend_anzahl, nominiert_anzahl) fuer Runde n.
    Zeit = letzter Import ('TT.MM.JJJJ HH:MM'), '' = Liste vorhanden, aber ohne Zeitangabe, None = keine Liste."""
    ab = get_absent(store, n)
    ab_pdf = [m for m in ab.values() if isinstance(m, dict) and m.get("src") == "pdf"]
    ab_t = None
    if ab_pdf:
        ats = [m.get("at") for m in ab_pdf if m.get("at")]
        ab_t = max(ats, key=_sort_key) if ats else ""
    nom = get_nom(store).get(f"TAG {int(n)}")
    nom_t = None
    if isinstance(nom, dict) and nom.get("nrs") is not None:
        nom_t = nom.get("at") or ""
    return ab_t, nom_t, len(ab_pdf), (len(nom.get("nrs", [])) if isinstance(nom, dict) else 0)


def _sort_key(t):
    try:
        from datetime import datetime
        return datetime.strptime(t, "%d.%m.%Y %H:%M")
    except Exception:
        from datetime import datetime
        return datetime.min


# ---------------------------------------------------------------- PDF lesen
def parse_pdf_numbers(file_bytes):
    """Liest ein PDF und liefert (nummern, datum, ignorierte_zeilen).
    Nummer = Zeile, die nur aus einer Zahl besteht. Datum = erstes TT.MM.JJJJ im Text."""
    from pypdf import PdfReader  # in requirements.txt: pypdf
    reader = PdfReader(BytesIO(file_bytes))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    return parse_text_numbers(text)


def parse_text_numbers(text):
    nums, ignored, seen = [], [], set()
    m = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
    date = m.group(1) if m else None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        # Eine Zeile aus nur Zahlen (eine oder mehrere, z. B. bei mehrspaltigen Listen) = Katalognummern
        if re.fullmatch(r"\d{1,4}(?:\s+\d{1,4})*", s):
            for tok in s.split():
                n = str(int(tok))
                if n not in seen:
                    seen.add(n)
                    nums.append(n)
        else:
            ignored.append(s)
    return nums, date, ignored


# ---------------------------------------------------------------- Abwesende (pro Runde)
def _absent_all(store):
    """{'TAG 1': {nr: meta}, ...}. Eine alte, flache Liste {nr: meta} gilt fuer alle Runden."""
    d = store.data.get(ABSENT_KEY)
    if not isinstance(d, dict) or not d:
        return {}
    if all(str(k).startswith("TAG ") for k in d):
        return {k: dict(v) for k, v in d.items() if isinstance(v, dict)}
    return {f"TAG {n}": dict(d) for n in (1, 2, 3)}


def get_absent(store, n):
    return _absent_all(store).get(f"TAG {int(n)}", {})


def is_absent(store, nr, n):
    return str(nr) in get_absent(store, n)


def add_absent(store, nrs, n, date=None, src="pdf", replace_pdf=False):
    allr = _absent_all(store)
    tag = f"TAG {int(n)}"
    cur = dict(allr.get(tag, {}))
    if replace_pdf:
        cur = {k: v for k, v in cur.items() if v.get("src") != "pdf"}
    for x in nrs:
        cur[str(x)] = {"date": date or "", "src": src, "at": _now()}
    allr[tag] = cur
    store.data[ABSENT_KEY] = allr
    store.save_backup()


def release_absent(store, nr, n):
    allr = _absent_all(store)
    tag = f"TAG {int(n)}"
    cur = dict(allr.get(tag, {}))
    cur.pop(str(nr), None)
    allr[tag] = cur
    store.data[ABSENT_KEY] = allr
    store.save_backup()


# ---------------------------------------------------------------- Nominierte
def get_nom(store):
    d = store.data.get(NOM_KEY)
    return d if isinstance(d, dict) else {}


def set_nom(store, tag, nrs, date=None):
    cur = dict(get_nom(store))
    cur[tag] = {"nrs": [str(n) for n in nrs], "date": date or "", "at": _now()}
    store.data[NOM_KEY] = cur
    store.save_backup()


def clear_nom(store, tag):
    cur = dict(get_nom(store))
    cur.pop(tag, None)
    store.data[NOM_KEY] = cur
    store.save_backup()


def apply_nom_overrides(df, store):
    """Ersetzt SELECTION n durch die importierte Nominierungsliste (falls vorhanden)."""
    noms = get_nom(store)
    if not noms or df is None or "KAT_STR" not in df.columns:
        return df
    out = df.copy()
    for tag, info in noms.items():
        m = re.search(r"\d+", str(tag))
        if not m:
            continue
        col = f"SELECTION {m.group()}"
        nrs = set(info.get("nrs", []))
        out[col] = out["KAT_STR"].apply(lambda x: "X" if str(x) in nrs else "-")
    return out


def reset_keep_protected(store, keep=True):
    """Leert den Store, behaelt aber die Importlisten (wenn keep=True)."""
    saved = {k: store.data[k] for k in PROTECTED_KEYS if k in store.data} if keep else {}
    store.data = dict(saved)
