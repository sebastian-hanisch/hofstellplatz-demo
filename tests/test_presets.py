import helpers  # noqa: F401

import hst_constants as C
import hst_presets as P


def test_bounds_match_constants():
    assert P.bounds("rows_slider") == C.ROWS_RANGE
    assert P.bounds("depth_radio") == (min(C.DEPTH_LEVELS), max(C.DEPTH_LEVELS))
    assert P.bounds("sigma_slider") == C.SIGMA_RANGE


def test_depth_caster_rejects_non_levels():
    spec = P.SETTING_SPECS["depth_radio"]
    import pytest
    with pytest.raises(ValueError):
        spec.caster(10)
    with pytest.raises(ValueError):
        spec.caster(0)
    assert spec.caster(3) == 3
    assert spec.caster(4) == 4   # muss gueltig sein - kein abgeschnittenes Kandidaten-Intervall
    assert spec.caster("2") == 2
    assert spec.caster(2.7) == 3   # rundet (int(round(...))), schneidet nicht nur ab (int(...))


def test_parse_setting_clamps_and_rounds_step():
    spec = P.SETTING_SPECS["sigma_slider"]
    assert P.parse_setting(spec, "1000") == C.SIGMA_RANGE[1]
    assert P.parse_setting(spec, "-50") == C.SIGMA_RANGE[0]
    assert P.parse_setting(spec, "30") == 25   # rundet auf den naechsten Schritt (0,25,50,...)
    assert P.parse_setting(spec, "40") == 50   # (40-0)/25=1.6 -> rundet auf 2 -> 50 (nicht int()-Abschneiden auf 1 -> 25)


def test_parse_setting_invalid_returns_none():
    spec = P.SETTING_SPECS["rows_slider"]
    assert P.parse_setting(spec, "not-a-number") is None
    assert P.parse_setting(P.SETTING_SPECS["depth_radio"], "7") is None


def test_all_presets_have_every_setting_key():
    for name, values in C.PRESETS.items():
        for field in P.PRESET_STATE_KEYS:
            assert field in values, (name, field)
        assert values["depth"] in C.DEPTH_LEVELS
        assert C.ROWS_RANGE[0] <= values["rows"] <= C.ROWS_RANGE[1]


def test_preset_capacities_are_reasonable():
    """Kapazitaet R*H nicht extrem knapp (Abschnitt 13: realistisch bemessen) - ausser bewusst
    im Preset 'Ueberlastet' (dort ist der Overflow gerade der Punkt)."""
    for name, values in C.PRESETS.items():
        cap = values["rows"] * values["depth"]
        assert cap >= 8
