# -*- coding: utf-8 -*-
"""
Projekt: Cat Show App der KECB Katzenausstellung
Copyright (c) 2026 Brigitte Portner
Alle Rechte vorbehalten

Einstiegspunkt. Die eigentlichen Seiten liegen in views/, gemeinsame Teile in core/.
"""
import importlib
import streamlit as st

from core.config import SHOW_YEAR, LOGO_URL, ACCESS_MAP

# set_page_config muss der erste Streamlit-Befehl sein
st.set_page_config(layout="wide", page_title=f"KECB Burgdorf {SHOW_YEAR}", page_icon="🐾")

from core.styles import inject_global_css
from core.store import get_store
from core.ui import logout, set_view

inject_global_css()
store = get_store()

VIEWS = {
    "Login": "views.login",
    "Home": "views.home",
    "BIS_Public": "views.bis_public",
    "Dashboard": "views.dashboard",
    "Live_Handy": "views.live_handy",
    "BIS_Ablauf": "views.bis_ablauf",
    "Steward_Panel": "views.steward_panel",
    "QR_Codes_Gen": "views.qr_codes_gen",
    "Nominated_Cats": "views.nominated_cats",
    "Admin_Panel": "views.admin_panel",
    "Check": "views.check",
    "Rundenmanager": "views.rundenmanager",
    "Judge_List": "views.judge_list",
    "Judge List": "views.judge_list",
    "Nomination_Labels": "views.nomination_labels",
    "Nomination Labels": "views.nomination_labels",
    "Live_Voting": "views.live_voting",
    "Live_Admin": "views.live_admin",
    "Moderator": "views.moderator",
    "Excel_Upload": "views.excel_upload",
    "Excel_Edit": "views.excel_edit",
    "Alters_Check": "views.alters_check",
    "Import_PDF": "views.import_pdf",
}

# --- SESSION STATE & URL PARAMETER ---
q_params = st.query_params

# 1. Prüfen, ob Zugangsdaten direkt in der URL stecken (Erzwingt das Login bei jedem Rerun)
from core.access import auth_ok
if "auth" in q_params and q_params["auth"] == "true" and auth_ok(q_params):
    st.session_state.authenticated = True
    st.session_state.user_role = q_params.get("role", "Public")
    
       # Falls eine bestimmte Ansicht in der URL steht, diese erzwingen
    # (nur EINMAL pro Link anwenden, sonst springt jeder Knopf mit set_view() wieder auf die URL-Ansicht zurueck)
    _sig = (str(q_params.get("view", "")).lower(), str(q_params.get("role", "")))
    if "view" in q_params and st.session_state.get("url_view_sig") != _sig:
        st.session_state["url_view_sig"] = _sig
        v_param = q_params["view"].lower()
        if v_param == "steward": st.session_state.view = "Steward_Panel"
       # elif v_param == "richter": st.session_state.view = "Judge_Voting"
        elif v_param == "admin": st.session_state.view = "Home"
        elif v_param == "rundenmanager": st.session_state.view = "Rundenmanager"
        elif v_param == "excel-upload": st.session_state.view = "Excel_Upload"
        elif v_param == "excel-edit": st.session_state.view = "Excel_Edit"
        elif v_param == "import-pdf": st.session_state.view = "Import_PDF"

       # elif v_param == "bis-admin": st.session_state.view = "BIS_Admin_Control"
       # elif v_param == "qr": st.session_state.view = "QR_Codes"
        elif v_param == "qr-gen": st.session_state.view = "QR_Codes_Gen"
        elif v_param == "nominated": st.session_state.view = "Nominated_Cats"
		
        # --- NEU: URL-PARAMETER FÜR DIE BEIDEN TEST-SEITEN ---
        elif v_param == "live-admin": st.session_state.view = "Live_Admin"
        elif v_param == "live-voting": st.session_state.view = "Live_Voting"




