# -*- coding: utf-8 -*-
"""PDF-Import: abwesende und nominierte Katzen.
Die Listen liegen im Store unter eigenen Schluesseln (PROTECTED_KEYS) und
ueberleben den Admin-Reset ("ALLE DATEN ZURUECKSETZEN"), ausser man waehlt es ausdruecklich."""
import re
from io import BytesIO

ABSENT_KEY = "import_absent"   # {"99": {"date": "10.10.2026", "src": "pdf"|"manuell"}}
NOM_KEY = "import_nom"         # {"TAG 1": {"nrs": ["1","5"], "date": "10.10.2026"}}
GATE_KEY = "cat_gate"         # {"Samstag": {"1": ["2","4"], ...}}  = gesperrte Kategorien je Runde
SHOWDAY_KEY = "show_day"      # "Samstag" | "Sonntag"
PROTECTED_KEYS = (ABSENT_KEY, NOM_KEY, GATE_KEY, SHOWDAY_KEY)


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
        if re.fullmatch(r"\d{1,4}", s):
            n = str(int(s))
            if n not in seen:
                seen.add(n)
                nums.append(n)
        else:
            ignored.append(s)
    return nums, date, ignored


# ---------------------------------------------------------------- Abwesende
def get_absent(store):
    d = store.data.get(ABSENT_KEY)
    return d if isinstance(d, dict) else {}


def is_absent(store, nr):
    return str(nr) in get_absent(store)


def add_absent(store, nrs, date=None, src="pdf", replace_pdf=False):
    cur = dict(get_absent(store))
    if replace_pdf:
        cur = {k: v for k, v in cur.items() if v.get("src") != "pdf"}
    for n in nrs:
        cur[str(n)] = {"date": date or "", "src": src}
    store.data[ABSENT_KEY] = cur
    store.save_backup()


def release_absent(store, nr):
    cur = dict(get_absent(store))
    cur.pop(str(nr), None)
    store.data[ABSENT_KEY] = cur
    store.save_backup()


# ---------------------------------------------------------------- Nominierte
def get_nom(store):
    d = store.data.get(NOM_KEY)
    return d if isinstance(d, dict) else {}


def set_nom(store, tag, nrs, date=None):
    cur = dict(get_nom(store))
    cur[tag] = {"nrs": [str(n) for n in nrs], "date": date or ""}
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
