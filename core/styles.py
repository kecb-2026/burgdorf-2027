# -*- coding: utf-8 -*-
"""Globales CSS der App."""
import streamlit as st


def inject_global_css():
    st.markdown("""
    <style>


	
    @keyframes blinker { 50% { opacity: 0.1; } }
    @keyframes fadeIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }

@keyframes flashGreen {
    0% { background-color: #1a4a9e; }
    50% { background-color: #28a745; }
    100% { background-color: #1a4a9e; }
}

	.voted-flash {
    		animation: flashGreen 2s ease-in-out;
	}
    /* Greift NUR noch auf die Buttons im Home-Menü zu: */
    .home-buttons div.stButton > button {
        width: 100% !important;
        height: 50px !important;
        background-color: #1a4a9e !important; /* Feste blaue Hintergrundfarbe */
        color: white !important; /* Weiße Schrift auf blauem Grund */
    }

    /* Login Container */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        background-color: #f8f9fa;
        border-radius: 20px;
        border: 2px solid #1a4a9e;
        max-width: 400px;
        margin: 5% auto;
    }

    /* Erzeugt einheitliche Höhen für alle Boxen in einer Zeile */
    .grid-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    /* --- STEWARD CARDS STYLES (ORIGINAL WIEDERHERGESTELLT) --- */
    /* Der Kasten umschließt jetzt das Meta-Grid UND die Buttons */
    .steward-card-wrapper {
        background-color: #f8f9fa !important; /* Karte komplett hellgrau */
        border: 1px solid #dcdcdc !important;
        border-radius: 12px !important;
        padding: 16px 16px 12px 16px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    
    .steward-card-wrapper.gerichtet {
        border: 1px dashed #cccccc !important;
        opacity: 0.6 !important;
    }
    
    .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #1a4a9e;
        padding-bottom: 6px;
        margin-bottom: 12px;
    }
    .card-cat-number {
        font-size: 22px !important;
        font-weight: 800;
        color: #1a4a9e;
    }
    .card-meta-main {
        font-size: 15px !important;
        font-weight: 700;
        color: #222;
    }
    .grid-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px 12px;
        margin-bottom: 12px;
    }
    .card-meta-sub {
        font-size: 13px !important;
        color: #555;
    }
    .meta-label {
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        font-size: 11px !important;
        letter-spacing: 0.5px;
    }

    /* --- GLOBALE BUTTONS (DASHBOARD) --- */
    div.stButton > button {
        width: 100% !important;
        height: 50px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        font-size: 12px !important;
        transition: all 0.2s ease;
        margin-bottom: 5px;
        border: 2px solid #1a4a9e !important;
        background-color: #1a4a9e !important;
        color: white !important;
    }


    /* --- BUTTONS SPEZIFISCH IM STEWARD PANEL VERKLEINERN --- */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        height: 35px !important;
        min-height: 35px !important;
        min-width: 100px !important;
        padding: 0px 5px !important;
        font-size: 8px !important;
        line-height: 1 !important;
        border-radius: 8px !important;
    }

    /* --- KEYFRAMES FÜR DAS FARBLICHE PULSIEREN (OHNE TEXT-BLINKEN) --- */
    @keyframes pulseBlue   { 0% { background-color: #007bff; } 50% { background-color: #0044aa; } 100% { background-color: #007bff; } }
    @keyframes pulseOrange { 0% { background-color: #ff9800; } 50% { background-color: #cc6600; } 100% { background-color: #ff9800; } }
    @keyframes pulseGreen  { 0% { background-color: #28a745; } 50% { background-color: #1a662c; } 100% { background-color: #28a745; } }
    @keyframes pulseYellow { 0% { background-color: #ffc107; } 50% { background-color: #cca300; } 100% { background-color: #ffc107; } }

    /* Spalten-spezifische Button-Farben & einheitliche Größen für das Steward-Pult */
    
    /* SPALTE 1: AUFRUFEN -> BLAU */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stButton"] > button {
        background-color: #007bff !important;
        border: none !important;
        color: white !important;
        width: 100% !important;
        height: 35px !important;
    }
    /* Wenn Aktiv: Blau pulsieren */
    .st-blink-btn div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stButton"] > button,
    div:nth-child(1) .st-blink-btn div[data-testid="stButton"] > button {
        animation: pulseBlue 1.5s infinite ease-in-out !important;
        box-shadow: 0 0 12px rgba(0, 123, 255, 0.5) !important;
    }
    
    /* SPALTE 2: WIRD GERICHTET -> ORANGE */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stButton"] > button {
        background-color: #ff9800 !important;
        border: none !important;
        color: white !important;
        width: 100% !important;
        height: 35px !important;
    }
    /* Wenn Aktiv: Orange pulsieren */
    .st-blink-btn div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stButton"] > button,
    div:nth-child(2) .st-blink-btn div[data-testid="stButton"] > button {
        animation: pulseOrange 1.5s infinite ease-in-out !important;
        box-shadow: 0 0 12px rgba(255, 152, 0, 0.5) !important;
    }
    
    /* SPALTE 3: BIV -> GRÜN */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stButton"] > button {
        background-color: #28a745 !important;
        border: none !important;
        color: white !important;
        width: 100% !important;
        height: 35px !important;
    }
    /* Wenn Aktiv: Grün pulsieren */
    .st-blink-btn div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stButton"] > button,
    div:nth-child(3) .st-blink-btn div[data-testid="stButton"] > button {
        animation: pulseGreen 1.5s infinite ease-in-out !important;
        box-shadow: 0 0 12px rgba(40, 167, 69, 0.5) !important;
    }
    
    /* SPALTE 4: NOM -> GELB */
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stButton"] > button {
        background-color: #ffc107 !important;
        border: none !important;
        color: black !important;
        width: 100% !important;
        height: 35px !important;
    }
    /* Wenn Aktiv: Gelb pulsieren */
    .st-blink-btn div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stButton"] > button,
    div:nth-child(4) .st-blink-btn div[data-testid="stButton"] > button {
        animation: pulseYellow 1.5s infinite ease-in-out !important;
        box-shadow: 0 0 12px rgba(255, 193, 7, 0.5) !important;
    }
    
    /* SPALTE 5: GERICHTET -> GRAU (Erledigt braucht kein Blinken) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) div[data-testid="stButton"] > button {
        background-color: #6c757d !important;
        border: none !important;
        color: white !important;
        width: 100% !important;
        height: 35px !important;
    }

    /* Erweiterte Hover Effekte für ein haptisches Feedback */
    div[data-testid="stHorizontalBlock"] > div div[data-testid="stButton"] > button:hover {
        transform: scale(1.02);           /* Button wird beim Drüberfahren minimal größer */
        cursor: pointer;                  /* Mauszeiger wird zur Hand */
        filter: brightness(110%);         /* Macht die Farbe einen Tick leuchtender statt nur dunkler */
        transition: all 0.2s ease-in-out; /* Lässt die Änderung sanft gleiten, nicht hart springen */
    }

    /* Individuelle Anpassung, falls du bei den spezifischen Farben bleiben willst: */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stButton"] > button:hover { background-color: #0069d9 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stButton"] > button:hover { background-color: #e68a00 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stButton"] > button:hover { background-color: #218838 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stButton"] > button:hover { background-color: #e0a800 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) div[data-testid="stButton"] > button:hover { background-color: #5a6268 !important; }

    /* Blinken für aktive Container-Wrapper im Python-Code */
    .button-class button, .st-blink-btn button, .blink-active button {
        animation: blinker 1.3s linear infinite !important;
        box-shadow: 0 0 15px rgba(0,0,0,0.2) !important;
    }


    /* Dashboard & Richter-Layout Styles */
    .judge-header-box { 
        background-color: #1a4a9e; color: white; padding: 8px; border-radius: 10px; text-align: center; 
        font-size: clamp(20px, 2.4vw, 38px) !important; text-transform: uppercase; font-weight: 900;
        line-height: 1.1; word-break: break-word; 
        margin-bottom: 10px; border: 2px solid #0d2a5e; min-height: 110px; height: auto; 
        display: flex; align-items: center; justify-content: center; 
    }
    
    .jh-wrap { container-type: inline-size; width: 100%; margin-bottom: 10px; }
    .jh-box { background-color: #1a4a9e; color: white; border: 2px solid #0d2a5e; border-radius: 10px; box-sizing: border-box;
        height: 104px; padding: 4px 3px; display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; text-transform: uppercase; font-weight: 900; line-height: 1.12; overflow: hidden; }
    .jh-first, .jh-last { font-size: var(--jhfs, 11cqw); white-space: nowrap; max-width: 100%; }
    .jh-last { min-height: 1.12em; }
    .jh-sub { font-size: 7.5cqw; font-weight: 600; text-transform: none; margin-top: 3px; white-space: nowrap; opacity: .95; }

    .class-label-box { 
        background-color: #e9ecef; color: #1a4a9e; padding: 5px; border-radius: 10px; text-align: center; 
        font-size: clamp(14px, 1.3vw, 22px) !important; text-transform: uppercase; font-weight: 900;
        border: 2px solid #1a4a9e; display: flex; align-items: center; justify-content: center; 
        height: 90px; width: 100%; line-height: 1.1; word-break: break-word; 
    }

    .cat-card, .placeholder-box { height: 90px; padding: 5px; border: 2px solid #1a4a9e; text-align: center; background-color: #f0f0f0; border-radius: 14px; margin-bottom: 5px; min-height: 90px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .placeholder-box { height: 90px; border: 1px solid #d1d1d1; background-color: #f2f2f2 !important; color: #999999; }
    .winner-card { height: 90px; border: 1px solid #ff4d4d !important; background-color: #ffcccc !important; color: #b21f2d !important; }
    .cat-number { font-size: 28px !important; font-weight: 900 !important; color: #1a4a9e; line-height: 1.0; }
    .cat-details { font-size: 14px !important; color: #333; font-weight: bold; margin-top: 2px; line-height: 1.1; }

	.cat-card.dash-big { height: auto; min-height: 125px; max-height: none; overflow: visible; box-sizing: border-box; padding: 6px 4px; }
    .cat-card.dash-big .cat-number { font-size: 38px !important; }
    .cat-card.dash-big .cat-details { font-size: 17px !important; white-space: normal; overflow: visible; }
    .cat-card.dash-big .tag { font-weight: 400; padding: 2px 7px; font-size: 15px; }

    /* Richter Initialen Kreise */
    .judge-initials-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 4px;
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px solid #eee;
    }
    .judge-circle {
        width: 24px;
        height: 24px;
        background-color: #008800;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: bold;
        cursor: help;
    }

    .cat-card.bis-card { padding: 2px 4px; justify-content: center; }
    .cat-card.bis-card .bis-top { display: flex; flex-direction: column; align-items: center; gap: 0; width: 100%; }
    .cat-card.bis-card .cat-number { font-size: 32px !important; line-height: 1; }
    .cat-card.bis-card .cat-details { font-size: 14px !important; line-height: 1.1; margin-top: 0; text-align: center; }
    .cat-card.bis-card .judge-initials-container { margin-top: 1px; padding-top: 2px; gap: 3px; }
    .cat-card.bis-card .judge-circle { width: 30px; height: 30px; font-size: 16px; font-weight: 400;}

    /* Overlay als zentrierte Box (80% Größe) */
    .winner-overlay {
        position: fixed;
        top: 10%; left: 10%; 
        width: 80vw; height: 80vh;
        background-color: white;
        z-index: 9999999;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center;
        border-radius: 40px;
        box-shadow: 0px 0px 100px rgba(0,0,0,0.5);
        border: 15px solid #1a4a9e;
        padding: 40px;
        animation: fadeIn 0.5s ease-out;
    }
    .overlay-backdrop {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: rgba(0,0,0,0.7);
        z-index: 9999998;
    }

    /* Titel Anpassungen Overlay */
    .ov-header {
        font-size: 32px !important; font-weight: 600; color: #333;
        text-transform: uppercase;
        border-bottom: 2px solid #ccc; width: 80%;
        padding-bottom: 15px; margin-bottom: 30px;
    }
    .ov-cat-name {
        font-size: 45px !important; font-weight: 900;
        text-transform: uppercase; color: #000;
        margin-bottom: 20px; line-height: 1.1;
        width: 90%; word-wrap: break-word;
    }
    .ov-owner {
        font-size: 30px !important; font-style: italic; color: #444;
    }
    
    /* Klasse für Hauptüberschriften neben dem Logo */
    .header-text {
        text-transform: uppercase !important;
        font-size: 26px !important;
        font-weight: bold;
        color: #1a4a9e;
        margin: 0 !important;
    }
    
    /* Tags */
    .tag-container { margin-top: 4px; display: flex; justify-content: center; flex-wrap: wrap; gap: 3px; }
    .tag { font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; text-transform: uppercase; color: white; }
    .tag-zumrichten { background-color: #007bff; }
    .tag-biv { background-color: #28a745; animation: blinker 1.5s linear infinite; }
    .tag-nom { background-color: #ffc107; color: black; animation: blinker 1s linear infinite; }

    /* --- AB HIER IN DEINEM SKRIPT ERSETZEN --- */
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] div.stButton > button {
        height: 25px !important;
        min-height: 25px !important;
        min-width: 10px !important;
        padding: 0px 5px !important;
        font-size: 8px !important;
        line-height: 1 !important;
        border-radius: 8px !important;
    }
                
    /* SPALTE 1: AUFRUFEN -> BLAU */
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #007bff !important; border: 2px solid #0056b3 !important; color: white !important; }
    
    /* SPALTE 2: WIRD GERICHTET -> ORANGE */
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #ff9800 !important; border: 2px solid #d37e00 !important; color: white !important; }
    
    /* SPALTE 3: BIV -> GRÜN */
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #28a745 !important; border: 2px solid #1e7e34 !important; color: white !important; }
    
    /* SPALTE 4: NOM -> GELB */
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(4) button { background-color: #ffc107 !important; border: 2px solid #d39e00 !important; color: black !important; }
    
    /* SPALTE 5: GERICHTET -> GRAU */
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(5) button { background-color: #6c757d !important; border: 2px solid #545b62 !important; color: white !important; }

    /* Hover Effekte */
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:hover { background-color: #0069d9 !important; }
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover { background-color: #e68a00 !important; }
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(3) button:hover { background-color: #218838 !important; }
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(4) button:hover { background-color: #e0a800 !important; }
    .steward-card-wrapper div[data-testid="stHorizontalBlock"] > div:nth-child(5) button:hover { background-color: #5a6268 !important; }
    
    .tag-wirdgerichtet { background-color: #ff9800 !important; color: white; }


</style>



</style>

    """, unsafe_allow_html=True)
