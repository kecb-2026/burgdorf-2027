# -*- coding: utf-8 -*-
"""Ansicht: Nominated_Cats"""
from io import BytesIO
from core.access import key_param
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
from core.rounds import round_label, usable_rounds
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
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
        runden = usable_rounds(store, df_full)
        data_runden = {n: [] for n in runden}
        
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

            # Echte Trennung nach SELECTION 1 / 2 / 3 (eine Runde je Spalte)
            for n in runden:
                if str(row.get(f'SELECTION {n}', '')).strip().upper() == 'X':
                    richter_n = row.get(f'RICHTER TAG {n}', row.get(f'RICHTER {n}', ''))
                    data_runden[n].append({
                        "Katalog-Nr.": kat_nr,
                        "Rasse": row.get('RASSE', '-'),
                        "Farbcode": row.get('FARBE', '-'),
                        "Farbgruppe": farbgruppe,
                        "Geburtsdatum": geb_datum,
                        "Geschlecht": row.get('GESCHLECHT', '-'),
                        "Kategorie": row.get('KATEGORIE', '-'),
                        "Klasse": klasse,
                        "Show-Klasse": get_show_class(row),
                        "Richter": richter_n if pd.notna(richter_n) and str(richter_n) != "nan" else "-",
                        "Runde": round_label(n, with_emoji=False)
                    })

        # Ein Reiter pro Runde + das Druckzentrum
        tab_namen = [round_label(n) for n in runden] + ["🖨️ PDF Richter-Druckzentrum"]
        alle_tabs = st.tabs(tab_namen)
        tab_pdf_druck = alle_tabs[-1]

        sort_options = {"Katalog-Nr.": "Katalog-Nr.", "Rasse": "Rasse", "Kategorie": "Kategorie", "Klasse": "Klasse", "Geschlecht": "Geschlecht", "Richter": "Richter"}
        reihenfolge = ["Kitten 4-8 M", "Kitten 4-8 W", "Junior 8-12 M", "Junior 8-12 W", "Neuter M", "Neuter W", "Adult M", "Adult W"]

        for tab_n, n in zip(alle_tabs[:-1], runden):
            rname = round_label(n, with_emoji=False)
            with tab_n:
                if data_runden[n]:
                    df_nom = pd.DataFrame(data_runden[n])
                    
                    # --- ADMIN-KONTROLLZENTRUM ---
                    st.markdown(f"### 🛡️ Admin-Kontrollzentrum ({rname})")
                    df_valid = df_nom[df_nom['Richter'] != "-"].copy()
                    
                    dups = df_nom[df_nom.duplicated(subset=['Katalog-Nr.'], keep=False)]
                    if not dups.empty:
                        st.error(f"❌ {len(dups['Katalog-Nr.'].unique())} Katze(n) sind mehrfach nominiert!")
                        st.dataframe(dups[['Katalog-Nr.', 'Richter']], hide_index=True)
                    else:
                        st.success(f"✅ Katalog-Nummern für {rname} sind eindeutig.")
                    
                    if not df_valid.empty:
                        richter_load = df_valid.groupby(['Richter', 'Kategorie']).size().reset_index(name='Anzahl')
                        overloaded = richter_load[richter_load['Anzahl'] > 8]
                        if not overloaded.empty:
                            st.warning(f"⚠️ {len(overloaded)} Richter-Kategorie-Kombination(en) über Limit (8)!")
                            st.dataframe(overloaded, hide_index=True)
                        else:
                            st.success(f"✅ Richter-Kapazität für {rname} eingehalten.")
                            
                        violation = df_valid.groupby(['Richter', 'Kategorie', 'Show-Klasse']).filter(lambda x: len(x) > 1)
                        if not violation.empty:
                            st.error(f"❌ {len(violation['Richter'].unique())} Richter hat Klassen-Verstöße!")
                            st.dataframe(violation[['Richter', 'Kategorie', 'Show-Klasse', 'Katalog-Nr.']], hide_index=True)
                        else:
                            st.success(f"✅ Klassen-Regel für {rname} eingehalten.")
                    
                    st.divider()

                    # --- FILTER & SORTIERUNG ---
                    st.markdown(f"### 🔍 Filter & Sortierung ({rname})")
                    c_f1, c_f2 = st.columns(2)
                    with c_f1:
                        r_opt = ["Alle Richter"] + sorted([r for r in df_nom['Richter'].unique() if r != "-"])
                        w_richter = st.selectbox("Nach Richter filtern:", r_opt, key=f"r_t{n}")
                    with c_f2:
                        k_opt = ["Alle Kategorien"] + sorted([str(k) for k in df_nom['Kategorie'].unique() if k != "-"])
                        w_kat = st.selectbox("Nach Kategorie filtern:", k_opt, key=f"k_t{n}")
                        
                    c_f3, c_f4 = st.columns(2)
                    with c_f3:
                        vorhandene_sk = [sk for sk in reihenfolge if sk in df_nom['Show-Klasse'].unique()]
                        w_sk = st.selectbox("Nach Show-Klasse filtern:", ["Alle Show-Klassen"] + vorhandene_sk, key=f"sk_t{n}")
                    with c_f4:
                        g_opt = ["Alle Geschlechter"] + sorted([str(g) for g in df_nom['Geschlecht'].unique() if g != "-"])
                        w_geschlecht = st.selectbox("Nach Geschlecht filtern:", g_opt, key=f"g_t{n}")

                    w_sort = st.selectbox("Primär sortieren nach:", list(sort_options.keys()), key=f"s_t{n}")

                    if w_richter != "Alle Richter": df_nom = df_nom[df_nom['Richter'] == w_richter]
                    if w_kat != "Alle Kategorien": df_nom = df_nom[df_nom['Kategorie'].astype(str) == w_kat]
                    if w_sk != "Alle Show-Klassen": df_nom = df_nom[df_nom['Show-Klasse'].astype(str) == w_sk]
                    if w_geschlecht != "Alle Geschlechter": df_nom = df_nom[df_nom['Geschlecht'] == w_geschlecht]

                    if w_sort == "Katalog-Nr.":
                        df_nom = df_nom.sort_values(by="Katalog-Nr.", key=lambda x: pd.to_numeric(x, errors='coerce'))
                    else:
                        df_nom = df_nom.sort_values(by=sort_options[w_sort])

                    st.success(f"Gefunden: {len(df_nom)} nominierte Katze(n) für {rname}.")
                    st.dataframe(df_nom, use_container_width=True, hide_index=True)
                    
                    csv_n = df_nom.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(f"📥 Liste {rname} als CSV herunterladen", data=csv_n, file_name=f"nominated_runde{n}.csv", mime="text/csv", key=f"dl_t{n}")
                else:
                    st.info(f"Keine Nominationen für {rname} (Spalte 'SELECTION {n}') vorhanden.")

        # --- REITER 3: DER NEUE DRUCK-BEREICH FÜR DAS REVOLUTIONÄRE RICHTER-PDF ---
        with tab_pdf_druck:
            st.markdown("### 🖨️ Offizielle Richter-Nominationsliste (PDF)")
            st.write("Wähle den Ausstellungstag und den Richter aus, um das personalisierte Deckblatt mit der Gesamtliste aller Nominationen inklusive Nominierungs-Richter zu drucken.")
            
            day_num = st.selectbox("📅 Runde für PDF wählen:", runden, format_func=round_label, key="pdf_round_sel")
            selected_day_label = round_label(day_num, with_emoji=False)
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
                            test_live_url = f"{base_url}?view=test-live-voting&auth=true&role=Richter&judge={judge_param}&day={day_num}{key_param()}"

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
