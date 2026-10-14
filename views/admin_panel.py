# -*- coding: utf-8 -*-
"""Ansicht: Admin_Panel"""
import streamlit as st
import core.backup as backup
from core.access import key_required, using_default_passwords
from core.imports import HANDY_LOCK_KEY, reset_keep_protected
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def render():
    store = get_store()
    display_header_with_logo("⚙️ Admin-Konsole")
    
    # --- ZUGRIFFSSCHUTZ (Status) ---
    if key_required():
        st.success("🔒 Zugriffsschutz aktiv (geheimer Schlüssel in den QR-Links).")
    else:
        st.error("⚠️ Zugriffsschutz NICHT aktiv: ACCESS_KEY fehlt in den Streamlit-Secrets.")
    if using_default_passwords():
        st.warning("Es gelten noch die Standard-Passwörter. Eigene Passwörter: PW_ADMIN, PW_STEWARD, PW_RICHTER in den Secrets setzen.")

    # --- DATENSICHERUNG ---
    st.subheader("💾 Datensicherung")
    st.write("Lädt den gesamten Stand (Stimmen, Status, Importlisten, Einstellungen) als Datei herunter. "
             "Vor jedem Zurücksetzen oder Wiederherstellen legt die App zusätzlich automatisch eine Kopie an.")
    st.download_button("⬇️ Sicherung herunterladen", data=backup.to_json_bytes(store),
                       file_name=backup.file_name(), mime="application/json", key="backup_dl")
    _up = st.file_uploader("Sicherung wiederherstellen (JSON-Datei)", type=["json"], key="backup_up")
    if _up is not None:
        _d, _err = backup.parse_upload(_up.getvalue())
        if _err:
            st.error(_err)
        else:
            st.info(f"Die Datei enthält: {backup.summary(_d)}. Der aktuelle Stand wird dabei ersetzt.")
            _rok = st.checkbox("Ja, aktuellen Stand durch diese Sicherung ersetzen", key="backup_restore_ok")
            if st.button("♻️ Wiederherstellen", disabled=not _rok, key="backup_restore_btn"):
                if backup.restore(store, _d):
                    st.success("Wiederhergestellt. Der vorherige Stand liegt als automatische Kopie bereit.")
                else:
                    st.error("Speichern in der Datenbank fehlgeschlagen. Bitte noch einmal versuchen.")
    _ac = backup.get_auto_copy(store)
    if _ac:
        st.caption(f"Automatische Kopie vom {_ac['time']} ({_ac['reason']}): {backup.summary(_ac['data'])}")
        _c1, _c2 = st.columns(2)
        with _c1:
            st.download_button("⬇️ Automatische Kopie herunterladen",
                               data=__import__("json").dumps(_ac["data"], ensure_ascii=False, indent=1, default=str).encode("utf-8"),
                               file_name="KECB2027_AutoKopie.json", mime="application/json", key="backup_auto_dl")
        with _c2:
            _aok = st.checkbox("Ja, diese Kopie zurückholen", key="backup_auto_ok")
            if st.button("↩️ Automatische Kopie zurückholen", disabled=not _aok, key="backup_auto_btn"):
                backup.restore(store, _ac["data"], reason="Vor Zurückholen der Kopie")
                st.success("Zurückgeholt.")
                st.rerun()
    st.markdown("---")

    _reset_ok = st.checkbox("Ja, wirklich ALLE Stimmen und Status löschen", key="confirm_reset_all")
    _keep_imp = st.checkbox("PDF-Importlisten (Abwesende / Nominierte) behalten", value=True, key="reset_keep_imports")
    if st.button("ALLE DATEN ZURÜCKSETZEN", disabled=not _reset_ok):
        backup.make_auto_copy(store, "Vor dem Zurücksetzen")
        _snap = store.data[backup.SNAP_KEY]
        reset_keep_protected(store, keep=_keep_imp)
        store.data[backup.SNAP_KEY] = _snap
        store.active_overlay = None
        store.save_backup()
        st.success("Speicher geleert! Eine Kopie des alten Stands liegt oben als «Automatische Kopie» bereit.")

    # --- NOTAUSKNOPF: Handy-Ansicht fuer Aussteller sperren ---
    st.markdown("---")
    st.subheader("🛑 Notausknopf Handy-Ansicht")
    st.write("Wenn der Server zu stark belastet wird: Sperrt die Handy-Seite für alle Aussteller. "
             "Sie sehen nur noch einen Hinweis, es werden keine Katzendaten mehr geladen und die Seite "
             "aktualisiert sich nur noch alle 5 Minuten. Richter, Steward und Dashboard sind nicht betroffen.")
    _locked = bool(store.data.get(HANDY_LOCK_KEY, False))
    _new = st.toggle("Handy-Ansicht für Aussteller sperren", value=_locked, key="handy_lock_toggle")
    if _new != _locked:
        store.data[HANDY_LOCK_KEY] = _new
        store.save_backup()
        st.rerun()
    if _locked:
        st.error("🛑 Die Handy-Ansicht ist GESPERRT. Aussteller sehen nur den Hinweis.")
    else:
        st.success("✅ Die Handy-Ansicht ist freigegeben.")

    # --- HIER IST DER NEUE BUTTON SAUBER EINIGERÜCKT ---


    # --- HIER IST DER NEUE BUTTON SAUBER EINIGERÜCKT ---
    st.markdown("---")  # Eine kleine Trennlinie für die Optik
    st.subheader("🔄 Excel-Cache")
    st.write("Die Excel-Datei wird automatisch alle 10 Minuten neu eingelesen. Hier kannst du das Laden sofort erzwingen:")
    
    if st.button("🔥 Excel-Daten JETZT sofort neu einlesen", key="clear_cache_button"):
        st.cache_data.clear()  # Löscht den 10-Minuten-Cache sofort
        st.success("Der Cache wurde geleert! Die Excel-Datei wird beim nächsten Aufruf frisch geladen.")
        st.rerun()
    st.markdown("---")
        
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_admin"):
        set_view("Home")


		
# --- NEUER MENÜPUNKT: JUDGE LIST ---
