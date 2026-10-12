# -*- coding: utf-8 -*-
"""Ansicht: Excel_Upload"""
import streamlit as st
from core.config import EXCEL_FILE
from core.ui import display_header_with_logo


def render():
    # Einheitlicher Header-Stil deiner App
    display_header_with_logo("⚙️ Excel-Upload")
    st.markdown('<div class="main-title">⚙️ Admin: Excel-Katalog austauschen</div>', unsafe_allow_html=True)
    
    st.write(f"Hier kannst du die zentrale `{EXCEL_FILE}` Datei ersetzen. Die Datei wird direkt in das Repository hochgeladen.")
    st.info("💡 **Hinweis:** Die Spaltenstruktur muss exakt mit der ursprünglichen Datei übereinstimmen.")
    
    uploaded_file = st.file_uploader("Neue Excel-Datei auswählen:", type=["xlsx"], key="excel_uploader_file")
    
    if uploaded_file is not None:
        # Hier sitzen die Buttons direkt unter dem Upload-Feld
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            if st.button("🚀 JETZT SPEICHERN", key="btn_execute_github_upload", type="primary", use_container_width=True):
                with st.spinner("Überprüfe Datei und übertrage zu GitHub..."):
                    try:
                        import base64
                        import requests
                        import pandas as pd
                        
                        # 1. Spalten-Validierung vor dem Upload
                        df_new = pd.read_excel(uploaded_file)
                        try:
                            df_current = pd.read_excel(EXCEL_FILE)
                            current_columns = list(df_current.columns)
                            new_columns = list(df_new.columns)
                            missing_cols = [col for col in current_columns if col not in new_columns]
                        except Exception:
                            # Falls lokal keine Excel-Datei liegt, Check überspringen
                            missing_cols = []

                        if missing_cols:
                            st.error(f"❌ **Validierungsfehler!** Der neuen Datei fehlen folgende Spalten der Originalstruktur: `{missing_cols}`. Upload abgebrochen.")
                        elif df_new.empty:
                            st.error("❌ **Validierungsfehler!** Die hochgeladene Datei enthält keine Datenzeilen.")
                        else:
                            # 2. Upload zu GitHub, wenn Validierung erfolgreich
                            file_bytes = uploaded_file.getvalue()
                            token = st.secrets["GITHUB_TOKEN"]
                            repo = st.secrets["GITHUB_REPO"]
                            filename = EXCEL_FILE
                            branch = "main"
                            
                            url = f"https://api.github.com/repos/{repo}/contents/{filename}"
                            headers = {"Authorization": f"token {token}"}

                            # SHA-Hash für das Überschreiben abfragen
                            res = requests.get(url, headers=headers)
                            sha = res.json().get("sha") if res.status_code == 200 else None

                            content_base64 = base64.b64encode(file_bytes).decode("utf-8")
                            
                            payload = {
                                "message": "Katalog-Update via Streamlit Admin Panel",
                                "content": content_base64,
                                "branch": branch
                            }
                            if sha:
                                payload["sha"] = sha

                            response = requests.put(url, json=payload, headers=headers)
                            
                            if response.status_code in [200, 201]:
                                st.success(f"✅ **Erfolgreich!** `{df_new.shape[0]}` Zeilen auf GitHub überschrieben.")
                                st.cache_data.clear()
                                import time
                                time.sleep(1.5)
                                st.session_state.view = "Home"
                                st.rerun()
                            else:
                                st.error(f"GitHub API Fehler ({response.status_code}): {response.text}")
                    except Exception as e:
                        st.error(f"Fehler beim Verarbeiten der Datei: {e}")
        
        with col_cancel:
            if st.button("🚫 Abbrechen", key="btn_abort_upload", use_container_width=True):
                st.session_state.view = "Home"
                st.rerun()
                    
    st.divider()
    
    # Globaler Zurück-Button am Seitenende
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_upload_panel", use_container_width=True):
        st.session_state.view = "Home"
        st.rerun()

# ==============================================================================
# NEUER MENÜPUNKT: 📝 Excel Direct Editor
# ==============================================================================
