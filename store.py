# -*- coding: utf-8 -*-
"""Globaler Speicher (Supabase)."""
import json
import time
from supabase import create_client, Client
import streamlit as st

class GlobalStore:
    def __init__(self):
        # Hier nutzen wir die Werte aus deinen Secrets
        url = st.secrets["NEXT_PUBLIC_SUPABASE_URL"]
        key = st.secrets["NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"]

        self.client: Client = create_client(url, key)
        self.data = {"votes": {}}
        self.active_overlay = None
        self.overlay_start_time = 0

        # NEU: Merker, ob der Stand aus der Datenbank erfolgreich gelesen wurde.
        # Solange das nicht der Fall ist, darf NICHTS in die Datenbank geschrieben
        # werden, sonst würde ein leerer Stand die echten Daten überschreiben.
        self.loaded_ok = False

        # NEU: Hier landet die letzte Fehlermeldung. Die Sidebar zeigt sie rot an.
        self.last_error = None

        self.load_backup()

    # NEU: Kleine Hilfsfunktion, die den Inhalt aus Supabase holt.
    # Load und Save brauchen beide diese Abfrage, darum steht sie einmal hier.
    def _fetch_remote(self):
        res = self.client.table("app_data").select("content").eq("id", 1).execute()
        return res.data[0]["content"] if res.data else {}

    def load_backup(self):
        """Lädt aus Supabase. Bei Fehler bleibt der RAM-Stand unangetastet."""
        try:
            remote = self._fetch_remote()
            if remote:
                self.data = remote
            # NEU: Lesen hat geklappt, also darf später gespeichert werden
            self.loaded_ok = True
            self.last_error = None
        except Exception as e:
            # GEÄNDERT: Vorher wurde bei einem Fehler self.data auf einen leeren
            # Stand gesetzt. Jetzt bleibt der Stand, wie er ist, und der Fehler
            # wird gemerkt (Sidebar) und ins Log geschrieben (Manage app).
            self.last_error = f"Laden fehlgeschlagen: {e}"
            print("[STORE]", self.last_error)

    def save_backup(self):
        """Speichert in Supabase (2 Versuche). Überschreibt die DB NIE,
        solange der DB-Stand nicht erfolgreich gelesen wurde."""

        # NEU: Schutz. Konnte die Datenbank beim App-Start nicht gelesen werden,
        # wird sie jetzt zuerst nachgeladen und mit dem aktuellen Stand im
        # Arbeitsspeicher zusammengeführt (Stimmen werden vereint).
        if not self.loaded_ok:
            try:
                remote = self._fetch_remote()
                merged = dict(remote or {})
                merged_votes = dict(merged.get("votes", {}))
                merged_votes.update(self.data.get("votes", {}))
                merged.update(self.data)
                merged["votes"] = merged_votes
                self.data = merged
                self.loaded_ok = True
            except Exception as e:
                # Datenbank immer noch nicht erreichbar: lieber NICHT speichern
                # als blind überschreiben. Die Sidebar zeigt die Warnung.
                self.last_error = f"Speichern gesperrt (DB nicht lesbar): {e}"
                print("[STORE]", self.last_error)
                return False

        # GEÄNDERT: Vorher gab es einen Versuch, und Fehler wurden mit
        # "except Exception: pass" verschluckt. Jetzt gibt es zwei Versuche,
        # und bei Misserfolg wird der Fehler gemerkt und geloggt.
        # NEU: pandas/numpy-Werte (z. B. int64) in normale Python-Werte umwandeln
        def _plain(o):
            return o.item() if hasattr(o, "item") else str(o)
       # payload = json.loads(json.dumps(self.data, default=_plain))

        for attempt in range(2):
            try:
                payload = json.loads(json.dumps(self.data, default=_plain))
                self.client.table("app_data").upsert({"id": 1, "content": payload}).execute()
                self.last_error = None
                return True

            except Exception as e:
                self.last_error = f"Speichern fehlgeschlagen: {e}"
                print("[STORE]", self.last_error)
                time.sleep(0.3)          # kurze Pause vor dem zweiten Versuch
        return False

    # UNVERÄNDERT: set_data ist genau wie vorher
    def set_data(self, key, field=None, value=None):
        if field is None:
            self.data[key] = value
        else:
            if key not in self.data:
                self.data[key] = {}
            self.data[key][field] = value
        self.save_backup()


@st.cache_resource
def get_store():
    return GlobalStore()
