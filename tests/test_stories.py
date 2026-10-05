"""Abnahmekriterien der Presets an der Grundgesamtheit (300 Instanzen, wie tools/tune_presets.py)."""
import helpers  # noqa: F401

import hst_constants as C
import hst_evaluation as E
import hst_stories as ST


def _params(name):
    p = C.PRESETS[name]
    return E.Params(p["rows"], p["depth"], p["n_items"], p["window"], p["dwell"], p["sigma"])


def test_all_preset_criteria_hold_on_population():
    for name in C.PRESETS:
        rows = E.sample(_params(name), n_trials=150)
        for ok, text in ST.criteria(name, rows):
            assert ok, f"{name}: {text}"


def test_all_preset_criteria_hold_on_shown_seed():
    for name, values in C.PRESETS.items():
        row = E.sample_row(_params(name), values["seed"])
        assert ST.holds(name, row), name


def test_offene_flaeche_is_exact_not_approximate():
    rows = E.sample(_params("Offene Fläche"), n_trials=80)
    assert all(r.naiv_total == r.look_total for r in rows)


def test_advantage_of_vorausschauend_stays_small_across_presets():
    """Zentraler Befund dieser Demo (siehe README 'Befunde/Korrekturen'): mit der echten Wegkettenrechnung und der engsten
    Passung spart die vorausschauende Regel in keinem der fünf Presets mehr als 5 % Gesamtstrecke, und bei H=4 ist sie klar teurer."""
    for name in C.PRESETS:
        rows = E.sample(_params(name), n_trials=120)
        assert ST.savings_pct(rows) <= 5.0, name
        if C.PRESETS[name]["depth"] == 4:
            assert ST.savings_pct(rows) <= -3.0, name
