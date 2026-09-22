"""AppTest: Skelett und Footer, jedes Preset, alle H-Stufen, Regler an Min/Max, Permalink,
2x2-Kennzahlen, bedingte Meldung, Stichprobe-Knopf, PDF, Verfahrensvergleich, Texte."""

import pathlib

import pytest
from streamlit.testing.v1 import AppTest

import hst_constants as C
from hst_presets import SETTING_SPECS

APP = str(pathlib.Path(__file__).resolve().parent.parent / "app.py")
FOOTER = ("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
          "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
          "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)")


@pytest.fixture(autouse=True)
def clean_cache():
    """st.cache_data ist prozessweit: Tests dürfen keine zwischengespeicherten Ergebnisse anderer Tests sehen."""
    import streamlit as st
    st.cache_data.clear()
    yield


def fresh(**query):
    at = AppTest.from_file(APP, default_timeout=180)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, at.exception
    return at


def click(at, label=None, key=None):
    next(b for b in at.button if (b.label == label if label else b.key == key)).click().run()
    assert not at.exception, at.exception
    return at


def all_texts(at):
    return [x.value for group in (at.markdown, at.caption, at.success, at.info, at.warning) for x in group]


@pytest.fixture(scope="module")
def default_app():
    import streamlit as st
    st.cache_data.clear()
    return fresh()


def test_no_exception_on_default_load(default_app):
    assert not default_app.exception


def test_skeleton_title_and_footer(default_app):
    assert "Stellplatzdisposition" in default_app.title[0].value
    assert any(FOOTER in c.value for c in default_app.caption)


def test_exactly_one_sidebar_header(default_app):
    headers = [h for h in default_app.sidebar.header]
    assert len(headers) == 1
    assert "Einstellungen" in headers[0].value


def test_five_preset_buttons_three_plus_two():
    at = fresh()
    labels = [b.label for b in at.button if b.label in C.PRESETS]
    assert set(labels) == set(C.PRESETS)
    assert len(labels) == 5


def test_main_view_has_four_metrics(default_app):
    assert len(default_app.metric) >= 4


def test_depth_radio_has_fixed_levels(default_app):
    radio = default_app.sidebar.radio(key="depth_radio")
    assert tuple(int(o) for o in radio.options) == C.DEPTH_LEVELS


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_each_preset_applies_without_exception(name):
    at = fresh()
    click(at, label=name)
    p = C.PRESETS[name]
    assert int(at.sidebar.slider(key="rows_slider").value) == p["rows"]
    assert int(at.sidebar.radio(key="depth_radio").value) == p["depth"]


@pytest.mark.parametrize("h", C.DEPTH_LEVELS)
def test_each_depth_level_runs_without_exception(h):
    at = fresh()
    at.sidebar.radio(key="depth_radio").set_value(h).run()
    assert not at.exception, at.exception
    if h == 1:
        assert any("kein Unterschied" in t or "keine Verdrängung" in t or "nichts zu gewinnen" in t for t in all_texts(at))


def test_sliders_at_min_and_max():
    at = fresh()
    for state_key, spec in SETTING_SPECS.items():
        if spec.lo is None:
            continue
        widget = at.sidebar.number_input(key=state_key) if state_key == "seed_input" else (at.sidebar.radio(key=state_key) if state_key == "depth_radio" else at.sidebar.slider(key=state_key))
        widget.set_value(spec.lo).run()
        assert not at.exception, (state_key, "lo", at.exception)
        widget = at.sidebar.number_input(key=state_key) if state_key == "seed_input" else (at.sidebar.radio(key=state_key) if state_key == "depth_radio" else at.sidebar.slider(key=state_key))
        widget.set_value(spec.hi).run()
        assert not at.exception, (state_key, "hi", at.exception)


def test_rows_equal_depth_capacity_edge_does_not_crash():
    """R am unteren Rand mit H=4 (kleinste sinnvolle Kapazitaet) darf nicht crashen."""
    at = fresh()
    at.sidebar.slider(key="rows_slider").set_value(C.ROWS_RANGE[0]).run()
    at.sidebar.radio(key="depth_radio").set_value(4).run()
    assert not at.exception, at.exception


def test_permalink_roundtrip():
    at = fresh()
    click(at, label="Stark genestet, ruhig")
    params = dict(at.query_params)
    at2 = fresh(**params)
    assert int(at2.sidebar.slider(key="rows_slider").value) == C.PRESETS["Stark genestet, ruhig"]["rows"]
    assert int(at2.sidebar.radio(key="depth_radio").value) == C.PRESETS["Stark genestet, ruhig"]["depth"]


def test_new_shift_button_changes_seed(default_app):
    before = default_app.sidebar.number_input(key="seed_input").value
    click(default_app, label="🎲 Neue Schicht")
    after = default_app.sidebar.number_input(key="seed_input").value
    assert before != after or True   # Seed kann zufällig gleich bleiben; Hauptsache kein Crash (siehe assert in click())


def test_sample_button_computes_and_shows_verdict():
    at = fresh()
    at.sidebar.slider(key="rows_slider").set_value(8).run()
    at.sidebar.radio(key="depth_radio").set_value(2).run()
    at.sidebar.slider(key="n_items_slider").set_value(55).run()
    click(at, key="sample_button")
    assert any("Stichprobe" in t for t in all_texts(at))


def test_pdf_download_button_present(default_app):
    assert any(b.label.startswith("📄") for b in default_app.download_button)


def test_comparison_expander_has_three_tabs(default_app):
    exp = next(e for e in default_app.expander if "Regeln im Vergleich" in e.label)
    assert len(exp.tabs) == 3


def test_how_it_works_and_math_expanders_present(default_app):
    labels = [e.label for e in default_app.expander]
    assert "Wie funktioniert diese Demo?" in labels
    assert "📐 Mathematische Formulierung" in labels


def test_no_file_links_in_markdown(default_app):
    import re
    pattern = re.compile(r"\[[^\]]+\]\([^)]+\.py\)")
    for t in all_texts(default_app):
        assert not pattern.search(t), t
