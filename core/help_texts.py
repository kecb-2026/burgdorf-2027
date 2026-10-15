# -*- coding: utf-8 -*-
"""Anleitungen je Modul fuer die Hilfe-Seite.

Die Standardtexte stehen hier. Im Admin-Bereich der Hilfe-Seite kann jeder Text bearbeitet werden;
die Aenderung wird im Store gespeichert (ueberlebt den Reset) und ersetzt dann den Standardtext.
Format: Markdown (**fett**, - Aufzaehlung)."""

HELP_KEY = "help_texts"   # {modul_key: text}

# (key, Titel, Standardtext) in der Reihenfolge der Hilfe-Seite
DEFAULT_HELP = [
    ("check", "Check (vor der Show)",
     "Prüft Technik und Ausstellung auf einer Seite. Grüner Haken = in Ordnung, Warnung = Knopf führt zur passenden Seite.\n\n"
     "- Vor der Show öffnen und alle Warnungen abarbeiten.\n- Prüft u. a. Mindestalter, Klassen 11/12, Nominations-Verstösse, PDF-Importlisten."),
    ("excel_upload", "Excel-Upload",
     "Lädt die Excel-Datei mit allen Katzen, Nominationen und Richtern hoch.\n\n"
     "- Danach den **Check** ausführen.\n- Ein Backup (Admin-Konsole) vorher herunterladen."),
    ("excel_edit", "Excel Live-Editor",
     "Einzelne Zellen der Excel-Daten direkt in der App korrigieren, ohne neu hochzuladen."),
    ("pdf_import", "PDF-Import (Abwesende / Nominierte)",
     "Liest Listen der Abwesenden und der Nominierten aus einem PDF ein, je Runde getrennt.\n\n"
     "- Der Zeitpunkt des letzten Imports wird gespeichert und im Check angezeigt.\n- Abwesende Katzen werden im Steward-Pult gesperrt."),
    ("richter_liste", "Richter-Liste", "Übersicht, welcher Richter in welcher Runde welche Kategorien richtet."),
    ("nominierte", "Nominierte-Katzen-Liste", "Listen der nominierten Katzen je Runde und Richter. Hier erscheinen auch Klassen-Verstösse."),
    ("labels", "Nomination-Labels-Druck", "Erstellt die Nominations-Etiketten zum Ausdrucken, je Runde ein Reiter."),
    ("qr", "QR-Code-Generator",
     "Erstellt pro Richter einen QR-Code für Steward und Richter sowie die Codes für Publikum-Seiten.\n\n"
     "- Die QR-Links enthalten den Zugangsschlüssel. Wenn du den ACCESS_KEY änderst, müssen die QR-Codes neu gedruckt werden."),
    ("live_admin", "Live-Admin Control",
     "Steuert die Best in Show: Runde und Kategorie verwalten, Klassen für die Richter freigeben, Nominationen und Gewinner zeigen.\n\n"
     "- **Live-Admin ist die bestimmende Instanz**: Richter und BIS-Bildschirm folgen ihm.\n"
     "- Oben die Statuszeile zeigt: was du verwaltest, was die Richter sehen, was das Publikum sieht.\n"
     "- Die Automatik schaltet nach «Gewinner zeigen» zur nächsten Klasse weiter."),
    ("rundenmanager", "Rundenmanager",
     "Legt die Standard-Runde fest und die Runde jedes Richters (Gelb, Grün, Rot). Steuert Dashboard und Steward-Pult.\n\n"
     "- Unabhängig vom Live-Admin: Die BIS kann in einer anderen Runde laufen als das Richten."),
    ("steward", "Steward-Pult",
     "Für die Stewards am Richtertisch: Katzen aufrufen, «Wird gerichtet», «Gerichtet», BIV und NOM setzen.\n\n"
     "- Katzen, die bei einem anderen Richter belegt oder abwesend sind, sind gesperrt."),
    ("voting", "Live-Voting (Richter)", "Hier wählen die Richter in der freigegebenen Klasse ihre Katze und bestätigen. Der Name des Besitzers wird nicht angezeigt."),
    ("moderator", "Moderator",
     "Bildschirm für die Moderation: zeigt das Ergebnis und löst «Gewinner zeigen» aus.\n\n"
     "- Vorzeitig zeigen geht nur mit gesetztem Haken und einer eindeutig führenden Katze."),
    ("dashboard", "Live-Dashboard", "Zeigt je Richter die aufgerufenen Katzen in der Farbe seiner Runde. Für den Katzenaufruf im Saal."),
    ("bis_public", "Best in Show (Public)", "Der Bildschirm fürs Publikum: Nominationen, dann Gewinner mit Ballonen. Folgt dem Live-Admin."),
    ("bis_ablauf", "BIS-Ablauf", "Zeigt dem Publikum die Reihenfolge der Kategorien und die Startzeit der Best in Show."),
    ("admin", "Admin-Konsole (Reset)",
     "Backup herunterladen und zurückspielen, Daten zurücksetzen, Notausknopf, Zugangsstatus.\n\n"
     "- Vor einem Reset wird automatisch eine Kopie gespeichert.\n- Testdaten vor der Show zurücksetzen."),
]


def get_help(store):
    """Liste (key, titel, text) mit eventuell im Store gespeicherten Aenderungen."""
    saved = store.data.get(HELP_KEY)
    saved = saved if isinstance(saved, dict) else {}
    return [(k, t, saved.get(k, d)) for k, t, d in DEFAULT_HELP]


def set_help(store, key, text):
    saved = store.data.get(HELP_KEY)
    saved = dict(saved) if isinstance(saved, dict) else {}
    saved[key] = text
    store.data[HELP_KEY] = saved
    store.save_backup()


def reset_help(store, key):
    saved = store.data.get(HELP_KEY)
    if isinstance(saved, dict) and key in saved:
        saved = dict(saved)
        saved.pop(key)
        store.data[HELP_KEY] = saved
        store.save_backup()
