"""
Stellplatzdisposition auf dem Hof – interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zusatz zur Yard-Linie (yard-demo): wohin eine ankommende Wechselbrücke stellen, wenn die Reihen im
Ankunftsfeld genestet sind (mehrere Brücken hintereinander, nur von der Gassenseite erreichbar) und
man die Abholzeit vorab kennt? Zeigt, mit einer echten Wegkettenrechnung, ob sich vorausschauendes
Einparken gegenüber "nächster freier Platz" lohnt - und korrigiert damit eine grobe Vorab-Schätzung.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import hst_constants as C
import hst_evaluation as E
import hst_scenario as S
import hst_simulation as SIM
import hst_ui_panel as UI
import hst_visualization as V
from hst_pdf_export import generate_hst_pdf
from hst_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, SETTING_SPECS, sync_query_params

st.set_page_config(page_title="Stellplatzdisposition auf dem Hof - Sebastian Hanisch", layout="wide")

SCENARIO_KEYS = list(SETTING_SPECS)


@st.cache_data(show_spinner=False, max_entries=64)
def _compute_pair(key):
    rows, depth, n_items, window, dwell, sigma, seed = key
    items = S.make_shift(n_items, window, dwell, sigma, seed)
    return SIM.run_pair(items, rows, depth, record_steps=True)


@st.cache_data(show_spinner=False, max_entries=32)
def _compute_h_curve(key):
    rows, depth, n_items, window, dwell, sigma = key
    return E.h_curve(rows, depth, n_items, window, dwell, sigma)


@st.cache_data(show_spinner=False, max_entries=32)
def _compute_sigma_curve(key):
    rows, depth, n_items, window, dwell = key
    return E.sigma_curve(rows, depth, n_items, window, dwell)


@st.cache_data(show_spinner=False, max_entries=64)
def _compute_sample_row(key):
    rows, depth, n_items, window, dwell, sigma, seed = key
    return E.sample_row(E.Params(rows, depth, n_items, window, dwell, sigma), seed)


st.title("🅿️ Stellplatzdisposition: Wohin mit der ankommenden Wechselbrücke?")
st.markdown(
    """