# 2. Standard-Fallbacks, falls nichts in der URL steht
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "Public"
if "view" not in st.session_state:
    st.session_state.view = "Dashboard"

# Falls man manuell über das Menü navigiert, ohne URL-Parameter zu verlieren
if "view" in q_params and not st.session_state.authenticated:
    v_param = q_params["view"].lower()
    if v_param == "katzenaufruf": st.session_state.view = "Dashboard"
    elif v_param == "live": st.session_state.view = "Live_Handy"
    elif v_param == "bis": st.session_state.view = "BIS_Public"
    elif v_param in ["admin", "steward", "richter", "bis-admin"]:
        st.session_state.view = "Login"
        st.session_state.target_role = v_param
        

# NEU: Richter-Parameter aus der URL sichern, falls übergeben
if "judge" in q_params: 
    st.session_state.url_judge = q_params["judge"]
elif "url_judge" not in st.session_state: 
    st.session_state.url_judge = "--"

# --- HANDY-MODUS FÜR AUSSTELLER (nur Live Handy, sonst nichts) ---
# Aufruf: <App-Adresse>?view=live  (ohne Login). Kein Menü, keine Seitenleiste,
# keine Streamlit-Leisten: es gibt nichts, wo man sich verklicken könnte.
if (str(q_params.get("view", "")).lower() in ("live", "handy")
        and not st.session_state.authenticated):
    st.session_state.view = "Live_Handy"
    st.markdown("""
        <style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"], [data-testid="stSidebarNav"],
        [data-testid="stToolbar"], [data-testid="stHeader"], header,
        [data-testid="stDecoration"], [data-testid="stStatusWidget"],
        .stAppDeployButton, #MainMenu, footer,
        [class*="viewerBadge"], [class*="_profileContainer"] { display: none !important; }
        .block-container { padding-top: 1rem !important; }
        </style>
    """, unsafe_allow_html=True)
    importlib.import_module(VIEWS["Live_Handy"]).render()
    st.stop()

# --- NAVIGATION & ZUGRIFF ---
st.markdown("""
        <style>
        div.stButton > button {
            background-color: #ffffff !important;
            color: #1a4a9e !important;
            border: 2px solid #1a4a9e !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            width: 100% !important;
            display: block !important;
            transition: all 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #1a4a9e !important;
            color: #ffffff !important;
        }
        .login-container {
            border: 2px solid #1a4a9e !important;
            border-radius: 15px;
            padding: 20px;
            background-color: transparent;
        }
        </style>
    """, unsafe_allow_html=True)
    
available_views = ACCESS_MAP.get(st.session_state.user_role, ["Dashboard"])
st.sidebar.image(LOGO_URL, width=150)

# HIER WURDE format_func HINZUGEFÜGT: Tauscht bei der Anzeige die Unterstriche gegen Leerzeichen
st.session_state.view = st.sidebar.radio(
    "Menü:", 
    available_views, 
    index=available_views.index(st.session_state.view) if st.session_state.view in available_views else 0,
    format_func=lambda x: x.replace("_", " ")
)
##if st.session_state.view != "BIS_Public":
   # store.active_overlay = None	

if store.last_error:
    st.sidebar.error(f"⚠️ Datenbank-Problem – Stimmen evtl. nicht gesichert!\n\n{store.last_error}")

if st.session_state.authenticated:
    if st.sidebar.button("Abmelden"): logout()
elif st.session_state.view != "Login":

    if st.sidebar.button("🔒 Interner Login"): set_view("Login")

# --- Copyright Bereich ---
st.sidebar.markdown("---") # Trennlinie für saubere Optik
st.sidebar.markdown(
    """
    <div style="font-size: 0.8em; color: gray; text-align: center;">
        © 2026 Brigitte Portner<br>
        Alle Rechte vorbehalten.
    </div>
    """, 
    unsafe_allow_html=True
)

# --- ANSICHT ANZEIGEN ---
_module = VIEWS.get(st.session_state.view)
if _module:
    importlib.import_module(_module).render()
