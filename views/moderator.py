# -*- coding: utf-8 -*-
"""Ansicht: Moderator"""
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import re
import streamlit as st
import time
from core.config import NO_CLASS_LABEL
from core.data import real_judges, class_mask, get_full_label, load_labels, with_selection
from core.bis import cat_status
import core.autonext as autonext
from core.store import get_store
from core.ui import display_header_with_logo, round_banner


def render():
    store = get_store()
    import html as _html
    st_autorefresh(interval=2000, key="moderator_refresh")
    autonext.process(store)   # faelligen automatischen Klassenwechsel ausfuehren

    _NO_VOTE = ("Keine Wahl", "Keine Wahl/Not chosen yet")

    # --- BEGIN MOD_LOGIC ---
    def _mod_parse_vote(raw):
        """Liefert (katze oder None, status), status = 'none' | 'wählt' | 'bestaerkt'."""
        if isinstance(raw, dict):
            k = raw.get("katze")
            if k is None or str(k) in _NO_VOTE:
                return None, "none"
            return str(k), ("bestaerkt" if raw.get("status") == "bestaerkt" else "wählt")
        if isinstance(raw, str) and raw not in _NO_VOTE:
            return raw, "bestaerkt"  # alte Stimmen, die nur als Text gespeichert wurden
        return None, "none"

    def _mod_summary(votes, prefix, judges, override):
        """Wertet die Runde aus. Es zählen nur bestätigte Stimmen."""
        per_judge = {}
        counts = {}
        for j in judges:
            k, s = _mod_parse_vote(votes.get(prefix + j))
            per_judge[j] = (k, s)
            if s == "bestaerkt":
                counts[k] = counts.get(k, 0) + 1
        n_conf = sum(1 for k, s in per_judge.values() if s == "bestaerkt")
        winner, source, note, revote = None, None, "", []
        if override and override != "Automatisch (Stimmen)":
            winner, source = str(override), "admin"
        elif not judges:
            note = "Keine Richter gefunden."
        elif n_conf < len(judges):
            note = f"Warte auf {len(judges) - n_conf} Richter"
        else:
            top = max(counts.values())
            leaders = [k for k, c in counts.items() if c == top]
            if len(leaders) == 1:
                winner, source = leaders[0], "stimmen"
            else:
                revote = [j for j, (k, s) in per_judge.items() if k not in leaders]
                note = "Gleichstand: " + ", ".join("#" + k for k in sorted(leaders))
        return per_judge, counts, n_conf, winner, source, note, revote
    # --- END MOD_LOGIC ---

    # Der Knopf schreibt NUR, wenn er wirklich gedrückt wird (on_click).
    def _mod_show_winner(tag, cat, label, nr):
        store.data[f"reveal_{tag}_{cat}_{label}"] = True
        store.data[f"winner_reveal_{tag}_{cat}_{label}"] = True
        _df = load_labels()
        if _df is not None:
            _m = _df[_df['KAT_STR'] == str(nr)]
            if not _m.empty:
                store.active_overlay = _m.iloc[0].to_dict()
                store.overlay_start_time = time.time()
        autonext.schedule(store, tag, cat, label)   # nach der Wartezeit zur naechsten Klasse
        store.save_backup()

    def _mod_show_early(tag, cat, label, nr):
        # Gewinner festlegen (damit spaetere Stimmen ihn nicht mehr aendern) und zeigen
        store.data[f"override_{tag}_{cat}_{label}"] = str(nr)
        _mod_show_winner(tag, cat, label, nr)

    def _mod_request_tiebreak(key, judge_names, cats, pre, restart):
        """Stichentscheid: judge_names stimmen nur noch zwischen cats ab.
        restart=True (Richter mit Einzelstimme): ihre bisherige Stimme wird zurueckgesetzt (und gemerkt)."""
        names = [j for j in judge_names if j and j != "--"]
        if not names:
            return
        old = {}
        if restart and isinstance(store.data.get("votes"), dict):
            for j in names:
                if pre + j in store.data["votes"]:
                    old[j] = store.data["votes"].pop(pre + j)
        store.data[key] = {"judges": names, "cats": [str(c) for c in cats], "old": old}
        store.save_backup()

    def _mod_cancel_tiebreak(key, pre):
        tb = store.data.pop(key, None)
        if isinstance(tb, dict) and isinstance(store.data.get("votes"), dict):
            for j in tb.get("judges", []):
                store.data["votes"].pop(pre + j, None)
            for j, v in (tb.get("old") or {}).items():
                store.data["votes"][pre + j] = v
        store.save_backup()

    def _e(x):
        return _html.escape(str(x))

    display_header_with_logo("🎤 Moderator")
    df_full = load_labels()
    if df_full is None:
        st.error("Die Excel-Daten konnten nicht geladen werden.")
        st.stop()

    tag = str(store.data.get("test_live_tag") or store.data.get("admin_selected_day", "Tag 1")).upper()
    df_full = with_selection(df_full, tag)
    round_banner(tag, cat=store.data.get("test_live_cat"))
    st.sidebar.info(f"📅 Aktiver Ausstellungstag: {tag}")

    cat = store.data.get("test_live_cat")
    label = store.data.get("test_live_label")
    if cat is None or not label:
        st.info("⏳ Noch keine Runde freigegeben. Sobald der Admin eine Klasse freischaltet, erscheint sie hier.")
        st.stop()

    _defs = {
        "Adult Male": ([1, 3, 5, 7, 9], "M"), "Adult Female": ([1, 3, 5, 7, 9], "W"),
        "Neuter Male": ([2, 4, 6, 8, 10], "M"), "Neuter Female": ([2, 4, 6, 8, 10], "W"),
        "Junior 8-12 Male": ([11], "M"), "Junior 8-12 Female": ([11], "W"),
        "Kitten 4-8 Male": ([12], "M"), "Kitten 4-8 Female": ([12], "W"),
        NO_CLASS_LABEL: (None, None),   # Kategorie ohne Klassen (Hauskatzen)
    }
    if label not in _defs:
        st.error(f"Unbekannte Klasse: {label}")
        st.stop()
    klassen, geschl = _defs[label]
    _bs = cat_status(store, df_full, int(re.search(r"\d+", tag).group()), cat)
    if _bs["ready"]:
        st.success("✅ BIS bereit: alle Katzen dieser Kategorie in dieser Runde sind gerichtet.")
    else:
        st.warning(f"⏳ BIS noch nicht bereit: {len(_bs['open'])} von {_bs['total']} Katzen offen.")

    r_col = f"RICHTER {tag}"
    if r_col not in df_full.columns:
        st.error(f"Im Excel fehlt die Spalte '{r_col}'.")
        st.stop()

    pool = df_full[
        (df_full['SELECTION'].astype(str).str.strip().str.upper() == 'X')
        & (df_full['KATEGORIE'] == cat)
        & class_mask(df_full, klassen, geschl)
    ]

    votes = store.data.get("votes", {})
    if not isinstance(votes, dict):
        votes = {}
    prefix = f"v_{tag}_{cat}_{label}_"

    # Beteiligt sind alle Richter, die in dieser Runde richten (nicht nur die, die in dieser Klasse/Kategorie
    # eine Katze nominiert haben), plus alle, die schon eine Stimme abgegeben haben.
    _in_round = df_full[df_full[tag].astype(str).str.strip().str.upper() == "X"] \
        if tag in df_full.columns else df_full.iloc[0:0]
    _judge_set = set(real_judges(_in_round[r_col]))
    _judge_set |= set(str(r).strip() for r in pool[r_col].unique() if str(r).strip() not in ("", "nan", "-"))
    for _k in votes:
        if str(_k).startswith(prefix) and _mod_parse_vote(votes[_k])[1] != "none":
            _judge_set.add(str(_k)[len(prefix):])
    _tb_key = f"tiebreak_{tag}_{cat}_{label}"
    _tb = store.data.get(_tb_key) if isinstance(store.data.get(_tb_key), dict) else None
    _regular = set(_judge_set)
    if _tb:
        _judge_set |= set(_tb.get("judges", []))
    judges = sorted(_judge_set)
    override = store.data.get(f"override_{tag}_{cat}_{label}", "Automatisch (Stimmen)")
    per_judge, counts, n_conf, winner, source, note, revote = _mod_summary(votes, prefix, judges, override)
    # Nur EINE Katze nominiert: sie gewinnt automatisch, die Richter haben keine Wahl.
    # Der Gewinner-Knopf ist sofort aktiv, es muss nicht auf Richterstimmen gewartet werden.
    _single = None
    if winner is None and (not override or override == "Automatisch (Stimmen)") and pool['KAT_STR'].astype(str).nunique() == 1:
        _single = str(pool['KAT_STR'].astype(str).iloc[0])
        winner, source, note = _single, "einzige", ""
    winner_revealed = bool(store.data.get(f"winner_reveal_{tag}_{cat}_{label}", False))

    # --- Kopfzeile: aktive Runde ---
    st.markdown(
        f"<div style='background-color:#fff3cd; padding:14px 18px; border-radius:10px; border-left:6px solid #ffc107; margin-bottom:14px;'>"
        f"<div style='font-size:15px; color:#856404;'>AKTIVE RUNDE</div>"
        f"<div style='font-size:28px; font-weight:bold; color:#856404;'>Kategorie {_e(cat)} — {_e(label)}</div>"
        f"<div style='font-size:16px; color:#856404;'>{n_conf} von {len(judges)} Richtern haben bestätigt</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- Ergebnis + ein Knopf ---
    _bsel = lambda suf="": ",".join(
        'html body div[data-testid="stHorizontalBlock"] > div:nth-child(n) .st-key-%s.st-key-%s button%s' % (k, k, suf)
        for k in ("mod_show_winner", "mod_show_winner_early"))
    st.markdown("<style>" +
        _bsel() + "{width:100% !important; min-width:0 !important; height:110px !important; min-height:110px !important; padding:8px 12px !important; "
        "border-radius:18px !important; background-color:#2e9e4f !important; color:#ffffff !important; border:3px solid #1e7a38 !important; "
        "display:flex !important; align-items:center !important; justify-content:center !important; overflow:hidden !important; animation:none !important;}" +
        _bsel(" p") + "{font-size:30px !important; font-weight:900 !important; line-height:1.1 !important; white-space:normal !important; "
        "text-align:center !important; margin:0 !important;}" +
        _bsel(":disabled") + "{opacity:.45 !important;}" +
        "</style>", unsafe_allow_html=True)
    c_res, c_btn = st.columns([1.3, 1])
    with c_res:
        if winner:
            _w = df_full[df_full['KAT_STR'] == str(winner)]
            if not _w.empty:
                _wr = _w.iloc[0]
                w_text = f"{_e(_wr.get('NAME', ''))} · {_e(get_full_label(_wr))}"
            else:
                w_text = ""
            src = ("vom Admin festgelegt" if source == "admin"
                   else "einzige nominierte Katze, keine Abstimmung nötig" if source == "einzige"
                   else f"{counts.get(str(winner), 0)} Stimmen")
            st.markdown(
                f"<div style='background-color:#fff3cd; padding:14px 18px; border-radius:10px; border:3px solid #d4af37;'>"
                f"<div style='font-size:15px; color:#856404;'>ERGEBNIS ({_e(src)})</div>"
                f"<div style='font-size:44px; font-weight:900; color:#b21f2d;'>#{_e(winner)}</div>"
                f"<div style='font-size:18px; color:#333;'>{w_text}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            if note.startswith("Gleichstand"):
                if revote:
                    extra = "Revote durch: " + ", ".join(_e(j) for j in revote)
                else:
                    extra = "Revote oder Los: Der Admin legt den Gewinner fest."
                msg = f"<b>{_e(note)}</b><br>{extra}"
            else:
                msg = _e(note) if note else "Noch kein Ergebnis."
            st.markdown(
                f"<div style='background-color:#f1f3f5; padding:14px 18px; border-radius:10px; border:2px dashed #adb5bd; font-size:20px;'>{msg}</div>",
                unsafe_allow_html=True,
            )
            if note.startswith("Gleichstand") and _tb is None and not winner_revealed:
                _tied = [k for k, c in counts.items() if c == max(counts.values())] if counts else []
                if revote:
                    # 2-2-1: Der Richter mit der Einzelstimme entscheidet zwischen den gleichauf liegenden Katzen
                    st.markdown("<div style='font-size:18px; font-weight:bold; margin-top:12px;'>🗳️ Neuabstimmung durch den Richter mit der Einzelstimme</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:16px;'>{', '.join(_e(j) for j in revote)} wählt neu zwischen {', '.join('#' + _e(c) for c in sorted(_tied))}.</div>", unsafe_allow_html=True)
                    st.button("Neuabstimmung starten", key=f"mod_rv_go_{tag}_{cat}_{label}", on_click=_mod_request_tiebreak,
                              args=(_tb_key, list(revote), _tied, prefix, True))
                else:
                    # z. B. 2-2 oder 3-3: keine Einzelstimme -> zusaetzlicher Richter ausserhalb der Runde
                    _all_j = set()
                    for _n in (1, 2, 3):
                        _c = f"RICHTER TAG {_n}"
                        if _c in df_full.columns:
                            _all_j |= set(real_judges(df_full[_c]))
                    _cands = sorted(_all_j - _regular)
                    st.markdown("<div style='font-size:18px; font-weight:bold; margin-top:12px;'>🗳️ Stichentscheid durch zusätzlichen Richter</div>", unsafe_allow_html=True)
                    if _cands:
                        _pick = st.selectbox("Richter für den Stichentscheid:", ["--"] + _cands, key=f"mod_tb_pick_{tag}_{cat}_{label}")
                        st.button("Stichentscheid anfordern", key=f"mod_tb_go_{tag}_{cat}_{label}",
                                  disabled=(_pick == "--"), on_click=_mod_request_tiebreak, args=(_tb_key, [_pick], _tied, prefix, False))
                    else:
                        st.info("Es gibt keinen weiteren Richter ausserhalb dieser Runde.")
            if _tb is not None and not winner_revealed:
                _what = "Neuabstimmung" if _tb.get("old") else "Stichentscheid"
                st.markdown(f"<div style='font-size:16px; margin-top:10px;'>🗳️ {_what} läuft: <b>{', '.join(_e(j) for j in _tb['judges'])}</b> wählt zwischen {', '.join('#' + _e(c) for c in _tb['cats'])}.</div>", unsafe_allow_html=True)
                st.button(f"{_what} zurücknehmen", key=f"mod_tb_cancel_{tag}_{cat}_{label}",
                          on_click=_mod_cancel_tiebreak, args=(_tb_key, prefix))
    with c_btn:
        st.button(
            "🏆 OVERLAY NOCHMALS ZEIGEN" if winner_revealed else "🏆 GEWINNER ZEIGEN",
            key="mod_show_winner",
            disabled=(winner is None),
            on_click=_mod_show_early if source == "einzige" else _mod_show_winner,   # einzige Katze: als Gewinner festschreiben
            args=(tag, cat, label, winner),
            use_container_width=True,
        )
        if winner_revealed:
            st.caption("✅ Gewinner ist für Richter und BIS-Screen freigegeben.")

        # --- Zweiter Knopf: vorzeitig zeigen, wenn noch nicht alle bestätigt haben ---
        _early = None
        _show_early = winner is None and not winner_revealed and n_conf < len(judges)
        if _show_early and counts:
            _top = max(counts.values())
            _lead = [k for k, c in counts.items() if c == _top]
            if len(_lead) == 1:
                _early = _lead[0]
        if _show_early:
            if _early is not None:
                st.markdown(f"<div style='font-size:15px; color:#856404; margin-top:10px;'>Vorläufig führt <b>#{_e(_early)}</b> mit {counts[_early]} von {n_conf} bestätigten Stimmen ({len(judges) - n_conf} Richter fehlen noch).</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:15px; color:#856404; margin-top:10px;'>Vorzeitiges Zeigen ist möglich, sobald es eine eindeutig führende Katze gibt.</div>", unsafe_allow_html=True)
            _ok = st.checkbox("Ich weiss: Es haben noch nicht alle bestätigt. Gewinner trotzdem zeigen.", key="mod_early_ok")
            st.button(
                "⚡ GEWINNER JETZT ZEIGEN",
                key="mod_show_winner_early",
                disabled=(not _ok) or (_early is None),
                on_click=_mod_show_early,
                args=(tag, cat, label, _early),
                use_container_width=True,
            )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # --- Links: nominierte Katzen / Rechts: Richter ---
    c_cats, c_judges = st.columns([1.2, 1])

    with c_cats:
        st.markdown("### Nominierte Katzen")
        if pool.empty:
            st.info("Für diese Klasse sind keine Katzen nominiert.")
        rows = [r for _, r in pool.iterrows()]
        rows.sort(key=lambda r: (int(str(r['KAT_STR'])) if str(r['KAT_STR']).isdigit() else 99999, str(r['KAT_STR'])))
        for r in rows:
            nr = str(r['KAT_STR'])
            geb_cols = [c for c in r.index if "GEB" in str(c)]
            geb = r[geb_cols[0]] if geb_cols else "N/A"
            if isinstance(geb, pd.Timestamp):
                geb = geb.strftime('%d.%m.%Y')
            elif pd.isna(geb) or str(geb).strip().lower() == "nan":
                geb = "N/A"
            nom = r.get(r_col, '-')
            if pd.isna(nom) or str(nom).strip().lower() in ("nan", ""):
                nom = "-"
            is_win = winner_revealed and winner is not None and nr == str(winner)
            bg = "#ffcccc" if is_win else "#ffffff"
            bd = "#ff4d4d" if is_win else "#1a4a9e"
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:14px; border:2px solid {bd}; background:{bg}; border-radius:10px; padding:10px 14px; margin-bottom:8px;'>"
                f"<div style='font-size:34px; font-weight:900; color:#1a4a9e; min-width:70px;'>{_e(nr)}</div>"
                f"<div style='flex:1;'>"
                f"<div style='font-size:18px; font-weight:bold;'>{_e(r.get('NAME', ''))}</div>"
                f"<div style='font-size:15px;'>{_e(get_full_label(r))} · {_e(r.get('GESCHLECHT', ''))}, *{_e(geb)}</div>"
                f"<div style='font-size:14px; color:#666;'>Nominiert von {_e(nom)}</div>"
                f"</div>"
                f"<div style='font-size:22px; font-weight:bold; text-align:right;'>{counts.get(nr, 0)} ✔</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with c_judges:
        st.markdown("### Richter")
        def _jcard(name, nrtxt, txt, bg):
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:12px; background:{bg}; border-radius:10px; padding:10px 14px; margin-bottom:8px;'>"
                f"<div style='flex:1;'>"
                f"<div style='font-size:18px; font-weight:bold;'>{_e(name)}</div>"
                f"<div style='font-size:14px;'>{txt}</div>"
                f"</div>"
                f"<div style='font-size:26px; font-weight:900; color:#1a4a9e;'>{nrtxt}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        for j in judges:
            k, s = per_judge[j]
            if s == "bestaerkt":
                bg, txt, nrtxt = "#c8e6c9", "✅ bestätigt", f"#{_e(k)}"
            elif s == "wählt":
                bg, txt, nrtxt = "#ffe0b2", "✏️ wählt noch", f"#{_e(k)}"
            else:
                bg, txt, nrtxt = "#e9ecef", "⏳ noch keine Wahl", "–"
            if _tb and j in _tb.get("judges", []):
                _o = (_tb.get("old") or {}).get(j)
                if _o is not None:
                    # ursprüngliche Stimme bleibt als normale Karte stehen
                    _okat = _mod_parse_vote(_o)[0]
                    _jcard(j, f"#{_e(_okat)}", "✅ bestätigt", "#c8e6c9")
                if s == "bestaerkt":
                    bg = "#f5b301"
                _jcard(f"{j} (Stichentscheid)", nrtxt, txt, bg)
            else:
                _jcard(j, nrtxt, txt, bg)

