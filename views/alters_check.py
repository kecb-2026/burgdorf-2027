# -*- coding: utf-8 -*-
"""Ansicht: Alters_Check – Katzen, die am Ausstellungstag noch nicht alt genug sind (Mindestalter 4 Monate)."""

import streamlit as st
from core.age import check, class_age_check
from core.config import SHOW_DATES, MIN_AGE_MONTHS
from core.data import load_labels
from core.ui import display_header_with_logo


def render():
    display_header_with_logo("🎂 Alters-Check")
    df = load_labels()
    if df is None or "GEBURTSDATUM" not in df.columns:
        st.error("Excel-Daten oder Spalte GEBURTSDATUM nicht verfügbar.")
        return
    st.write("Prüft für jede Katze, ob sie am Ausstellungstag das Mindestalter erreicht hat. "
             "Das Mindestalter gilt als erreicht, wenn der Tag nach Ablauf der vollen Monate ab Geburtsdatum liegt "
             "(geboren 09.06. → vier Monate am 09.10.).")
    c1, c2, c3 = st.columns(3)
    d1 = c1.date_input("Ausstellungstag 1", value=SHOW_DATES[0], format="DD.MM.YYYY", key="age_d1")
    d2 = c2.date_input("Ausstellungstag 2", value=SHOW_DATES[1], format="DD.MM.YYYY", key="age_d2")
    months = c3.number_input("Mindestalter (Monate)", min_value=1, max_value=12, value=MIN_AGE_MONTHS, step=1, key="age_m")

    res = check(df, d1, d2, int(months))
    n_bad = int(res["Status"].str.startswith("❌").sum())
    n_half = int(res["Status"].str.startswith("⚠️").sum())
    n_na = int(res["Status"].str.startswith("❓").sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Katzen geprüft", len(res))
    m2.metric("❌ an beiden Tagen zu jung", n_bad)
    m3.metric("⚠️ nur am 2. Tag alt genug", n_half)
    m4.metric("❓ Datum fehlt/ungültig", n_na)

    if n_bad == 0 and n_half == 0 and n_na == 0:
        st.success("✅ Alle Katzen haben das Mindestalter erreicht.")
    show_all = st.checkbox("Alle Katzen anzeigen (nicht nur Problemfälle)", value=False, key="age_all")
    view = res if show_all else res[~res["Status"].str.startswith("✅")]
    if not view.empty:
        def _color(row):
            s = str(row["Status"])
            if s.startswith("❌"):
                return ["background-color:#f8d7da; color:#721c24"] * len(row)
            if s.startswith("⚠️"):
                return ["background-color:#fff3cd; color:#856404"] * len(row)
            if s.startswith("❓"):
                return ["background-color:#e2e3e5; color:#383d41"] * len(row)
            return [""] * len(row)
        st.dataframe(view.style.apply(_color, axis=1), use_container_width=True, hide_index=True)
    st.download_button("Ergebnis als CSV herunterladen", res.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name="alters_check.csv", mime="text/csv")


    # --- ALTER PASST ZUR KLASSE ---
    st.divider()
    st.subheader("🐱 Passt das Alter zur Klasse?")
    st.write("Klasse 12 (Kitten): 4 bis unter 8 Monate. Klasse 11 (Junior): 8 bis unter 12 Monate. "
             "Geprüft wird an beiden Ausstellungstagen. Mit genau 8 Monaten gilt eine Katze als Junior.")
    cres = class_age_check(df, d1, d2)
    if cres.empty:
        st.info("Keine Katzen in den Klassen 11 und 12 gefunden.")
    else:
        c_bad = int(cres["Status"].str.startswith("❌").sum())
        c_half = int(cres["Status"].str.startswith("⚠️").sum())
        c_na = int(cres["Status"].str.startswith("❓").sum())
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Kitten/Junioren geprüft", len(cres))
        k2.metric("❌ passt an keinem Tag", c_bad)
        k3.metric("⚠️ nur an einem Tag", c_half)
        k4.metric("❓ Datum fehlt/ungültig", c_na)
        if c_bad == 0 and c_half == 0 and c_na == 0:
            st.success("✅ Alle Katzen der Klassen 11 und 12 sind im richtigen Altersfenster.")
        else:
            st.dataframe(cres[~cres["Status"].str.startswith("✅")], use_container_width=True, hide_index=True)
