# -*- coding: utf-8 -*-
"""Ansicht: QR_Codes_Gen"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
import qrcode
import streamlit as st
from core.access import key_param, key_required
from core.config import BASE_URL, SHOW_YEAR
from core.data import load_labels
from core.rounds import all_judges
from core.ui import display_header_with_logo, set_view


def render():
    display_header_with_logo("📱 QR-Code Login Generator")
    st.write("Lass die Richter und Mitarbeiter diesen QR-Code scannen, um sich sofort ohne Passwort einzuloggen.")
    
    df_full = load_labels()
    
    # Basis-URL deiner App
    base_url = BASE_URL
    
    # 1. Hilfsfunktion zum Zeichnen der QR-Codes für die Streamlit-UI
    def generate_qr_image(url_to_encode):
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url_to_encode)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # 2. PDF-Generierungsfunktion (Getrennter Admin-Block & Emoji-frei)
    def generate_pdf_download(df):
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, 
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=20, leading=24, spaceAfter=15, textColor=colors.HexColor("#1A365D"), alignment=1)
        section_style = ParagraphStyle('DocSection', parent=styles['Heading2'], fontSize=12, leading=15, spaceBefore=15, spaceAfter=6, textColor=colors.HexColor("#2B6CB0"))
        label_style = ParagraphStyle('DocLabel', parent=styles['Normal'], fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#2D3748"))
        
        story = []
        story.append(Paragraph(f"QR-Code Login Zentrale - Burgdorf {SHOW_YEAR}", title_style))
        story.append(Spacer(1, 10))
        
        # --- FIX: ADMIN DIREKT ZEICHNEN (Nicht im 3er-Raster der Richter!) ---
        story.append(Paragraph("1. Allgemeine Logins und Admins", section_style))
        adm_url = f"{base_url}?view=admin&auth=true&role=Admin{key_param()}"
        
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(adm_url)
        qr.make(fit=True)
        img_pil = qr.make_image(fill_color="black", back_color="white")
        img_buf = BytesIO()
        img_pil.save(img_buf, format="PNG")
        img_buf.seek(0)
        
        # Platziert den Admin zentriert als Einzelelement
        admin_table = Table([[Paragraph("<b>ADMIN MAIN HOME</b>", label_style)], [Image(img_buf, width=90, height=90)]], colWidths=[180])
        admin_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(admin_table)
        story.append(Spacer(1, 15))
        
        # --- AB HIER NUR NOCH DIE LISTEN FÜR STUFENWEISE RASTER SAMMELN ---
        all_qr_items = []
        
        # --- Daten sammeln: ein QR-Code pro Richter (gilt fuer alle Runden) ---
        # Die Runde eines Richters steuert die Ausstellungsleitung im Rundenmanager.
        if df is not None:
            for judge in all_judges(df):
                jp = judge.replace(' ', '+')
                stew_url = f"{base_url}?view=steward&auth=true&role=Steward&judge={jp}{key_param()}"
                all_qr_items.append((f"Steward fuer: {judge}", stew_url, "2. Steward-Links (alle Runden)"))
                j_url = f"{base_url}?view=live-voting&auth=true&role=Richter&judge={jp}{key_param()}"
                all_qr_items.append((f"Richter: {judge}", j_url, "3. Richter-Direkt-Links (alle Runden)"))
        
        # --- Grid im PDF generieren ---
        unique_sections = list(dict.fromkeys([item[2] for item in all_qr_items]))
        for current_section in unique_sections:
            story.append(Paragraph(current_section, section_style))
            story.append(Spacer(1, 4))
            
            section_items = [item for item in all_qr_items if item[2] == current_section]
            cells = []
            
            for label, url, _ in section_items:
                qr = qrcode.QRCode(version=1, box_size=4, border=1)
                qr.add_data(url)
                qr.make(fit=True)
                img_pil = qr.make_image(fill_color="black", back_color="white")
                
                img_buf = BytesIO()
                img_pil.save(img_buf, format="PNG")
                img_buf.seek(0)
                
                rl_img = Image(img_buf, width=90, height=90)
                
                cell_content = [
                    Paragraph(f"<b>{label}</b>", label_style),
                    Spacer(1, 3),
                    rl_img,
                    Spacer(1, 10)
                ]
                cells.append(cell_content)
            
            grid_data = []
            row = []
            for i, cell in enumerate(cells):
                row.append(cell)
                if (i + 1) % 3 == 0 or (i + 1) == len(cells):
                    while len(row) < 3:
                        row.append(Paragraph("", label_style)) # Saubere leere Zelle
                    grid_data.append(row)
                    row = []
            
            if grid_data:
                table_grid = Table(grid_data, colWidths=[180, 180, 180])
                table_grid.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]))
                story.append(table_grid)
                story.append(Spacer(1, 5))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    # ---------------- DYNAMIC DOWNLOAD BUTTON ----------------
    st.write("### 🖨️ Druckansicht & Export")
    try:
        pdf_data = generate_pdf_download(df_full)
        st.download_button(
            label="📄 ALLE QR-Codes (Admins, Stewards & Richter) als PDF herunterladen",
            data=pdf_data,
            file_name=f"Alle_QR_Codes_Burgdorf_{SHOW_YEAR}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Fehler bei der PDF-Erstellung: {e}")
    
    st.divider()

    # Registerkarten für die Übersichtlichkeit (Web-Ansicht)
    tab1, tab2, tab3 = st.tabs(["🤵 Stewards & Admins", "👨‍⚖️ Richter", "📱 Aussteller (Handy)"])
    judges_alle = all_judges(df_full) if df_full is not None else []
    
    if key_required():
        st.success("🔒 Zugriffsschutz aktiv: Die Admin-, Steward- und Richter-QR-Codes enthalten den geheimen Schlüssel. "
                   "Die Aussteller-Codes brauchen keinen.")
    else:
        st.error("⚠️ Kein Zugriffsschutz: In den Streamlit-Secrets fehlt ACCESS_KEY. Die Codes funktionieren zwar, "
                 "aber jeder, der die Adresse kennt, kommt als Admin hinein. Siehe Anleitung (ANLEITUNG_ZUGRIFF.md).")

    # ---------------- TAB 1: STEWARDS & ADMINS ----------------
    with tab1:
        st.subheader("Allgemeine Logins")
        col_adm, _ = st.columns(2)
        with col_adm:
            st.warning("⚙️ ADMIN MAIN HOME")
            adm_url = f"{base_url}?view=admin&auth=true&role=Admin{key_param()}"
            st.image(generate_qr_image(adm_url), width=230)
            st.caption(f"[Link kopieren]({adm_url})")
            
        st.divider()
        
        st.markdown("### 📝 Steward-Links (gelten für alle Runden)")
        st.write("Ein QR-Code pro Richter. Die aktuelle Runde des Richters steuert die Ausstellungsleitung im Rundenmanager.")
        if judges_alle:
            s_cols = st.columns(3)
            for idx, judge in enumerate(judges_alle):
                with s_cols[idx % 3]:
                    st.info(f"Steward für: {judge}")
                    stew_url = f"{base_url}?view=steward&auth=true&role=Steward&judge={judge.replace(' ', '+')}{key_param()}"
                    st.image(generate_qr_image(stew_url), width=200)
                    st.write("---")
        else:
            st.write("Keine Richter gefunden.")
                
    # ---------------- TAB 2: RICHTER ----------------
    with tab2:
        st.subheader("Richter-Direkt-Links (gelten für alle Runden)")
        if judges_alle:
            j_cols = st.columns(3)
            for idx, judge in enumerate(judges_alle):
                with j_cols[idx % 3]:
                    st.success(f"Richter: {judge}")
                    j_url = f"{base_url}?view=live-voting&auth=true&role=Richter&judge={judge.replace(' ', '+')}{key_param()}"
                    st.image(generate_qr_image(j_url), width=200)
                    st.write("---")
        else:
            st.write("Keine Richter gefunden.")
                
    # ---------------- TAB 3: AUSSTELLER ----------------
    with tab3:
        st.subheader("Aussteller-Ansicht (ohne Login)")
        st.write("Ein allgemeiner QR-Code mit Richter-Auswahl und je ein QR-Code pro Richter (z. B. am Richtertisch aufhängen).")
        g_url = f"{base_url}?view=live&embed=true"
        st.info("Allgemein (Richter selbst wählen)")
        st.image(generate_qr_image(g_url), width=230)
        st.caption(f"[Link kopieren]({g_url})")
        st.divider()
        if judges_alle:
            a_cols = st.columns(3)
            for idx, judge in enumerate(judges_alle):
                with a_cols[idx % 3]:
                    st.info(f"Aussteller: {judge}")
                    a_url = f"{base_url}?view=live&embed=true&judge={judge.replace(' ', '+')}"
                    st.image(generate_qr_image(a_url), width=200)
                    st.write("---")

    # --- ZURÜCK NAVI ---
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_qrcode"):
        set_view("Home")
                

# VIEW: NOMINATED CATS (DEIN KOMPLETTES ADMIN-KONTROLLZENTRUM + INTEGRIERTER PDF-DRUCK)
# ==============================================================================
