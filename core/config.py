# -*- coding: utf-8 -*-
"""Zentrale Einstellungen. Hier aendert man Jahr, Excel-Name und App-Adresse."""

SHOW_YEAR = 2027
EXCEL_FILE = f"{SHOW_YEAR}.xlsx"          # Name der Excel-Datei im Repository

# Adresse der App (wird in den QR-Codes verwendet).
BASE_URL = "https://kecb2027.streamlit.app/"

LOGO_URL = "logo_kecb.png"

# Copyright-Hinweis am Ende der Home-Seite (hier anpassen)
COPYRIGHT_TEXT = f"© {SHOW_YEAR} KECB Burgdorf · Alle Rechte vorbehalten"

# Ausstellungstage (fuer Alters-Check) und Mindestalter in Monaten
from datetime import date as _date
SHOW_DATES = (_date(2027, 10, 9), _date(2027, 10, 10))
MIN_AGE_MONTHS = 4

FIFe_KLASSEN_NAMEN = {
    1: "1 - PH",
    2: "2 - PH",
    3: "3 - CACS",
    4: "4 - CAPS",
    5: "5 - CAGCIB",
    6: "6 - CAGCIP",
    7: "7 - CACIB",
    8: "8 - CACIP",
    9: "9 - CAC",
    10: "10 - CAP",
    11: "11 - CACJ",
    12: "12 - CACC"
}

ACCESS_MAP = {
    "Public": ["Dashboard", "Live_Handy", "BIS_Public", "BIS_Ablauf", "Login"],
    "Richter": ["Live_Voting", "Dashboard", "Live_Handy", "BIS_Public", "BIS_Ablauf"],
    "Steward": ["Steward_Panel", "Dashboard", "BIS_Public", "BIS_Ablauf"],
    "Admin": ["Home", "Rundenmanager", "Dashboard", "Steward_Panel", "Live_Voting",
              "BIS_Public", "BIS_Ablauf", "Live_Admin", "Moderator", "Live_Handy",
              "QR_Codes_Gen", "Nominated_Cats", "Nomination_Labels", "Judge_List",
              "Import_PDF", "Excel_Upload", "Excel_Edit", "Alters_Check", "Admin_Panel", "Check", "Hilfe"],
}

# ---------------------------------------------------------------------------
# RUNDEN (2027): Gelb / Gruen / Rot  =  Excel-Spalten TAG 1 / TAG 2 / TAG 3
# (RICHTER TAG n und SELECTION n gehoeren zur selben Nummer n)
# ---------------------------------------------------------------------------
ROUNDS = {
    1: {"name": "Gelb", "emoji": "🟡", "color": "#f2b600", "on_color": "#1b1b1b", "tint": "#fffdf2"},
    2: {"name": "Grün", "emoji": "🟢", "color": "#2e9e4f", "on_color": "#ffffff", "tint": "#f7fff4"},
    3: {"name": "Rot",  "emoji": "🔴", "color": "#d93a3a", "on_color": "#ffffff", "tint": "#fff5f5"},
}

# Showtypen: welche Runden gibt es? (Vorlagen, im Rundenmanager umschaltbar)
SHOWTYPES = {
    "2027 – 3 Runden (Gelb, Grün, Rot)": [1, 2, 3],
    "2026 – 1 Runde pro Tag (2 Runden)": [1, 2],
    "2028 – 2 Runden (nach Kategorien)": [1, 2],
}
DEFAULT_SHOWTYPE = "2027 – 3 Runden (Gelb, Grün, Rot)"

# Kategorien ohne Klassen (z. B. Hauskatzen): BIS Public zeigt nur eine Zeile "Nominierte Katzen"
NO_CLASS_CATEGORIES = ("5",)
NO_CLASS_LABEL = "Nominierte Katzen"


# Ballone beim Gewinner-Overlay (BIS Public): "streamlit" = eingebaute Ballone, "eigene" = selbst gebaute (liegen sicher ueber dem Overlay)
BALLOON_STYLE = "streamlit"
# Vorlauf: so viele Sekunden laufen nur die Streamlit-Ballone, danach erscheint das Gewinner-Overlay
BALLOON_LEAD_SECONDS = 3
# Text waehrend des Vorlaufs (leer lassen = nur Ballone auf leerer Seite)
BALLOON_LEAD_TEXT = "Und der Gewinner ist …"
