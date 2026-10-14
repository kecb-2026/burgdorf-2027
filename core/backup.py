# -*- coding: utf-8 -*-
"""Datensicherung: Download, Wiederherstellen und automatische Kopie vor dem Reset."""
import json
import time
from datetime import datetime

SNAP_KEY = "backup_auto"   # {"time": "...", "reason": "...", "data": {...}}  (ueberlebt Reset/Restore)


def _plain(o):
    return o.item() if hasattr(o, "item") else str(o)


def snapshot_data(store):
    """Der gesamte Stand ohne die automatische Kopie selbst."""
    return {k: v for k, v in store.data.items() if k != SNAP_KEY}


def to_json_bytes(store):
    return json.dumps(snapshot_data(store), default=_plain, ensure_ascii=False, indent=1).encode("utf-8")


def file_name():
    return "KECB2027_Sicherung_" + datetime.now().strftime("%Y-%m-%d_%H-%M") + ".json"


def make_auto_copy(store, reason):
    """Legt eine Kopie des aktuellen Stands im Store ab (nur die letzte bleibt erhalten)."""
    data = json.loads(json.dumps(snapshot_data(store), default=_plain))
    store.data[SNAP_KEY] = {"time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"), "reason": reason, "data": data}


def get_auto_copy(store):
    s = store.data.get(SNAP_KEY)
    return s if isinstance(s, dict) and isinstance(s.get("data"), dict) else None


def parse_upload(raw_bytes):
    """Liest eine hochgeladene Sicherung. Gibt (dict, Fehlertext) zurueck."""
    try:
        d = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        return None, f"Datei nicht lesbar: {e}"
    if not isinstance(d, dict):
        return None, "Das ist keine Sicherung dieser App (Inhalt ist kein Objekt)."
    if not d:
        return None, "Die Sicherung ist leer."
    return d, None


def restore(store, data, reason="Vor Wiederherstellung"):
    """Ersetzt den Stand durch `data`. Vorher wird automatisch eine Kopie des alten Stands abgelegt."""
    make_auto_copy(store, reason)
    snap = store.data[SNAP_KEY]
    store.data = {k: v for k, v in data.items() if k != SNAP_KEY}
    store.data[SNAP_KEY] = snap
    store.active_overlay = None
    return store.save_backup()


def summary(data):
    votes = data.get("votes", {})
    return f"{len(votes) if hasattr(votes, '__len__') else 0} Stimmen, {len(data)} Einträge insgesamt"
