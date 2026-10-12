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
    "Admin": ["Home", "Dashboard", "BIS_Public", "Moderator", "Steward_Panel", "Live_Admin", "Live_Voting",
              "QR_Codes_Gen", "Nominated_Cats", "Judge_List", "Nomination_Labels", "Admin_Panel",
              "Excel_Upload", "Excel_Edit"],
}
