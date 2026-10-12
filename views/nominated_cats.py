# -*- coding: utf-8 -*-
"""Ansicht: Nominated_Cats"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
import os
import pandas as pd
import qrcode
import streamlit as st
from core.config import BASE_URL, LOGO_URL
from core.data import load_labels, roman_to_numeric
from core.ui import display_header_with_logo, set_view


def render():
    display_header_with_logo("🏅 Nominierte Katzen (Admin-Zentrale)")

    def get_show_class(row):
        kl = str(row.get('KLASSE_INTERNAL', row.get('AUSSTELLUNGSKLASSE', row.get('KLASSE', '')))).replace('.0', '')
        geschlecht = str(row.get('GESCHLECHT', '')).upper()
        if kl in ['1','3','5','7','9']: return f"Adult {geschlecht}"
        if kl in ['2','4','6','8','10']: return f"Neuter {geschlecht}"
        if kl == '11': return f"Junior 8-12 {geschlecht}"
        if kl == '12': return f"Kitten 4-8 {geschlecht}"
        return "Unbekannt"    
    
    df_full = load_labels()
        
    if df_full is not None:
        data_tag1 = []
        data_tag2 = []
        
        for _, row in df_full.iterrows():
            kat_nr = row.get('KAT_STR', str(row.get('KATALOG-NR', ''))).replace('.0', '')
            klasse = row.get('KLASSE_INTERNAL', row.get('AUSSTELLUNGSKLASSE', row.get('KLASSE', '-')))
            
            # Farb- und Spalten-Ermittlung komplett unzensiert
            fg_cols = [c for c in row.index if "FARBGRUPPE" in c or "FARB-GRUPPE" in c]
            farbgruppe = row[fg_cols[0]] if fg_cols else row.get('FARBGRUPPE', '-')
            
            geb_cols = [c for c in row.index if "GEB" in c or "GEBURT" in c]
            geb_datum = row[geb_cols[0]] if geb_cols else row.get('GEB_DATUM', '-')
            if isinstance(geb_datum, pd.Timestamp): 
                geb_datum = geb_datum.strftime('%d.%m.%Y')

            # Echte Trennung nach SELECTION 1
            if str(row.get('SELECTION 1', '')).strip().upper() == 'X':
                richter_t1 = row.get('RICHTER TAG 1', row.get('RICHTER 1', ''))
                data_tag1.append({
                    "Katalog-Nr.": kat_nr,
                    "Rasse": row.get('RASSE', '-'),
                    "Farbcode": row.get('FARBE', '-'),
                    "Farbgruppe": farbgruppe,
                    "Geburtsdatum": geb_datum,
                    "Geschlecht": row.get('GESCHLECHT', '-'),
                    "Kategorie": row.get('KATEGORIE', '-'),
                    "Klasse": klasse,
                    "Show-Klasse": get_show_class(row),
                    "Richter": richter_t1 if pd.notna(richter_t1) and str(richter_t1) != "nan" else "-",
                    "Tag": "Tag 1 (Sa)"
                })
                
            # Echte Trennung nach SELECTION 2
            if str(row.get('SELECTION 2', '')).strip().upper() == 'X':
                richter_t2 = row.get('RICHTER TAG 2', row.get('RICHTER 2', ''))
                data_tag2.append({
                    "Katalog-Nr.": kat_nr,
                    "Rasse": row.get('RASSE', '-'),
                    "Farbcode": row.get('FARBE', '-'),
                    "Farbgruppe": farbgruppe,
                    "Geburtsdatum": geb_datum,
                    "Geschlecht": row.get('GESCHLECHT', '-'),
                    "Kategorie": row.get('KATEGORIE', '-'),
                    "Klasse": klasse,
                    "Show-Klasse": get_show_class(row),
                    "Richter": richter_t2 if pd.notna(richter_t2) and str(richter_t2) != "nan" else "-",
                    "Tag": "Tag 2 (So)"
                })

        # Drei Reiter: Deine beiden Original-Tage + das neue Druckzentrum
        tab_t1, tab_t2, tab_pdf_druck = st.tabs(["Tag 1 (Samstag)", "Tag 2 (Sonntag)", "🖨️ PDF Richter-Druckzentrum"])

        # --- SEITE FÜR TAG 1 (DEIN ORIGINAL CODE) ---
        with tab_t1:
            if data_tag1:
                df_nom_t1 = pd.DataFrame(data_tag1)
                
                # --- ADMIN-KONTROLLZENTRUM TAG 1 ---
                st.markdown("### 🛡️ Admin-Kontrollzentrum (Samstag)")
                df_valid_t1 = df_nom_t1[df_nom_t1['Richter'] != "-"].copy()
                
                dups_t1 = df_nom_t1[df_nom_t1.duplicated(subset=['Katalog-Nr.'], keep=False)]
                if not dups_t1.empty:
                    st.error(f"❌ {len(dups_t1['Katalog-Nr.'].unique())} Katze(n) sind mehrfach nominiert!")
                    st.dataframe(dups_t1[['Katalog-Nr.', 'Richter']], hide_index=True)
                else:
                    st.success("✅ Katalog-Nummern für Samstag sind eindeutig.")
                
                if not df_valid_t1.empty:
                    richter_load_t1 = df_valid_t1.groupby(['Richter', 'Kategorie']).size().reset_index(name='Anzahl')
                    overloaded_t1 = richter_load_t1[richter_load_t1['Anzahl'] > 8]
                    if not overloaded_t1.empty:
                        st.warning(f"⚠️ {len(overloaded_t1)} Richter-Kategorie-Kombination(en) über Limit (8)!")
                        st.dataframe(overloaded_t1, hide_index=True)
                    else:
                        st.success("✅ Richter-Kapazität für Samstag eingehalten.")
                        
                    violation_t1 = df_valid_t1.groupby(['Richter', 'Kategorie', 'Show-Klasse']).filter(lambda x: len(x) > 1)
                    if not violation_t1.empty:
                        st.error(f"❌ {len(violation_t1['Richter'].unique())} Richter hat Klassen-Verstöße!")
                        st.dataframe(violation_t1[['Richter', 'Kategorie', 'Show-Klasse', 'Katalog-Nr.']], hide_index=True)
                    else:
                        st.success("✅ Klassen-Regel für Samstag eingehalten.")
                
                st.divider()

                # --- FILTER & SORTIERUNG TAG 1 ---
                st.markdown("### 🔍 Filter & Sortierung (Samstag)")
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    r_opt_t1 = ["Alle Richter"] + sorted([r for r in df_nom_t1['Richter'].unique() if r != "-"])
                    w_richter_t1 = st.selectbox("Nach Richter filtern:", r_opt_t1, key="r_t1")
                with c_f2:
                    k_opt_t1 = ["Alle Kategorien"] + sorted([str(k) for k in df_nom_t1['Kategorie'].unique() if k != "-"])
                    w_kat_t1 = st.selectbox("Nach Kategorie filtern:", k_opt_t1, key="k_t1")
                    
                c_f3, c_f4 = st.columns(2)
                with c_f3:
                    reihenfolge = ["Kitten 4-8 M", "Kitten 4-8 W", "Junior 8-12 M", "Junior 8-12 W", "Neuter M", "Neuter W", "Adult M", "Adult W"]
                    vorhandene_sk_t1 = [sk for sk in reihenfolge if sk in df_nom_t1['Show-Klasse'].unique()]
                    w_sk_t1 = st.selectbox("Nach Show-Klasse filtern:", ["Alle Show-Klassen"] + vorhandene_sk_t1, key="sk_t1")
                with c_f4:
                    g_opt_t1 = ["Alle Geschlechter"] + sorted([str(g) for g in df_nom_t1['Geschlecht'].unique() if g != "-"])
                    w_geschlecht_t1 = st.selectbox("Nach Geschlecht filtern:", g_opt_t1, key="g_t1")

                sort_options = {"Katalog-Nr.": "Katalog-Nr.", "Rasse": "Rasse", "Kategorie": "Kategorie", "Klasse": "Klasse", "Geschlecht": "Geschlecht", "Richter": "Richter"}
                w_sort_t1 = st.selectbox("Primär sortieren nach:", list(sort_options.keys()), key="s_t1")

                if w_richter_t1 != "Alle Richter": df_nom_t1 = df_nom_t1[df_nom_t1['Richter'] == w_richter_t1]
                if w_kat_t1 != "Alle Kategorien": df_nom_t1 = df_nom_t1[df_nom_t1['Kategorie'].astype(str) == w_kat_t1]
                if w_sk_t1 != "Alle Show-Klassen": df_nom_t1 = df_nom_t1[df_nom_t1['Show-Klasse'].astype(str) == w_sk_t1]
                if w_geschlecht_t1 != "Alle Geschlechter": df_nom_t1 = df_nom_t1[df_nom_t1['Geschlecht'] == w_geschlecht_t1]

                if w_sort_t1 == "Katalog-Nr.":
                    df_nom_t1 = df_nom_t1.sort_values(by="Katalog-Nr.", key=lambda x: pd.to_numeric(x, errors='coerce'))
                else:
                    df_nom_t1 = df_nom_t1.sort_values(by=sort_options[w_sort_t1])

                st.success(f"Gefunden: {len(df_nom_t1)} nominierte Katze(n) für Samstag.")
                st.dataframe(df_nom_t1, use_container_width=True, hide_index=True)
                
                csv_t1 = df_nom_t1.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Liste Tag 1 als CSV herunterladen", data=csv_t1, file_name="nominated_samstag.csv", mime="text/csv", key="dl_t1")
            else:
                st.info("Keine Nominationen für Tag 1 (Spalte 'SELECTION 1') vorhanden.")

        # --- SEITE FÜR TAG 2 (DEIN ORIGINAL CODE) ---
        with tab_t2:
            if data_tag2:
                df_nom_t2 = pd.DataFrame(data_tag2)
                
                # --- ADMIN-KONTROLLZENTRUM TAG 2 ---
                st.markdown("### 🛡️ Admin-Kontrollzentrum (Sonntag)")
                df_valid_t2 = df_nom_t2[df_nom_t2['Richter'] != "-"].copy()
                
                dups_t2 = df_nom_t2[df_nom_t2.duplicated(subset=['Katalog-Nr.'], keep=False)]
                if not dups_t2.empty:
                    st.error(f"❌ {len(dups_t2['Katalog-Nr.'].unique())} Katze(n) sind mehrfach nominiert!")
                    st.dataframe(dups_t2[['Katalog-Nr.', 'Richter']], hide_index=True)
                else:
                    st.success("✅ Katalog-Nummern für Sonntag sind eindeutig.")
                
                if not df_valid_t2.empty:
                    richter_load_t2 = df_valid_t2.groupby(['Richter', 'Kategorie']).size().reset_index(name='Anzahl')
                    overloaded_t2 = richter_load_t2[richter_load_t2['Anzahl'] > 8]
                    if not overloaded_t2.empty:
                        st.warning(f"⚠️ {len(overloaded_t2)} Richter-Kategorie-Kombination(en) über Limit (8)!")
                        st.dataframe(overloaded_t2, hide_index=True)
                    else:
                        st.success("✅ Richter-Kapazität für Sonntag eingehalten.")
                        
                    violation_t2 = df_valid_t2.groupby(['Richter', 'Kategorie', 'Show-Klasse']).filter(lambda x: len(x) > 1)
                    if not violation_t2.empty:
                        st.error(f"❌ {len(violation_t2['Richter'].unique())} Richter hat Klassen-Verstöße!")
                        st.dataframe(violation_t2[['Richter', 'Kategorie', 'Show-Klasse', 'Katalog-Nr.']], hide_index=True)
                    else:
                        st.success("✅ Klassen-Regel für Sonntag eingehalten.")
                
                st.divider()

                # --- FILTER & SORTIERUNG TAG 2 ---
                st.markdown("### 🔍 Filter & Sortierung (Sonntag)")
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    r_opt_t2 = ["Alle Richter"] + sorted([r for r in df_nom_t2['Richter'].unique() if r != "-"])
                    w_richter_t2 = st.selectbox("Nach Richter filtern:", r_opt_t2, key="r_t2")
                with c_f2:
                    k_opt_t2 = ["Alle Kategorien"] + sorted([str(k) for k in df_nom_t2['Kategorie'].unique() if k != "-"])
                    w_kat_t2 = st.selectbox("Nach Kategorie filtern:", k_opt_t2, key="k_t2")
                    
                c_f3, c_f4 = st.columns(2)
                with c_f3:
                    reihenfolge = ["Kitten 4-8 M", "Kitten 4-8 W", "Junior 8-12 M", "Junior 8-12 W", "Neuter M", "Neuter W", "Adult M", "Adult W"]
                    vorhandene_sk_t2 = [sk for sk in reihenfolge if sk in df_nom_t2['Show-Klasse'].unique()]
                    w_sk_t2 = st.selectbox("Nach Show-Klasse filtern:", ["Alle Show-Klassen"] + vorhandene_sk_t2, key="sk_t2")
                with c_f4:
                    g_opt_t2 = ["Alle Geschlechter"] + sorted([str(g) for g in df_nom_t2['Geschlecht'].unique() if g != "-"])
                    w_geschlecht_t2 = st.selectbox("Nach Geschlecht filtern:", g_opt_t2, key="g_t2")

                w_sort_t2 = st.selectbox("Primär sortieren nach:", list(sort_options.keys()), key="s_t2")

                if w_richter_t2 != "Alle Richter": df_nom_t2 = df_nom_t2[df_nom_t2['Richter'] == w_richter_t2]
                if w_kat_t2 != "Alle Kategorien": df_nom_t2 = df_nom_t2[df_nom_t2['Kategorie'].astype(str) == w_kat_t2]
                if w_sk_t2 != "Alle Show-Klassen": df_nom_t2 = df_nom_t2[df_nom_t2['Show-Klasse'].astype(str) == w_sk_t2]
                if w_geschlecht_t2 != "Alle Geschlechter": df_nom_t2 = df_nom_t2[df_nom_t2['Geschlecht'] == w_geschlecht_t2]

                if w_sort_t2 == "Katalog-Nr.":
                    df_nom_t2 = df_nom_t2.sort_values(by="Katalog-Nr.", key=lambda x: pd.to_numeric(x, errors='coerce'))
                else:
                    df_nom_t2 = df_nom_t2.sort_values(by=sort_options[w_sort_t2])

                st.success(f"Gefunden: {len(df_nom_t2)} nominierte Katze(n) für Sonntag.")
                st.dataframe(df_nom_t2, use_container_width=True, hide_index=True)
                
                csv_t2 = df_nom_t2.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Liste Tag 2 als CSV herunterladen", data=csv_t2, file_name="nominated_sonntag.csv", mime="text/csv", key="dl_t2")
            else:
                st.info("Keine Nominationen für Tag 2 (Spalte 'SELECTION 2') vorhanden.")

        # --- REITER 3: DER NEUE DRUCK-BEREICH FÜR DAS REVOLUTIONÄRE RICHTER-PDF ---
        with tab_pdf_druck:
            st.markdown("### 🖨️ Offizielle Richter-Nominationsliste (PDF)")
            st.write("Wähle den Ausstellungstag und den Richter aus, um das personalisierte Deckblatt mit der Gesamtliste aller Nominationen inklusive Nominierungs-Richter zu drucken.")
            
            selected_day_label = st.selectbox("📅 Ausstellungstag für PDF wählen:", ["Tag 1 (Samstag)", "Tag 2 (Sonntag)"], key="pdf_day_sel")
            day_num = 1 if "Tag 1" in selected_day_label else 2
            tag_key = f"TAG {day_num}"
            selection_col = f"SELECTION {day_num}"
            judge_col = f"RICHTER TAG {day_num}"
            
            if selection_col in df_full.columns and judge_col in df_full.columns:
                available_judges = sorted([r for r in df_full[judge_col].unique() if pd.notna(r) and str(r).strip() != "" and str(r).lower() != "nan" and str(r) != "-"])
                
                if available_judges:
                    selected_judge = st.selectbox("👨‍⚖️ Richter für PDF wählen (für Deckblatt & QR-Code):", available_judges, key="pdf_judge_sel")
                    st.write("")
                    
                    if st.button(f"🖨️ PDF für {selected_judge} ({tag_key}) generieren", use_container_width=True, key="btn_gen_pdf_nominated"):
                        
                        # Alle nominierten Katzen des Tages holen
                        df_nominated = df_full[df_full[selection_col].astype(str).str.upper() == 'X'].copy()
                        
                        # Sprechende Übersetzungen der Klassen (z.B. Kitten 4-8 Female)
                        def get_pdf_show_class_label(row):
                            kl = str(row.get('KLASSE_INTERNAL', row.get('AUSSTELLUNGSKLASSE', ''))).replace('.0', '').strip()
                            geschlecht_raw = str(row.get('GESCHLECHT', '')).strip().lower()
                            geschlecht_str = "Male" if geschlecht_raw in ['m', '1,0', 'male'] else "Female"
                            
                            if kl in ['1','3','5','7','9']: return f"Adult {geschlecht_str}"
                            if kl in ['2','4','6','8','10']: return f"Neuter {geschlecht_str}"
                            if kl == '11': return f"Junior 8-12 {geschlecht_str}"
                            if kl == '12': return f"Kitten 4-8 {geschlecht_str}"
                            return f"Class {kl} {geschlecht_str}"

                        if not df_nominated.empty:
                            pdf_buffer = BytesIO()
                            doc = SimpleDocTemplate(
                                pdf_buffer, pagesize=A4,
                                leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
                            )
                            
                            styles = getSampleStyleSheet()
                            title_style = ParagraphStyle(
                                'CoverTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
                                fontSize=26, leading=32, alignment=1, textColor=colors.HexColor('#1a4a9e'), spaceAfter=30
                            )
                            cat_header_style = ParagraphStyle(
                                'CategoryHeader', parent=styles['Heading2'], fontName='Helvetica-Bold',
                                fontSize=22, leading=26, textColor=colors.HexColor('#1a4a9e'), spaceBefore=15, spaceAfter=15, keepWithNext=True
                            )
                            class_header_style = ParagraphStyle(
                                'ClassHeader', parent=styles['Heading3'], fontName='Helvetica-Bold',
                                fontSize=14, leading=18, textColor=colors.HexColor('#333333'), spaceBefore=12, spaceAfter=6, keepWithNext=True
                            )
                            
                            # Farb-Styles
                            cell_header_text = ParagraphStyle('CellHeaderText', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=1, textColor=colors.white)
                            cell_text_bold = ParagraphStyle('CellTextBold', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=1, textColor=colors.black)
                            cell_text_normal = ParagraphStyle('CellTextNormal', fontName='Helvetica', fontSize=10, leading=13, alignment=0, textColor=colors.black)
                            
                            story = []
                            
                            # ======================================================
                            # SEITE 1: COVERSHEET
                            # ======================================================
                            story.append(Spacer(1, 40))
                            if os.path.exists(LOGO_URL):
                                story.append(Image(LOGO_URL, width=120, height=120))
                                story.append(Spacer(1, 20))
                                
                            story.append(Paragraph(f"Nominated Cats List<br/>Burgdorf Day {day_num} - {selected_judge}", title_style))
                            story.append(Spacer(1, 30))
                            
                            # Reines Ersetzen der Leerzeichen durch ein + (Sonderzeichen bleiben wie sie sind)
                            base_url = BASE_URL
                            judge_param = str(selected_judge).replace(' ', '+')
                            test_live_url = f"{base_url}?view=test-live-voting&auth=true&role=Richter&judge={judge_param}&day={day_num}"

                            qr = qrcode.QRCode(version=1, box_size=10, border=4)
                            qr.add_data(test_live_url)
                            qr.make(fit=True)
                            img_qr = qr.make_image(fill_color="black", back_color="white")
                            
                            qr_buffer = BytesIO()
                            img_qr.save(qr_buffer, format="PNG")
                            qr_buffer.seek(0)
                            
                            story.append(Image(qr_buffer, width=200, height=200))
                            story.append(Spacer(1, 15))
                            story.append(Paragraph(
                                f"<font color='#1a4a9e'><b>SCAN FOR LIVE VOTING</b></font><br/>"
                                f"<font size='8' color='#666666'>{test_live_url}</font>", 
                                ParagraphStyle('QR_Sub', fontName='Helvetica', fontSize=10, alignment=1, leading=14)
                            ))
                            
                            from reportlab.platypus import PageBreak
                            story.append(PageBreak())
                            
                            # ======================================================
                            # SEITE 2+: DIE GESAMTLISTE MIT NEUER SORTIERUNG
                            # ======================================================
                            categories = sorted(df_nominated['KATEGORIE'].unique(), key=lambda x: str(x))
                            
                            for idx_cat, cat in enumerate(categories):
                                if idx_cat > 0:
                                    story.append(PageBreak())
                                    
                                story.append(Paragraph(f"Category {cat}", cat_header_style))
                                df_cat = df_nominated[df_nominated['KATEGORIE'] == cat].copy()
                                df_cat['PDF_SHOW_CLASS'] = df_cat.apply(get_pdf_show_class_label, axis=1)
                                
                                # EXAKTE REIHNENFOLGE NACH DEINER VORGABE: (Zuerst Female vor Male!)
                                klassen_reihenfolge = [
                                    "Kitten 4-8 Female", "Kitten 4-8 Male", 
                                    "Junior 8-12 Female", "Junior 8-12 Male", 
                                    "Neuter Female", "Neuter Male", 
                                    "Adult Female", "Adult Male"
                                ]
                                
                                # Nur die Klassen herausfiltern, die auch tatsächlich Katzen enthalten
                                vorhandene_klassen = [sk for sk in klassen_reihenfolge if sk in df_cat['PDF_SHOW_CLASS'].unique()]
                                for sk in df_cat['PDF_SHOW_CLASS'].unique():
                                    if sk not in vorhandene_klassen:
                                        vorhandene_klassen.append(sk)
                                        
                                # Durchlaufe die Klassen in der exakten Wunsch-Reihenfolge
                                for s_klasse in vorhandene_klassen:
                                    df_class = df_cat[df_cat['PDF_SHOW_CLASS'] == s_klasse].copy()
                                    df_class['SORT_KEY'] = pd.to_numeric(df_class['KATALOG-NR'], errors='coerce')
                                    df_class = df_class.sort_values('SORT_KEY')
                                    
                                    if not df_class.empty:
                                        story.append(Paragraph(s_klasse, class_header_style))
                                        
                                        # Tabellen-Header
                                        table_data = [[
                                            Paragraph("<b>Number</b>", cell_header_text), 
                                            Paragraph("<b>EMS/Group</b>", cell_header_text), 
                                            Paragraph("<b>Date of Birth</b>", cell_header_text), 
                                            Paragraph("<b>Sex</b>", cell_header_text),
                                            Paragraph("<b>Nominated by</b>", cell_header_text)
                                        ]]
                                        
                                        for _, row in df_class.iterrows():
                                            kat_nr = str(row.get('KAT_STR', row.get('KATALOG-NR', ''))).replace('.0', '')
                                            rasse_name = row.get('RASSE', '-')
                                            farbcode = row.get('FARBE', '-')
                                            
                                            fg_cols = [c for c in row.index if "FARBGRUPPE" in str(c) or "FARB-GRUPPE" in str(c)]
                                            farbgruppe = row[fg_cols[0]] if fg_cols else row.get('FARBGRUPPE', '')
                                            gruppe_clean = roman_to_numeric(farbgruppe) if 'roman_to_numeric' in globals() else farbgruppe
                                            
                                            if gruppe_clean and str(gruppe_clean).strip() != "-":
                                                details_text = f"<b>{rasse_name} {farbcode}</b><br/>Group {gruppe_clean}"
                                            else:
                                                details_text = f"<b>{rasse_name} {farbcode}</b>"
                                                
                                            geb_cols = [c for c in row.index if "GEB" in str(c) or "GEBURT" in str(c)]
                                            geb_datum = row[geb_cols[0]] if geb_cols else row.get('GEB_DATUM', '-')
                                            if isinstance(geb_datum, pd.Timestamp):
                                                geb_datum = geb_datum.strftime('%d.%m.%Y')
                                            elif pd.isna(geb_datum) or str(geb_datum).strip().lower() == "nan":
                                                geb_datum = "–"
                                                
                                            geschl_raw = str(row.get('GESCHLECHT', '-')).strip().upper()
                                            geschl_text = "MALE (1.0)" if geschl_raw in ['M', '1,0', 'MALE'] else "FEMALE (0.1)"
                                            
                                            nominating_judge = row.get(judge_col, row.get(f'RICHTER {day_num}', '-'))
                                            if pd.isna(nominating_judge) or str(nominating_judge).strip().lower() == "nan" or str(nominating_judge).strip() == "":
                                                nominating_judge = "-"
                                            
                                            table_data.append([
                                                Paragraph(f"<font size='14'><b>{kat_nr}</b></font>", cell_text_bold),
                                                Paragraph(details_text, cell_text_normal),
                                                Paragraph(str(geb_datum), cell_text_bold),
                                                Paragraph(geschl_text, cell_text_bold),
                                                Paragraph(str(nominating_judge), cell_text_bold)
                                            ])
                                            
                                        cat_table = Table(table_data, colWidths=[55, 175, 80, 88, 125])
                                        cat_table.setStyle(TableStyle([
                                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4a9e')),
                                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                                        ]))
                                        
                                        story.append(cat_table)
                                        story.append(Spacer(1, 10))
                                        
                            doc.build(story)
                            pdf_buffer.seek(0)
                            
                            st.success(f"🎉 PDF-Kompilierung für Richter {selected_judge} erfolgreich abgeschlossen!")
                            st.download_button(
                                label=f"📥 PDF-Datei herunterladen und drucken",
                                data=pdf_buffer,
                                file_name=f"Nominated_Cats_Day{day_num}_{selected_judge.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.warning(f"Für {selected_day_label} wurden generell keine nominierten Katzen gefunden.")
                else:
                    st.info("Es wurden am gewählten Tag keine gültigen Richternamen gefunden.")
            else:
                st.error(f"Fehler: Spaltenstrukturen '{selection_col}' oder '{judge_col}' fehlen in der Datei.")

    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_nom"):
        set_view("Home")


# ADMIN PANEL