Eine Wechselbrücke kommt im Ankunftsfeld des Hofs an – in welche **Reihe** stellt man sie, wenn die Reihen **genestet** sind (mehrere Brücken hintereinander, nur von der Gassenseite erreichbar, LIFO)
und man die **Abholzeit** vorab kennt? Bei `stapelplanung-demo` und `blockzuweisung-demo` zahlt sich ein Blick auf die Zukunft aus – hier ist das **bewusst ein Gegenbeispiel**: Diese Demo rechnet
mit einer echten **Wegkettenrechnung** nach, ob sich derselbe Gedanke auch beim Einparken lohnt, und korrigiert damit eine grobe Vorab-Schätzung, die "ja" sagte. Das Ergebnis fällt anders aus
(siehe "Wie funktioniert diese Demo?" und "📐 Mathematische Formulierung" weiter unten).
"""
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Offene Fläche": "Der Grenzfall H=1: keine Verdrängung möglich, beide Regeln liefern für jede Instanz exakt denselben Plan.",
    "Leicht genestet": "8 Reihen à 2: die vorausschauende Regel meidet nahe Reihen und zahlt dafür drauf - trotz deutlich weniger Umsetzungen.",
    "Stark genestet, ruhig": "4 Reihen à 4, mäßige Auslastung: der größte gemessene Nachteil der vorausschauenden Regel.",
    "Stark genestet, viel Verkehr": "Wie oben, aber hohe Auslastung: Overflow wird spürbar, der Nachteil der vorausschauenden Regel bleibt.",
    "Überlastet": "Hohe Auslastung bei leichter Nestung: Overflow ist hier der größere Hebel als die Einlagerungsregel.",
}
preset_names = list(C.PRESETS.keys())
for row in (preset_names[:3], preset_names[3:]):
    cols = st.columns(3)
    for col, name in zip(cols, row):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    rows = st.slider("Reihen R", *bounds("rows_slider"), key="rows_slider", help="Zahl der Reihen im Ankunftsfeld; zusammen mit der Reihentiefe H ergibt sich die Kapazität R·H.")
    depth = st.radio("Reihentiefe H", C.DEPTH_LEVELS, key="depth_radio", horizontal=True,
                     help="H=1: offene Fläche, keine Verdrängung möglich (Ergebnis, kein toter Regler - siehe Hauptansicht). H=2..4: genestet, nur von der Gasse zugänglich (LIFO).")
    n_items = st.slider("Ankünfte im Schichtfenster", *bounds("n_items_slider"), key="n_items_slider", help="Zusammen mit Fenster und Standzeit bestimmt das die Auslastung (Faustformel nach Little).")
    window = st.slider("Schichtfenster (h)", *bounds("window_slider"), key="window_slider", help="Länge des Ankunftsfensters; Ankünfte darin gleichverteilt.")
    dwell = st.slider("mittlere Standzeit (min)", *bounds("dwell_slider"), key="dwell_slider", help="Parameter der Exponentialverteilung der Verweildauer (rechtsschief wie in vorab_stellplatz/measure.py).")
    sigma = st.slider("Schätzfehler der Abholzeit σ (%)", *bounds("sigma_slider"), step=C.SIGMA_STEP, key="sigma_slider",
                      help="Wie ungenau die vom vorausschauenden Verfahren gesehene Abholzeit-Schätzung ist (die naive Regel ignoriert die Abholzeit ohnehin). Macht das vorausschauende Verfahren nur "
                           "gleichmäßig teurer, kein Kipppunkt (siehe tools/PRESET_SWEEP.md).")
    seed = st.number_input("Seed", *bounds("seed_input"), key="seed_input", step=1, help="Bestimmt Ankünfte, Standzeiten und den Schätzfehler der Schicht.")
    st.button("🎲 Neue Schicht", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Seed für die Schicht.")

cap = int(rows) * int(depth)
util_est = n_items * dwell / (window * 60.0) / cap if cap else 0.0

sync_query_params({key: st.session_state[key] for key in SCENARIO_KEYS})

key = (int(rows), int(depth), int(n_items), int(window), int(dwell), int(sigma), int(seed))
with st.spinner("Rechne die Schicht mit beiden Regeln..."):
    result = _compute_pair(key)
res_n, res_l = result

# ---------------------------------------------------------------------------------------------------
# Hauptansicht
# ---------------------------------------------------------------------------------------------------
st.markdown("## 🎯 Lohnt sich vorausschauendes Einparken hier?")
st.caption(f"{int(rows)} Reihen à Tiefe {int(depth)} (Kapazität {cap} Plätze); {int(n_items)} Ankünfte im {int(window)}-h-Fenster (Auslastung ~{util_est * 100:.0f} %, grobe Schätzung nach Little); "
           f"Schätzfehler σ = {int(sigma)} %. Angezeigt: Delta = vorausschauend minus nächster freier Platz.")

UI.render_main_metrics(res_n, res_l)

kind, text = E.diagnosis(E.Params(int(rows), int(depth), int(n_items), int(window), int(dwell), int(sigma)), res_n, res_l)
if kind == "null":
    st.info(f"ℹ️ {text}")
elif kind == "look":
    st.success(f"✅ {text}")
elif kind == "overflow":
    st.warning(f"⚠️ {text}")
elif kind == "naiv":
    st.warning(f"⚠️ {text}")
else:
    st.info(f"ℹ️ {text}")

st.markdown("#### 🔍 Blick auf den Hof")
view_policy = st.radio("Regel", list(C.POLICY_KEYS), format_func=C.POLICY_LABELS.get, key="view_radio", horizontal=True)
chosen = res_n if view_policy == C.POLICY_NEAREST else res_l
max_step = max(1, len(chosen.steps))
step_idx = st.slider("Ereignis", 1, max_step, max_step, key="yard_step_slider", help="Schrittweise durch Ankünfte, Abholungen und Umsetzungen dieser Schicht.") - 1
st.plotly_chart(V.yard_figure(int(rows), int(depth), chosen.steps[step_idx].occupancy if chosen.steps else (), f"{C.POLICY_SHORT[view_policy]}: nach Ereignis {step_idx + 1} von {max_step}"),
                width="stretch", key="main_yard_chart")
st.caption("Reihen mit Belegung, vorne (rechts) ist die Gasse - nur der vorderste Platz ist ohne Umsetzen erreichbar.")

pdf_slot = st.container()

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Kernabschnitt
# ---------------------------------------------------------------------------------------------------
st.subheader("📐 Wann lohnt sich vorausschauendes Einparken?")
st.markdown(
    """
