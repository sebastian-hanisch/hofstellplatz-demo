"""Konstanten der Stellplatzdisposition-Demo: Maßstab, Regler-Grenzen, Presets, Farben.

Maßstab wie yard-demo (yard_constants.py): 15 m Reihenabstand, 20 m Basisabstand zum Tor. Reihe r
(0-indiziert) liegt bei ROW_DISTANCE(r) Metern vom Tor - siehe row_distance() unten.
"""

# --- Maßstab (fest, kein Regler) ---------------------------------------------------------------
ROW_SPACING_M = 15.0
BASE_DIST_M = 20.0


def row_distance(row_index):
    """Distanz der Reihe vom Tor entlang des Zugangswegs (m)."""
    return BASE_DIST_M + row_index * ROW_SPACING_M


def leg_distance(row_a, row_b):
    """Echte Wegstrecke zwischen zwei Reihen (m): beide liegen entlang desselben Zugangswegs, die
    Fahrt geht direkt von Reihe zu Reihe, nicht über das Tor zurück (siehe README, 'Befunde/Korrekturen':
    das ersetzt die grobe Schätzung Distanz(alt) + Distanz(neu) des Vorab-Checks)."""
    return abs(row_distance(row_a) - row_distance(row_b))


# --- Regler --------------------------------------------------------------------------------------
ROWS_RANGE, ROWS_DEFAULT = (4, 16), 8
DEPTH_LEVELS = (1, 2, 3, 4)
DEPTH_DEFAULT = 2
N_ITEMS_RANGE, N_ITEMS_DEFAULT = (30, 90), 55
WINDOW_RANGE, WINDOW_DEFAULT = (4, 12), 8            # Schichtfenster (h)
DWELL_RANGE, DWELL_DEFAULT = (40, 200), 100           # mittlere Standzeit (min)
SIGMA_RANGE, SIGMA_DEFAULT, SIGMA_STEP = (0, 150), 0, 25   # Schätzfehler der Abholzeit (%); Default 0 (siehe tools/PRESET_SWEEP.md: sigma verschiebt nur, kippt nichts)
SEED_RANGE, SEED_DEFAULT = (0, 9999), 42

MIN_DWELL_MIN = 5.0                  # wie vorab_stellplatz/measure.py: Standzeit mindestens 5 min

# --- Auswertung ------------------------------------------------------------------------------------
SAMPLE_TRIALS_DEFAULT = 300           # Stichprobe (Knopf): wie im Vorab-Check, Rechenzeit im Sekundenbereich
SAMPLE_SEED_BASE = 100000             # eigener Seed-Bereich, nicht der eingestellte Seed
H_CURVE_TRIALS = 150                  # H-Kurve: pro H-Stufe gemittelt (schneller als die volle Stichprobe, live im Kernabschnitt)
H_CURVE_SEED_BASE = 200000
SIGMA_CURVE_TRIALS = 150
SIGMA_CURVE_SEED_BASE = 300000
SIGMA_CURVE_POINTS = (0, 25, 50, 75, 100, 125, 150)
VERDICT_Z = 2.0                      # klar ab mehr als VERDICT_Z Standardfehlern der gepaarten Differenz

# --- Darstellung -----------------------------------------------------------------------------------
COLOR_NAIVE = "#c0392b"
COLOR_LOOKAHEAD = "#2e7d4f"
COLOR_GATE_ACCENT = "#8a94a3"
MARKER_LINE_COLOR = "#808895"
CHART_HEIGHT = 360

POLICY_NEAREST = "naechster"
POLICY_LOOKAHEAD = "vorausschauend"
POLICY_KEYS = (POLICY_NEAREST, POLICY_LOOKAHEAD)
POLICY_LABELS = {POLICY_NEAREST: "🎯 Nächster freier Platz", POLICY_LOOKAHEAD: "🔭 Vorausschauend"}
POLICY_SHORT = {POLICY_NEAREST: "Nächster freier Platz", POLICY_LOOKAHEAD: "Vorausschauend"}
POLICY_DESCRIPTIONS = {
    POLICY_NEAREST: "Die Reihe mit freiem Platz, die dem Tor am nächsten liegt (kleinste Distanz, dann kleinster Reihenindex). Ignoriert die Abholzeit vollständig - die Alltagsregel und "
                     "Referenz aller Deltas; entspricht dem heutigen impliziten yard-demo-Modell bei H=1.",
    POLICY_LOOKAHEAD: "Bevorzugt eine Reihe, in der niemand Früheres verdrängt wird (geschätzte Abholzeit ≤ Minimum der Reihe); darunter die mit der spätesten vordersten Abholzeit (möglichst "
                       "eng); sonst die Reihe mit der insgesamt spätesten vordersten Abholzeit. Nutzt die (mit Schätzfehler behaftete) Abholzeit, um spätere Umsetzungen zu vermeiden.",
}

# --- Presets (5 Stück, 3+2 im Hauptbereich; siehe tools/PRESET_SWEEP.md) -------------------------
# WICHTIG: mit der echten Wegkettenrechnung (AP 0) hält die im Vorab-Check geschätzte 12-23%-Ersparnis
# des vorausschauenden Verfahrens NICHT stand - siehe README "Befunde/Korrekturen". Der Vorab-Check-Preset
# "Unsicherer Blick voraus" entfällt deshalb: ohne anfänglichen Vorteil gibt es keinen Kipppunkt über
# sigma zu zeigen (sigma macht das vorausschauende Verfahren nur gleichmäßig noch teurer, siehe
# tools/PRESET_SWEEP.md) - sigma bleibt als Regler, aber ohne eigenes Preset.
_BASE = dict(rows=ROWS_DEFAULT, depth=DEPTH_DEFAULT, n_items=N_ITEMS_DEFAULT, window=WINDOW_DEFAULT, dwell=DWELL_DEFAULT, sigma=0, seed=SEED_DEFAULT)
_PRESET_SEED = 10   # gemeinsamer Seed für alle Presets (Sweep: 66 von 300 Kandidaten-Seeds erfüllen alle Kriterien beider hochausgelasteten Presets zugleich, siehe tools/PRESET_SWEEP.md)
PRESETS = {
    "Offene Fläche": dict(_BASE, rows=16, depth=1, n_items=55, seed=_PRESET_SEED),
    "Leicht genestet": dict(_BASE, rows=8, depth=2, n_items=55, seed=_PRESET_SEED),
    "Stark genestet, ruhig": dict(_BASE, rows=4, depth=4, n_items=55, seed=_PRESET_SEED),
    "Stark genestet, viel Verkehr": dict(_BASE, rows=4, depth=4, n_items=75, seed=_PRESET_SEED),
    "Überlastet": dict(_BASE, rows=8, depth=2, n_items=75, seed=_PRESET_SEED),
}
