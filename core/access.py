# -*- coding: utf-8 -*-
"""Zugriffsschutz: geheimer Schluessel (Streamlit-Secrets) fuer QR-/URL-Logins.

In den Streamlit-Secrets steht:   ACCESS_KEY = "ein-langer-zufaelliger-text"
Optional (eigene Passwoerter fuer die Anmeldung per Passwort):
    PW_ADMIN = "..."   PW_STEWARD = "..."   PW_RICHTER = "..."
Ist ACCESS_KEY nicht gesetzt, gilt der alte Zustand (Links mit auth=true funktionieren ohne Schluessel)."""
import hmac
from urllib.parse import quote

import streamlit as st

_DEFAULT_PW = {"Admin": "admin2026", "Steward": "steward2026", "Richter": "judge2026"}


def _secret(name):
    try:
        v = st.secrets.get(name)
    except Exception:
        return ""
    return str(v).strip() if v is not None else ""


def access_key():
    return _secret("ACCESS_KEY")


def key_required():
    return bool(access_key())


def key_valid(value):
    """True, wenn kein Schluessel verlangt wird oder der uebergebene stimmt."""
    k = access_key()
    if not k:
        return True
    return hmac.compare_digest(str(value or "").encode("utf-8"), k.encode("utf-8"))


def key_param():
    """Anhaengsel fuer URLs: '&key=...' (leer, wenn kein Schluessel gesetzt ist)."""
    k = access_key()
    return f"&key={quote(k, safe='')}" if k else ""


def password_for(role):
    return _secret({"Admin": "PW_ADMIN", "Steward": "PW_STEWARD", "Richter": "PW_RICHTER"}[role]) or _DEFAULT_PW[role]


def using_default_passwords():
    return not all(_secret(n) for n in ("PW_ADMIN", "PW_STEWARD", "PW_RICHTER"))
