# -*- coding: utf-8 -*-
"""Ansicht: PDF-Import (abwesende und nominierte Katzen)"""
import re
import pandas as pd
import streamlit as st
from core.config import ROUNDS
from core.data import get_full_label, load_labels
from core.imports import (add_absent, clear_nom, get_absent, get_nom, parse_pdf_numbers,
                          release_absent, set_nom)
from core.rounds import default_round, round_label, tag_of
from core.store import get_store
from core.ui import display_header_with_logo, set_view


def _cat_info(df, nr):
    """(Rasse/Farbe, Name) einer Katze aus dem Excel, oder None wenn unbekannt."""
    m = df[df["KAT_STR"] == str(nr)]
    if m.empty:
        return None
    r = m.iloc[0]
    return get_full_label(r), str(r.get("NAME", "")).strip()


def _read_pdf(upload):
    try:
        return parse_pdf_numbers(upload.getvalue())
    except ImportError:
        st.error("Die Bibliothek **pypdf** fehlt. Bitte in der Datei `requirements.txt` eine Zeile `pypdf` ergänzen und die App neu starten.")
    except Exception as e:
        st.error(f"Das PDF konnte nicht gelesen werden: {e}")
    return None


def render():
    store = get_store()
    display_header_with_logo("📥 PDF-Import")
    df = load_labels()
    if df is None or "KAT_STR" not in df.columns:
        st.error("Die Excel-Daten konnten nicht geladen werden.")
        return

    tab_abs, tab_nom = st.tabs(["🚫 Abwesende Katzen", "⭐ Nominierte Katzen"])

    # ------------------------------------------------------------ ABWESENDE
    with tab_abs:
        st.write("Lade das PDF **«Liste der abwesenden Katzen»** für eine Runde hoch. Jede Runde hat ihre eigene Liste. Erkannt werden alle Zeilen, die nur eine Katalognummer enthalten. Vor dem Übernehmen siehst du eine Vorschau.")
        rounds_abs = sorted(r for r in ROUNDS if f"TAG {r}" in df.columns) or [1]
        dflt_a = default_round(store)
        ra = st.radio("Für welche Runde?", rounds_abs, index=rounds_abs.index(dflt_a) if dflt_a in rounds_abs else 0,
                      format_func=lambda n: round_label(n), horizontal=True, key="imp_abs_round")
        up = st.file_uploader("PDF mit abwesenden Katzen", type=["pdf"], key=f"imp_abs_pdf_{ra}")
        if up is not None:
            res = _read_pdf(up)
            if res:
                nums, date, ignored = res
                cur = get_absent(store, ra)
                rows = []
                for n in nums:
                    info = _cat_info(df, n)
                    status = "bereits abwesend" if n in cur else ("neu" if info else "⚠️ nicht im Excel")
                    rows.append({"Nr.": n, "Rasse / Farbe": info[0] if info else "-", "Name": info[1] if info else "-", "Status": status})
                st.markdown(f"**{len(nums)} Katzen erkannt**" + (f" · Datum im PDF: **{date}**" if date else " · kein Datum im PDF gefunden"))
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                with st.expander(f"Ignorierte Zeilen ({len(ignored)})"):
                    st.write("\n".join(f"- {x}" for x in ignored) or "keine")
                unknown = [r["Nr."] for r in rows if r["Status"].startswith("⚠️")]
                if unknown:
                    st.warning(f"Nicht im Excel und deshalb übersprungen: {', '.join(unknown)}")
                mode = st.radio("Wie übernehmen?", ["Zur bestehenden Liste hinzufügen", "PDF-Einträge ersetzen (frühere PDF-Liste dieser Runde wird gelöscht, manuelle bleiben)"], key=f"imp_abs_mode_{ra}")
                if st.button(f"✅ Abwesende für {round_label(ra)} übernehmen", key=f"imp_abs_go_{ra}", disabled=not nums):
                    ok = [n for n in nums if n not in unknown]
                    add_absent(store, ok, ra, date=date, src="pdf", replace_pdf=mode.startswith("PDF-Einträge"))
                    st.success(f"{len(ok)} Katzen für {round_label(ra)} als abwesend gespeichert.")
                    st.rerun()

        st.divider()
        st.subheader(f"Aktuell abwesend in {round_label(ra)}")
        cur = get_absent(store, ra)
        if not cur:
            st.info("In dieser Runde ist keine Katze als abwesend markiert.")
        for nr in sorted(cur, key=lambda x: int(x) if x.isdigit() else 0):
            info = _cat_info(df, nr)
            meta = cur[nr]
            c1, c2 = st.columns([5, 1], vertical_alignment="center")
            c1.markdown(f"**Nr. {nr}** · {info[0] if info else 'nicht im Excel'} · {info[1] if info else ''} "
                        f"<span style='color:#888'>({meta.get('src','')} {meta.get('date','')})</span>", unsafe_allow_html=True)
            if c2.button("Wieder freigeben", key=f"imp_rel_{ra}_{nr}"):
                release_absent(store, nr, ra)
                st.rerun()
        st.markdown("**Manuell hinzufügen**")
        m1, m2 = st.columns([3, 1], vertical_alignment="bottom")
        man = m1.text_input("Katalognummer", key=f"imp_abs_manual_{ra}", placeholder="z. B. 57")
        if m2.button("Hinzufügen", key=f"imp_abs_manual_btn_{ra}"):
            n = man.strip()
            if not re.fullmatch(r"\d{1,4}", n):
                st.error("Bitte eine Katalognummer eingeben.")
            elif _cat_info(df, str(int(n))) is None:
                st.error(f"Nr. {n} ist nicht im Excel.")
            else:
                add_absent(store, [str(int(n))], ra, src="manuell")
                st.rerun()

    # ------------------------------------------------------------ NOMINIERTE
    with tab_nom:
        st.write("Lade das PDF mit den **nominierten Katzen** einer Runde hoch. Die Liste ersetzt für diese Runde die Spalte SELECTION im Excel (das Excel selbst bleibt unverändert).")
        rounds_avail = sorted(r for r in ROUNDS if f"SELECTION {r}" in df.columns) or [1]
        dflt = default_round(store)
        rn = st.radio("Für welche Runde?", rounds_avail, index=rounds_avail.index(dflt) if dflt in rounds_avail else 0,
                      format_func=lambda n: round_label(n), horizontal=True, key="imp_nom_round")
        tag = tag_of(rn)
        col = f"SELECTION {rn}"
        excel_nrs = None
        info_cur = get_nom(store).get(tag)
        if info_cur:
            st.info(f"Für {round_label(rn)} ist bereits eine importierte Liste aktiv: **{len(info_cur['nrs'])} Katzen** (Datum {info_cur.get('date') or '-'}).")
            if st.button("↩️ Import entfernen (zurück zur Excel-Liste)", key=f"imp_nom_clear_{tag}"):
                clear_nom(store, tag)
                st.rerun()
        up = st.file_uploader("PDF mit nominierten Katzen", type=["pdf"], key=f"imp_nom_pdf_{tag}")
        if up is not None:
            res = _read_pdf(up)
            if res:
                nums, date, ignored = res
                known = [n for n in nums if _cat_info(df, n)]
                unknown = [n for n in nums if n not in known]
                st.markdown(f"**{len(nums)} Katzen erkannt**" + (f" · Datum im PDF: **{date}**" if date else ""))
                orig = set(df.loc[df[col].astype(str).str.strip().str.upper() == "X", "KAT_STR"].astype(str))
                added = sorted(set(known) - orig, key=int)
                removed = sorted(orig - set(known), key=int)
                st.write(f"Vergleich mit der Excel-Liste von {round_label(rn)} ({len(orig)} Katzen): "
                         f"**+{len(added)} neu**, **−{len(removed)} nicht mehr nominiert**.")
                if added: st.caption("Neu: " + ", ".join(added))
                if removed: st.caption("Fallen weg: " + ", ".join(removed))
                if unknown: st.warning(f"Nicht im Excel und deshalb übersprungen: {', '.join(unknown)}")
                rows = [{"Nr.": n, "Rasse / Farbe": _cat_info(df, n)[0], "Name": _cat_info(df, n)[1]} for n in known]
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                with st.expander(f"Ignorierte Zeilen ({len(ignored)})"):
                    st.write("\n".join(f"- {x}" for x in ignored) or "keine")
                if st.button(f"✅ Nominierte für {round_label(rn)} übernehmen", key=f"imp_nom_go_{tag}", disabled=not known):
                    set_nom(store, tag, known, date=date)
                    st.success(f"{len(known)} nominierte Katzen für {round_label(rn)} gespeichert.")
                    st.rerun()

    st.divider()
    if st.button("⬅️ Zurück zum Hauptmenü", key="back_from_import"):
        set_view("Home")
