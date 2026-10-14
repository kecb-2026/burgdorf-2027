# -*- coding: utf-8 -*-
"""Ansicht: Login"""
import streamlit as st
from core.config import LOGO_URL
from core.ui import set_view
from core.access import password_for


def render():
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

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.image(LOGO_URL, width=150)
    st.markdown("<h2 style='text-align:center; color:#1a4a9e; text-transform: uppercase; font-size: 20px;'>Interner Bereich</h2>", unsafe_allow_html=True)
    
    role_map = {"admin": "Admin", "steward": "Steward", "richter": "Richter", "bis-admin": "Admin"}
    target = st.session_state.get("target_role", "Richter")
    role_list = ["Admin", "Steward", "Richter"]
    def_idx = role_list.index(role_map.get(target, "Richter"))

    role_input = st.selectbox("Rolle wählen:", role_list, index=def_idx)
    password = st.text_input("Passwort:", type="password")
    
    if st.button("Anmelden"):
        if role_input == "Admin" and password == password_for("Admin"):
            st.session_state.user_role, st.session_state.authenticated = "Admin", True
            st.query_params.update(auth="true", role="Admin") 
            set_view("Home")
        elif role_input == "Steward" and password == password_for("Steward"):
            st.session_state.user_role, st.session_state.authenticated = "Steward", True
            st.query_params.update(auth="true", role="Steward") 
            set_view("Steward_Panel")
        elif role_input == "Richter" and password == password_for("Richter"):
            st.session_state.user_role, st.session_state.authenticated = "Richter", True
            st.query_params.update(auth="true", role="Richter") 
            set_view("Judge_Voting")
        else:
            st.error("Passwort ungültig.")
    
    if st.button("Abbrechen"): set_view("Dashboard")
    st.markdown("</div>", unsafe_allow_html=True)


# HOME (ADMIN NUR)
