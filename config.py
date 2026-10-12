# -*- coding: utf-8 -*-
"""Zentrale Einstellungen. Hier aendert man Jahr, Excel-Name und App-Adresse."""

SHOW_YEAR = 2027
EXCEL_FILE = f"{SHOW_YEAR}.xlsx"          # Name der Excel-Datei im Repository

# Adresse der App (wird in den QR-Codes verwendet).
# ACHTUNG: zeigt noch auf die 2026-App. Sobald die neue App eine neue Adresse hat, hier anpassen.
BASE_URL = "https://kecb2026.streamlit.app/"

LOGO_URL = "logo_kecb.png"

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
    "Public": ["Dashboard", "BIS_Public", "Login"],
    "Richter": ["Live_Voting", "Dashboard", "BIS_Public"],
    "Steward": ["Steward_Panel", "Dashboard", "BIS_Public"],
    "Admin": ["Home", "Rundenmanager", "Dashboard", "BIS_Public", "Moderator", "Steward_Panel", "Live_Admin", "Live_Voting",
              "QR_Codes_Gen", "Nominated_Cats", "Judge_List", "Nomination_Labels", "Admin_Panel",
              "Excel_Upload", "Excel_Edit"],
}

# ---------------------------------------------------------------------------
# RUNDEN (2027): Gelb / Gruen / Rot  =  Excel-Spalten TAG 1 / TAG 2 / TAG 3
# (RICHTER TAG n und SELECTION n gehoeren zur selben Nummer n)
# ---------------------------------------------------------------------------
ROUNDS = {
    1: {"name": "Gelb", "emoji": "🟡", "color": "#f2b600", "on_color": "#1b1b1b", "tint": "#fff6cc"},
    2: {"name": "Grün", "emoji": "🟢", "color": "#2e9e4f", "on_color": "#ffffff", "tint": "#dff5e5"},
    3: {"name": "Rot",  "emoji": "🔴", "color": "#d93a3a", "on_color": "#ffffff", "tint": "#fde1e1"},
}

# Showtypen: welche Runden gibt es? (Vorlagen, im Rundenmanager umschaltbar)
SHOWTYPES = {
    "2027 – 3 Runden (Gelb, Grün, Rot)": [1, 2, 3],
    "2026 – 1 Runde pro Tag (2 Runden)": [1, 2],
    "2028 – 2 Runden (nach Kategorien)": [1, 2],
}
DEFAULT_SHOWTYPE = "2027 – 3 Runden (Gelb, Grün, Rot)"
