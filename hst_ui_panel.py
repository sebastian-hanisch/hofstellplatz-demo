"""Render-Panel: die 2x2-Kennzahlen der Hauptansicht und ein gemeinsames Panel je Regel (für die
Tabs des Verfahrens-Expanders)."""

import streamlit as st

import hst_constants as C
import hst_visualization as V


def _signed(x, digits=1):
    v = round(x, digits)
    if v == 0:
        v = 0.0
    return f"{v:+.{digits}f}"


def render_main_metrics(res_n, res_l):
    c1, c2, c3, c4 = st.columns(4)
    d_total = res_l.total_dist_per_item - res_n.total_dist_per_item
    d_retr = res_l.mean_retrieval_dist - res_n.mean_retrieval_dist
    d_reloc = res_l.reloc_per_item - res_n.reloc_per_item
    d_overflow = res_l.overflow - res_n.overflow
    c1.metric("Gesamtstrecke je Auftrag", f"{res_l.total_dist_per_item:.1f} m", delta=f"{_signed(d_total)} m", delta_color="inverse", help="Vorausschauend gegen nächster freier Platz; Anfahrt plus Umsetz-Mehrstrecke (echte Wegkettenrechnung).")
    c2.metric("Anfahrt je Abholung", f"{res_l.mean_retrieval_dist:.1f} m", delta=f"{_signed(d_retr)} m", delta_color="inverse", help="Reine Anfahrtsstrecke zur Reihe der Abholung, ohne Umsetzen.")
    c3.metric("Umsetzungen je Auftrag", f"{res_l.reloc_per_item:.2f}", delta=f"{_signed(d_reloc, 2)}", delta_color="inverse", help="Wie oft ein Auftrag beim Abholen eines anderen umgesetzt werden musste (schief verteilt: die meisten Aufträge 0-mal).")
    c4.metric("Overflow-Ereignisse", f"{res_l.overflow}", delta=f"{_signed(d_overflow, 0)}", delta_color="inverse", help="Ankünfte ohne freien Platz (kein Umsetzen kann helfen - die Gesamtkapazität ist erschöpft).")


def render_policy_panel(key_prefix, res, step_idx, n_rows, depth):
    st.markdown(f"**{C.POLICY_LABELS[res.policy]}**")
    st.caption(C.POLICY_DESCRIPTIONS[res.policy])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gesamtstrecke/Auftrag", f"{res.total_dist_per_item:.1f} m")
    c2.metric("Anfahrt/Abholung", f"{res.mean_retrieval_dist:.1f} m")
    c3.metric("Umsetzungen/Auftrag", f"{res.reloc_per_item:.2f}")
    c4.metric("Overflow", f"{res.overflow}")
    if res.steps:
        idx = min(step_idx, len(res.steps) - 1)
        step = res.steps[idx]
        st.plotly_chart(V.yard_figure(n_rows, depth, step.occupancy, f"Nach Ereignis {idx + 1} von {len(res.steps)} ({step.kind})"), width="stretch", key=f"{key_prefix}_yard")