Kernfrage dieser Demo: Lohnt sich ein Blick auf die **Abholzeit** beim Einparken, wenn Reihen **genestet** sind? Die vorausschauende Regel meidet Reihen, in denen sie später etwas verdrängen müsste -
das kostet eine längere **Anfahrt** jetzt, spart aber **Umsetzungen** später. Mit der **echten Wegkettenrechnung** (direkte Fahrt zwischen den Reihen, siehe "📐 Mathematische Formulierung") ist eine
Umsetzung so billig, dass sich dieser Umweg in den gemessenen Bedingungen **nicht** auszahlt – anders als die grobe Schätzung eines Vorab-Checks nahelegte (Einzelheiten unten und im README).
"""
)

st.markdown("**H-Kurve: Gesamtstrecke je Auftrag über die Reihentiefe** (Kapazität R·H bleibt fest)")
h_key = (int(rows), int(depth), int(n_items), int(window), int(dwell), int(sigma))
h_points = _compute_h_curve(h_key)
st.plotly_chart(V.h_curve_figure(h_points), width="stretch", key="h_curve_chart")
st.caption(f"Bei H=1 sind beide Regeln gleich (kein Unterschied, {C.H_CURVE_TRIALS} Instanzen je Punkt); ab H=2 kostet die vorausschauende Regel durchgehend mehr, mit wachsendem Abstand bei tieferer Nestung.")

st.markdown("**σ-Kurve: Gesamtstrecke je Auftrag über den Schätzfehler** (bei der eingestellten Reihentiefe)")
sigma_key = (int(rows), int(depth), int(n_items), int(window), int(dwell))
sigma_points = _compute_sigma_curve(sigma_key)
if int(depth) == 1:
    st.info("ℹ️ Bei H=1 gibt es nichts zu schätzen: kein Unterschied zwischen den Regeln, unabhängig von σ.")
else:
    st.plotly_chart(V.sigma_curve_figure(sigma_points), width="stretch", key="sigma_curve_chart")
    st.caption(f"Kein Kipppunkt: die vorausschauende Regel liegt schon bei σ=0 (perfekte Schätzung) über der naiven Regel; ein Schätzfehler macht sie nur gleichmäßig teurer ({C.SIGMA_CURVE_TRIALS} Instanzen je Punkt).")

st.markdown(f"**Stichprobe** ({C.SAMPLE_TRIALS_DEFAULT} andere Schichten mit den eingestellten Reglern, nicht Ihr Seed)")
if st.button(f"📊 Stichprobe rechnen ({C.SAMPLE_TRIALS_DEFAULT} Schichten)", key="sample_button"):
    bar = st.progress(0.0, text="Rechne die Stichprobe...")
    p = E.Params(int(rows), int(depth), int(n_items), int(window), int(dwell), int(sigma))
    rows_done = []
    for i in range(C.SAMPLE_TRIALS_DEFAULT):
        rows_done.append(_compute_sample_row((int(rows), int(depth), int(n_items), int(window), int(dwell), int(sigma), C.SAMPLE_SEED_BASE + i)))
        if (i + 1) % 20 == 0 or i + 1 == C.SAMPLE_TRIALS_DEFAULT:
            bar.progress((i + 1) / C.SAMPLE_TRIALS_DEFAULT, text=f"Schicht {i + 1} von {C.SAMPLE_TRIALS_DEFAULT}")
    bar.empty()
    st.session_state["sample_result"] = (key, tuple(rows_done))

stored_sample = st.session_state.get("sample_result")
sample_rows = stored_sample[1] if stored_sample and stored_sample[0] == key else None
if sample_rows is None:
    st.info("ℹ️ Die Stichprobe ist für diese Einstellungen noch nicht gerechnet: Knopf „Stichprobe rechnen“.")
else:
    v_kind, v_mean, v_se = E.verdict(sample_rows)
    sav = E.savings_pct(sample_rows)
    if v_kind == "unklar":
        st.info(f"ℹ️ Kein klarer Unterschied über die Stichprobe (Delta {v_mean:+.2f} ± {v_se:.2f} m je Auftrag, unter {C.VERDICT_Z:.0f} Standardfehlern).")
    elif v_kind == "besser":
        st.success(f"✅ Vorausschauend spart über die Stichprobe im Mittel **{sav:.1f} %** Gesamtstrecke (klar, Delta {v_mean:+.2f} ± {v_se:.2f} m je Auftrag).")
    else:
        st.warning(f"⚠️ Vorausschauend ist über die Stichprobe im Mittel **{abs(sav):.1f} % teurer** (klar, Delta {v_mean:+.2f} ± {v_se:.2f} m je Auftrag).")
    st.caption(f"Gesamtstrecke je Auftrag über die Stichprobe: naiv {E.mean([r.naiv_total for r in sample_rows]):.1f} m, vorausschauend {E.mean([r.look_total for r in sample_rows]):.1f} m; "
               f"Overflow naiv {E.mean([r.naiv_overflow for r in sample_rows]) * 100:.1f} %, vorausschauend {E.mean([r.look_overflow for r in sample_rows]) * 100:.1f} % der Ankünfte.")

with pdf_slot:
    st.download_button(
        "📄 Ergebnis als PDF herunterladen",
        data=generate_hst_pdf(E.Params(int(rows), int(depth), int(n_items), int(window), int(dwell), int(sigma)), int(seed), res_n, res_l, kind, text),
        file_name="hofstellplatz_ergebnis.pdf", mime="application/pdf", key="primary_pdf_download",
        help="Szenario, Befund dieser Schicht und Kennzahlen je Regel.")

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Verfahrensvergleich
# ---------------------------------------------------------------------------------------------------
with st.expander("🔧 Wie wir das erreichen – Regeln im Vergleich"):
    tabs = st.tabs([C.POLICY_LABELS[k] for k in C.POLICY_KEYS] + ["📊 Vergleich"])
    for tab, k, res in zip(tabs, C.POLICY_KEYS, (res_n, res_l)):
        with tab:
            UI.render_policy_panel(f"tab_{k}", res, step_idx, int(rows), int(depth))
    with tabs[-1]:
        st.plotly_chart(V.comparison_figure(res_n, res_l), width="stretch", key="comparison_chart")
        st.caption("Anfahrt, Umsetzungen, Umsetz-Mehrstrecke und Gesamtstrecke je Auftrag, für die eingestellte Schicht (echte Wegkettenrechnung).")

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        """
**Der Hof.** Im Ankunftsfeld stehen **R Reihen** mit Reihentiefe **H** (H Wechselbrücken hintereinander, **genestet**). Reihe *r* liegt 20 + 15·*r* Meter vom Tor entfernt (Maßstab wie yard-demo).
Nur der **vorderste (gassenseitige) Platz** einer Reihe ist ohne Umsetzen erreichbar - wie beim Stapeln in `stapelplanung-demo`, nur horizontal (Wegfahren) statt vertikal (Kranhub). **H=1** ist der
Grenzfall "offene Fläche": keine Verdrängung möglich, das ist exakt die implizite Annahme des heutigen `yard-demo`-Modells.

