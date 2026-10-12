# -*- coding: utf-8 -*-
"""Ansicht: Home"""
import streamlit as st
from core.config import SHOW_YEAR
from core.rounds import default_round, round_label
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    display_header_with_logo(f"🐾 KECB Burgdorf {SHOW_YEAR}")
    st.markdown('<div class="home-buttons">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📢 LIVE-DASHBOARD"):
            st.query_params.update({"view": "katzenaufruf"})
            set_view("Dashboard")
            st.rerun()
        if st.button("🏆 BEST IN SHOW (PUBLIC)"):
            st.query_params.update({"view": "bis"})
            set_view("BIS_Public")
            st.rerun()
        #if st.button("🗳️ RICHTER-VOTING"):
            #st.query_params.update({"view": "richter", "auth": "true", "role": "Richter"})
            #set_view("Judge_Voting")
            #st.rerun()
			        # --- NEU: BUTTON FÜR DAS RICHTER-TEST-VOTING ---
        if st.button("🧪 LIVE-VOTING (RICHTER)"):
            st.query_params.update({"view": "live-voting", "auth": "true", "role": "Admin"})
            set_view("Live_Voting")
            st.rerun()
    with col2:
        if st.button("📝 STEWARD-PULT"):
            st.query_params.update({"view": "steward", "auth": "true", "role": "Steward"})
            set_view("Steward_Panel")
            st.rerun()
        #if st.button("👨‍⚖️ BIS ADMIN / CONTROL"):
            #st.query_params.update({"view": "bis-admin", "auth": "true", "role": "Admin"})
            #set_view("BIS_Admin_Control")
           # st.rerun()
		 # --- NEU: BUTTON FÜR DEN LIVE-ADMIN-TEST ---
        if st.button("🎛️ LIVE-ADMIN CONTROL"):
            st.query_params.update({"view": "live-admin", "auth": "true", "role": "Admin"})
            set_view("Live_Admin")
            st.rerun()
        if st.button("⚙️ ADMIN-KONSOLE (RESET)"):
            st.query_params.update({"view": "admin", "auth": "true", "role": "Admin"})
            set_view("Admin_Panel")
            st.rerun()
        if st.button("⚙️ EXCEL-UPLOAD"):
            st.query_params.update({"view": "excel-upload", "auth": "true", "role": "Admin"})
            set_view("Excel_Upload")
            st.rerun()
        if st.button("📥 PDF-IMPORT (ABWESENDE / NOMINIERTE)"):
            st.query_params.update({"view": "import-pdf", "auth": "true", "role": "Admin"})
            set_view("Import_PDF")
            st.rerun()
        if st.button("📝 EXCEL LIVE-EDITOR"):
            st.query_params.update({"view": "excel-edit", "auth": "true", "role": "Admin"})
            set_view("Excel_Edit")
            st.rerun()

            # NEU: Der Button für die QR-Zentrale direkt im Admin-Menü
        #if st.button("📱 QR-CODE ZENTRALE"):
            #st.query_params.update({"view": "qr", "auth": "true", "role": "Admin"})
            #set_view("QR_Codes")
            #st.rerun()
	            # NEU: Der Button für die QR-Zentrale direkt im Admin-Menü
        if st.button("📱 QR-CODE GENERATOR"):
            st.query_params.update({"view": "qr-gen", "auth": "true", "role": "Admin"})
            set_view("QR_Codes_Gen")
            st.rerun()
             # NEU: Button für die nominierten Katzen
        if st.button("🐈 NOMINIERTE KATZEN LISTE"):
            st.query_params.update({"view": "nominated", "auth": "true", "role": "Admin"})
            set_view("Nominated_Cats")
            st.rerun()
            # NEU: Button für die Richter Liste
        if st.button("🐈 RICHTER LISTE"):
            st.query_params.update({"view": "judge-list", "auth": "true", "role": "Admin"})
            set_view("Judge_List")
            st.rerun()
        if st.button("🖨️ NOMINATION LABELS DRUCK"):
            st.query_params.update({"view": "nom-labels", "auth": "true", "role": "Admin"})
            set_view("Nomination_Labels")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    st.subheader("⚙️ System-Einstellungen (Admin-Steuerung)")
    
    # 1. Richter-Fixierung
    if "steward_lock" not in st.session_state:
        st.session_state.steward_lock = True
    st.session_state.steward_lock = st.toggle(
        "Richter-Auswahl für Stewards sperren (Lockdown)", 
        value=st.session_state.steward_lock
    )


    st.subheader("⚙️ Runden")
    st.info(f"Standard-Runde: {round_label(default_round(store))}. "
            "Runden und Richter werden im Rundenmanager gesteuert.")
    if st.button("🎛️ RUNDENMANAGER", key="home_to_rundenmanager"):
        st.query_params.update({"view": "rundenmanager", "auth": "true", "role": "Admin"})
        set_view("Rundenmanager")
