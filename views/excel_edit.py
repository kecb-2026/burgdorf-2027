# -*- coding: utf-8 -*-
"""Ansicht: Excel_Edit"""
import pandas as pd
import streamlit as st
from core.config import EXCEL_FILE
from core.data import load_labels
from core.ui import display_header_with_logo, set_view


def render():
    display_header_with_logo("📝 Live Excel-Editor")
    st.write("Bearbeite die Katalogdaten direkt hier in der Tabelle. Drücke nach Änderungen **Enter** und klicke anschließend auf Speichern.")
    
    df_loaded = load_labels()
    
    if df_loaded is not None:
        EXACT_ORIGINAL_COLS = [
            'SELECTION 1', 'SELECTION 2', 'KATALOG-NR', 'CHIP-NUMMER', 'STAMMBUCH-NUMMER',
            'NAME', 'GEBURTSDATUM', 'GESCHLECHT', 'KATEGORIE', 'RASSE', 'FARBE',
            'FARBGRUPPE', 'KASTRIERT', 'AUSSTELLUNGSKLASSE', 'TAG 1', 'TAG 2',
            'BESITZER NACHNAME', 'BESITZER VORNAME', 'BESITZER ADRESSE 1', 'BESITZER LAND',
            'BESITZER PLZ', 'BESITZER ORT', 'RICHTER TAG 1', 'RICHTER TAG 2'
        ]

        valid_cols = [col for col in EXACT_ORIGINAL_COLS if col in df_loaded.columns]
        df_current = df_loaded[valid_cols].copy()

        # 1. Filter für Übersicht im Editor
        st.markdown("### 🔍 Daten filtern (optional)")
        c1, c2 = st.columns(2)
        with c1:
            kat_filter = st.selectbox("Nach Kategorie filtern:", ["Alle"] + sorted([str(k) for k in df_current['KATEGORIE'].unique() if k != "-"]))
        with c2:
            r_opt = ["Alle"] + sorted([str(r) for r in df_current['RICHTER TAG 1'].unique() if str(r) not in ["-", "nan"]])
            richter_filter = st.selectbox("Nach Richter (Tag 1) filtern:", r_opt)

        df_to_edit = df_current.copy()
        if kat_filter != "Alle":
            df_to_edit = df_to_edit[df_to_edit['KATEGORIE'].astype(str) == kat_filter]
        if richter_filter != "Alle":
            df_to_edit = df_to_edit[df_to_edit['RICHTER TAG 1'].astype(str) == richter_filter]

        st.info("💡 **Wichtig:** Nach dem Ändern/Löschen einer Zelle bitte **Enter** drücken, um die Eingabe zu bestätigen.")

        # 2. Tabelleneditor
        edited_df_subset = st.data_editor(
            df_to_edit,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="excel_data_editor"
        )

        st.divider()

        # 3. Speichern-Schaltfläche
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            if st.button("💾 ÄNDERUNGEN IN EXCEL SPEICHERN", key="btn_save_live_excel", type="primary", use_container_width=True):
                with st.spinner("Überstrage geänderte Katalogdaten zu GitHub..."):
                    try:
                        import io
                        import base64
                        import requests

                        df_full_updated = df_current.copy()
                        
                        # Spalte KATALOG-NR als eindeutigen Schlüssel nutzen
                        if 'KATALOG-NR' in df_full_updated.columns and 'KATALOG-NR' in edited_df_subset.columns:
                            # Saubere Konvertierung der Schlüssel-Spalte
                            df_full_updated['KATALOG-NR'] = df_full_updated['KATALOG-NR'].astype(str).str.replace('.0', '', regex=False).str.strip()
                            edited_df_subset_copy = edited_df_subset.copy()
                            edited_df_subset_copy['KATALOG-NR'] = edited_df_subset_copy['KATALOG-NR'].astype(str).str.replace('.0', '', regex=False).str.strip()

                            df_full_updated.set_index('KATALOG-NR', inplace=True)
                            edited_indexed = edited_df_subset_copy.set_index('KATALOG-NR')
                            
                            # Aktualisiere die veränderten Zeilen
                            df_full_updated.update(edited_indexed)
                            df_full_updated.reset_index(inplace=True)
                        else:
                            df_full_updated = edited_df_subset
							
						# -------------------------------------------------------------
                        # 🎯 GENAU HIER HIN (vor dem Bereitstellen für den Export):
                        for sel_c in ['SELECTION 1', 'SELECTION 2']:
                            if sel_c in df_full_updated.columns:
                                df_full_updated[sel_c] = df_full_updated[sel_c].astype(str).str.strip().str.upper()
                        # -------------------------------------------------------------

                        # Saubere Formatierung: Leere Werte oder 'None' zu '-'
                        df_export = df_full_updated[valid_cols].fillna('-')

                        # In Excel-Bytes konvertieren
                        output_buffer = io.BytesIO()
                        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                            df_export.to_excel(writer, index=False, sheet_name='Sheet1')
                        file_bytes = output_buffer.getvalue()

                        # GitHub API Upload
                        token = st.secrets["GITHUB_TOKEN"]
                        repo = st.secrets["GITHUB_REPO"]
                        filename = EXCEL_FILE
                        branch = "main"

                        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
                        headers = {"Authorization": f"token {token}"}

                        res = requests.get(url, headers=headers)
                        sha = res.json().get("sha") if res.status_code == 200 else None

                        content_base64 = base64.b64encode(file_bytes).decode("utf-8")

                        payload = {
                            "message": "Live Katalog-Korrektur via Streamlit Data Editor",
                            "content": content_base64,
                            "branch": branch
                        }
                        if sha:
                            payload["sha"] = sha

                        response = requests.put(url, json=payload, headers=headers)

                        if response.status_code in [200, 201]:
                            # AGGRESSIVES LEEREN DES CACHES (Verhindert Geisterdaten!)
                            st.cache_data.clear()
                            if hasattr(load_labels, 'clear'):
                                load_labels.clear()
                            
                            st.success("✅ **Erfolgreich gespeichert!** Die Excel-Datei wurde auf GitHub aktualisiert und der App-Cache geleert.")
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ GitHub API Fehler ({response.status_code}): {response.text}")

                    except Exception as e:
                        st.error(f"❌ Fehler beim Speichern: {e}")

        with col_cancel:
            if st.button("🚫 Abbrechen", key="btn_cancel_excel_edit", use_container_width=True):
                set_view("Home")
                st.rerun()

    st.divider()
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_excel_edit", use_container_width=True):
        set_view("Home")