**Zwei Regeln.** 🎯 **Nächster freier Platz** ignoriert die Abholzeit, nimmt die nächste Reihe mit Platz. 🔭 **Vorausschauend** bevorzugt eine Reihe, in der niemand Früheres verdrängt wird
(geschätzte Abholzeit ≤ Minimum der Reihe); darunter die "engste" (späteste vorderste Abholzeit), sonst die insgesamt späteste. Holt man einen Auftrag ab, der nicht vorne steht, werden die
davorstehenden (später geparkten) Brücken zuerst per **nächster freier Platz** umgesetzt - für **beide** Regeln dieselbe Umsetz-Regel, damit der Vergleich nur die Einlagerungsentscheidung misst.

**Die echte Wegkettenrechnung.** Alle Reihen liegen entlang desselben Zugangswegs. Eine Umsetzung fährt **direkt** von der alten in die neue Reihe (nicht übers Tor zurück) und wieder zurück, um den
nächsten Blockierer oder den Zielauftrag zu holen - siehe "📐 Mathematische Formulierung". Das ersetzt die grobe Schätzung eines Vorab-Checks (Distanz alte + neue Reihe, als führe jede Fahrt übers
Tor), die den Umsetz-Aufwand deutlich überschätzt hat.

**Befund/Korrektur.** Der Vorab-Check hatte mit der groben Schätzung 12-23 % Ersparnis für die vorausschauende Regel gezeigt. Mit der echten Wegkettenrechnung ist eine Umsetzung so billig, dass sich
der Umweg, den die vorausschauende Regel bei der Einlagerung nimmt, in **keiner** hier gemessenen Bedingung auszahlt (siehe tools/PRESET_SWEEP.md - ein Sweep über R=2..8, H=2..4, Auslastung 50-97 %
findet höchstens -1,4 % "Ersparnis", also durchgehend einen Nachteil). Die naive Regel hat weiterhin deutlich mehr Umsetzungen (2-5×), aber jede einzelne ist real zu billig, damit sich das lohnt.
Bei H=1 bleibt der Nullbefund unverändert - das ist eine strukturelle Eigenschaft (keine Verdrängung möglich), kein Ergebnis der Distanzrechnung.

