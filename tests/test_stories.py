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


def test_savings_never_positive_for_vorausschauend_across_presets():
    """Zentraler Befund dieser Demo (siehe README 'Befunde/Korrekturen'): die vorausschauende
    Regel gewinnt in keinem der fünf Presets Gesamtstrecke."""
    for name in C.PRESETS:
        rows = E.sample(_params(name), n_trials=120)
        assert ST.savings_pct(rows) <= 1e-6, name
