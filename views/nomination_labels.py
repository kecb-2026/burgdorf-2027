# -*- coding: utf-8 -*-
"""Ansicht: Nomination_Labels"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import pandas as pd
import streamlit as st
from core.data import get_full_label, load_labels
from core.ui import display_header_with_logo, set_view


def render():
    display_header_with_logo("🖨️ Nomination Labels Druckzentrale")
    st.write("Generiere hier die exakten Druck-Labels (8 Stück pro A4-Seite). Jede Klasse beginnt ein neues Blatt.")

    df_full = load_labels()
    
    if df_full is not None:
        # 1. Spaltennamen radikal säubern
        df_full.columns = [str(c).strip().upper() for c in df_full.columns]
        
        # 2. Hilfsspalte für eine korrekte numerische Sortierung erstellen
        # Verhindert, dass 100 vor 11 kommt
        if 'KAT_STR' in df_full.columns:
            df_full['_sort_nr_helper'] = pd.to_numeric(
                df_full['KAT_STR'].astype(str).str.replace('.0', '', regex=False).str.strip(), 
                errors='coerce'
            ).fillna(9999).astype(int)
        else:
            df_full['_sort_nr_helper'] = 0

        # 3. Präzise Filterung & direkte Sortierung (Kategorie -> Klasse -> Kat.-Nr.)
        sort_spalten = []
        if 'KATEGORIE' in df_full.columns: sort_spalten.append('KATEGORIE')
        if 'KLASSE_INTERNAL' in df_full.columns: sort_spalten.append('KLASSE_INTERNAL')
        sort_spalten.append('_sort_nr_helper')

        if 'SELECTION 1' in df_full.columns:
            df_samstag_daten = df_full[df_full['SELECTION 1'].astype(str).str.strip().str.upper() == 'X'].sort_values(by=sort_spalten).copy()
        elif 'SELECTION' in df_full.columns:
            df_samstag_daten = df_full[df_full['SELECTION'].astype(str).str.strip().str.upper() == 'X'].sort_values(by=sort_spalten).copy()
        else:
            df_samstag_daten = pd.DataFrame(columns=df_full.columns)
            
        if 'SELECTION 2' in df_full.columns:
            df_sonntag_daten = df_full[df_full['SELECTION 2'].astype(str).str.strip().str.upper() == 'X'].sort_values(by=sort_spalten).copy()
        else:
            df_sonntag_daten = pd.DataFrame(columns=df_full.columns)

        # Aufräumen der Hilfsspalte, damit sie nicht in der App stört
        if not df_samstag_daten.empty: df_samstag_daten.drop(columns=['_sort_nr_helper'], errors='ignore', inplace=True)
        if not df_sonntag_daten.empty: df_sonntag_daten.drop(columns=['_sort_nr_helper'], errors='ignore', inplace=True)


    
    

        # DEINE PDF-FUNKTION (KOMPLETT UNBERÜHRT UND UNVERÄNDERT)
        def generate_avery_labels(df):
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            mm = 2.83464
            label_width = 99.1 * mm
            label_height = 67.7 * mm
            margin_left = 5.9 * mm
            margin_top = 13.1 * mm
            
            color_map = {
                "AM": colors.HexColor("#ffff00"),
                "AW": colors.HexColor("#ff99cc"),
                "KM": colors.HexColor("#99cc00"),
                "KW": colors.HexColor("#33ccff"),
                "JM": colors.HexColor("#cc99ff"),
                "JW": colors.HexColor("#e60073"),
                "KiM": colors.HexColor("#ffbf00"),
                "KiW": colors.HexColor("#ff6600")
            }
            
            sorted_rows = []
            for idx, row in df.iterrows():
                klasse_val = row.get('KLASSE_INTERNAL', row.get('KLASSE', ''))
                klasse_str = str(klasse_val).replace('.0', '')
                sex = str(row.get('GESCHLECHT', '')).strip().upper()
                kat_nr_str = str(row.get('KAT_STR', '')).replace('.0', '')
                
                try:
                    kat_nr_sort = int(kat_nr_str)
                except:
                    kat_nr_sort = 9999
                
                badge_key = "AM"
                badge_label = "Adult M"
                sort_order = 0
                
                try:
                    kl_num = int(klasse_str)
                    is_male = (sex in ["1,0", "M", "MALE"])
                    if kl_num in [1, 3, 5, 7, 9]:
                        badge_key = "AM" if is_male else "AW"
                        badge_label = "Adult M" if is_male else "Adult W"
                        sort_order = 0 if is_male else 1
                    elif kl_num in [2, 4, 6, 8, 10]:
                        badge_key = "KM" if is_male else "KW"
                        badge_label = "Kastrat M" if is_male else "Kastrat W"
                        sort_order = 2 if is_male else 3
                    elif kl_num == 11:
                        badge_key = "JM" if is_male else "JW"
                        badge_label = "8-12 M" if is_male else "8-12 W"
                        sort_order = 4 if is_male else 5
                    elif kl_num == 12:
                        badge_key = "KiM" if is_male else "KiW"
                        badge_label = "4-8 M" if is_male else "4-8 W"
                        sort_order = 6 if is_male else 7
                except:
                    if "K" in sex or "N" in sex:
                        badge_key = "KM" if "M" in sex else "KW"
                        badge_label = "MN" if "M" in sex else "FN"
                        sort_order = 2 if "M" in sex else 3
                    else:
                        badge_key = "AM"
                        badge_label = f"{klasse_str} {sex}"
                        sort_order = 8
                
                row_data = row.to_dict()
                row_data['_sort_kat'] = str(row.get('KATEGORIE', '9')).replace('.0', '')
                row_data['_sort_class'] = sort_order
                row_data['_sort_kat_nr'] = kat_nr_sort
                row_data['_badge_key'] = badge_key
                row_data['_badge_label'] = badge_label
                row_data['_clean_kat_nr'] = kat_nr_str
                row_data['_clean_klasse'] = klasse_str
                sorted_rows.append(row_data)
            
            df_sorted = pd.DataFrame(sorted_rows)
            if not df_sorted.empty:
                df_sorted = df_sorted.sort_values(by=['_sort_kat', '_sort_class', '_sort_kat_nr']).reset_index(drop=True)
                grouped = df_sorted.groupby(['_sort_kat', '_sort_class'])
                
                is_first_page = True
                for (kat_name, class_idx), group in grouped:
                    if not is_first_page:
                        c.showPage()
                    is_first_page = False
                    
                    count = 0
                    for _, row in group.iterrows():
                        if count > 0 and count % 8 == 0:
                            c.showPage()
                            
                        page_idx = count % 8
                        col = page_idx % 2
                        row_idx = page_idx // 2
                        
                        x = margin_left + (col * label_width)
                        y = (297 * mm) - margin_top - ((row_idx + 1) * label_height)
                        
                        kat_nr = row['_clean_kat_nr']
                        kategorie = row['_sort_kat']
                        badge_label = row['_badge_label']
                        badge_bg = color_map.get(row['_badge_key'], colors.HexColor("#99cc00"))
                        
                        #rasse = str(row.get('RASSE', ''))
                        #farbe = str(row.get('FARBE', ''))
                        #ems_code = f"{rasse} {farbe}".strip()
                        ems_code = get_full_label(row)

                        
                        geb_cols = [col for col in row.index if "GEB" in col or "GEBURT" in col]
                        geb_datum = row[geb_cols[0]] if geb_cols else row.get('GEB_DATUM', '-')
                        if isinstance(geb_datum, pd.Timestamp):
                            geb_datum = geb_datum.strftime('%d.%m.%Y')
                        
                        c.saveState()
                        c.setStrokeColor(colors.HexColor("#e5e5e5"))
                        c.setLineWidth(0.2)
                        c.rect(x, y, label_width, label_height)
                        
                        c.setFont("Helvetica", 14)
                        c.setFillColor(colors.black)
                        c.drawString(x + 6*mm, y + label_height - 10*mm, kategorie)
                        
                        badge_w = 22 * mm
                        badge_h = 6 * mm
                        bx = x + label_width - badge_w - 6*mm
                        by = y + label_height - 11*mm
                        
                        c.setFillColor(badge_bg)
                        c.rect(bx, by, badge_w, badge_h, fill=1, stroke=0)
                        
                        c.setFillColor(colors.black)
                        c.setFont("Helvetica-Bold", 11)
                        c.drawCentredString(bx + (badge_w / 2), by + 1.8*mm, badge_label)
                        
                        c.setFont("Helvetica", 46)
                        c.drawCentredString(x + (label_width / 2), y + (label_height / 2) - 4*mm, kat_nr)
                        
                        c.setFont("Helvetica", 12)
                        c.drawString(x + 6*mm, y + 10*mm, ems_code)
                        
                        c.setFont("Helvetica", 12)
                        c.drawRightString(x + label_width - 6*mm, y + 10*mm, str(geb_datum))
                        c.restoreState()
                        count += 1
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()

        # Tabs für die Tagestrennung
        tab_tag1, tab_tag2 = st.tabs(["Tag 1 (Samstag)", "Tag 2 (Sonntag)"])
        
        # =====================================================================
        # TAB FÜR TAG 1 (SAMSTAG)
        # =====================================================================
        with tab_tag1:
            if not df_samstag_daten.empty:
                st.info(f"Aktuell sind **{len(df_samstag_daten)}** Katzen für den Labeldruck an Tag 1 bereit.")
                
                pdf_labels_t1 = generate_avery_labels(df_samstag_daten.copy())
                st.download_button(
                    label="📥 Avery Zweckform (4782) PDF generieren & herunterladen (Tag 1)",
                    data=pdf_labels_t1,
                    file_name="KECB_Nomination_Labels_Sorted_Tag1.pdf",
                    mime="application/pdf",
                    key="dl_btn_t1"
                )
                
                st.write("### Vorschau der enthaltenen Katzen (Tag 1):")
                spalten_t1 = [c for c in ['KAT_STR', 'KATEGORIE', 'KLASSE_INTERNAL', 'GESCHLECHT', 'RASSE', 'FARBE'] if c in df_samstag_daten.columns]
                namen_t1 = {"KAT_STR": "Kat.-Nr.", "KATEGORIE": "Kategorie", "KLASSE_INTERNAL": "Klasse", "GESCHLECHT": "Geschlecht", "RASSE": "Rasse", "FARBE": "Farbe"}
                config_t1 = {c: namen_t1[c] for c in spalten_t1 if c in namen_t1}
                
                # Hier sortieren wir die Daten direkt im Aufruf mit reinen Leerzeichen für die Einrückung
                st.dataframe(df_samstag_daten[spalten_t1].sort_values(by='KAT_STR', key=lambda x: pd.to_numeric(x, errors='coerce')), column_config=config_t1, use_container_width=True, hide_index=True, key="preview_table_samstag_final")
                
            else:
                st.info("Aktuell sind keine Katzen für den Labeldruck an Tag 1 (Spalte 'SELECTION 1') bereit.")

        # =====================================================================
        # TAB FÜR TAG 2 (SONNTAG)
        # =====================================================================
        with tab_tag2:
            if not df_sonntag_daten.empty:
                st.info(f"Aktuell sind **{len(df_sonntag_daten)}** Katzen für den Labeldruck an Tag 2 bereit.")
                
                pdf_labels_t2 = generate_avery_labels(df_sonntag_daten.copy())
                st.download_button(
                    label="📥 Avery Zweckform (4782) PDF generieren & herunterladen (Tag 2)",
                    data=pdf_labels_t2,
                    file_name="KECB_Nomination_Labels_Sorted_Tag2.pdf",
                    mime="application/pdf",
                    key="dl_btn_t2"
                )
                
                st.write("### Vorschau der enthaltenen Katzen (Tag 2):")
                
                # --- AB HIER ERSETZEN ---
                spalten_t2 = [c for c in ['KAT_STR', 'KATEGORIE', 'KLASSE_INTERNAL', 'GESCHLECHT', 'RASSE', 'FARBE'] if c in df_sonntag_daten.columns]
                namen_t2 = {"KAT_STR": "Kat.-Nr.", "KATEGORIE": "Kategorie", "KLASSE_INTERNAL": "Klasse", "GESCHLECHT": "Geschlecht", "RASSE": "Rasse", "FARBE": "Farbe"}
                config_t2 = {c: namen_t2[c] for c in spalten_t2 if c in namen_t2}
                
                # Wir erstellen die Struktur für die Anzeige (die künstliche Spalte 'TAG' wurde hier entfernt!)
                df_sonntag_vorschau = df_sonntag_daten[spalten_t2].copy()
                                
                # Hier sortieren wir die fertige Sonntag-Vorschau direkt beim Anzeigen
                st.dataframe(
                    df_sonntag_vorschau.sort_values(by='KAT_STR', key=lambda x: pd.to_numeric(x, errors='coerce')), 
                    column_config=config_t2, 
                    use_container_width=True, 
                    hide_index=True, 
                    key="voneinander_getrennte_sonntags_tabelle"
                )
                # --- BIS HIER ERSETZEN ---

                
            

                
            else:
                st.info("Aktuell sind keine Katzen für den Labeldruck an Tag 2 (Spalte 'SELECTION 2') bereit.")

            
        if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_labels"):
            set_view("Home")


# ADMIN PANEL