**Grenzen dieses Modells** (bewusst so gewählt, damit die Aussage ehrlich bleibt): nur eine Reihenrichtung (gassenseitig LIFO), keine Quer- oder Diagonalfahrten; kein exakter Referenzlöser (Optimum mit
Hellsehen) in dieser Version; keine Terminalfahrzeug-Kapazität oder -Wartezeiten (siehe `yard-demo`); keine Wechselbrücken-Typen oder -Maße; Ankünfte und Abholungen unabhängig voneinander; die
Umsetz-Regel ist für beide Verfahren bewusst gleich (nächster freier Platz), damit der Vergleich nur die Einlagerungsentscheidung misst - eine cleverere, für beide Verfahren unterschiedliche
Umsetz-Regel ist nicht ausgeschlossen, aber nicht Teil dieser Version.
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Reihen und Distanz.** Reihen $r \in \{0, \dots, R-1\}$, $\text{dist}(r) = 20 + 15r$ Meter (Basisabstand 20 m, Reihenabstand 15 m). Reihentiefe $H$, Kapazität $R \cdot H$.

**Einlagerung.** Nächster freier Platz: $\arg\min_r \text{dist}(r)$ unter Reihen mit freiem Platz (Tie-Break: kleinster Index). Vorausschauend: unter Reihen mit freiem Platz zuerst die ohne Verdrängung
($\hat p_{\text{item}} \le \min_{o \in \text{Reihe}} \hat p_o$, mit $\hat p$ der - ggf. mit Schätzfehler behafteten - Abholzeit); darunter $\arg\max_r (\text{späteste vorderste } \hat p)$, sonst
kleinste Distanz, dann kleinster Index; ohne verdrängungsfreie Reihe: insgesamt $\arg\max_r$ der spätesten vordersten $\hat p$.

**Echte Wegkette bei Umsetzung.** Beim Abholen eines Auftrags an Reihe $r$, der nicht vorne steht, werden die $k$ davorstehenden Blockierer (Räumreihenfolge: vorderster zuerst) einzeln per nächster
freier Platz in Reihen $n_1, \dots, n_k$ umgesetzt. Die Wegstrecke zwischen zwei Reihen ist $\text{leg}(a, b) = |\text{dist}(a) - \text{dist}(b)|$ (direkte Fahrt entlang des Zugangswegs, nicht übers
Tor). Da das Hoffahrzeug nach jeder Umsetzung zur Reihe $r$ zurückkehren muss (um den nächsten Blockierer bzw. anschließend den Zielauftrag zu holen), ist die Umsetz-Wegkette
$2 \sum_{i=1}^{k} \text{leg}(r, n_i)$ - das ersetzt die grobe Schätzung $\sum_i \bigl(\text{dist}(r) + \text{dist}(n_i)\bigr)$ eines Vorab-Checks.

**Kennzahlen.** Anfahrt je Abholung $= \text{dist}(r)$ der jeweiligen Reihe; Gesamtstrecke je Auftrag $=$ mittlere Anfahrt (auf abgeholte Aufträge normiert) plus Umsetz-Wegkette je Auftrag; Overflow,
wenn bei Ankunft keine Reihe mit freiem Platz existiert.

**Schätzfehler.** $\hat p = p + \varepsilon$, $\varepsilon \sim \mathcal N(0, (\sigma / 100 \cdot \bar d)^2)$ mit $\bar d$ der mittleren Standzeit, eigener Zufallsstrom (unabhängig von Ankunft und
Standzeit, damit dieselbe Instanz bei unterschiedlichem $\sigma$ vergleichbar bleibt). Die naive Regel nutzt $\hat p$ nie.

**Verifikation.** `tests/test_rules.py` prüft die Wegkette an Handbeispielen und gegen vollständiges Durchprobieren auf Kleinstinstanzen; `test_evaluation.py::test_h1_exact_equality` prüft den
H=1-Nullbefund als hart kodierten Regressionstest.

Implementiert in `hst_scenario.py` (Schicht, Schätzfehler), `hst_rules.py` (Regeln, Wegkette), `hst_simulation.py` (Ablauf, Kennzahlen) und `hst_evaluation.py` (Stichprobe, H-Kurve, σ-Kurve, Urteil).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
