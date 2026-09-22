import helpers  # noqa: F401

import hst_evaluation as E
from hst_pdf_export import _clean, generate_hst_pdf


def test_clean_replaces_dangerous_characters():
    assert "–" not in _clean("Anfahrt – Umsetzen")
    assert "€" not in _clean("Preis: 5€")
    assert _clean("Preis: 5€") == "Preis: 5EUR"
    assert _clean("Anfahrt – Umsetzen") == "Anfahrt - Umsetzen"


def test_umlauts_pass_through_unchanged():
    assert _clean("Stellplätze für Wechselbrücken, größtmögliche Genauigkeit") == "Stellplätze für Wechselbrücken, größtmögliche Genauigkeit"


def test_generate_pdf_bytes_nonempty():
    p = E.Params(rows=8, depth=2, n_items=30, window=8, dwell=80, sigma=0)
    res_n, res_l = E.run_one(p, seed=1)
    kind, text = E.diagnosis(p, res_n, res_l)
    pdf_bytes = generate_hst_pdf(p, 1, res_n, res_l, kind, text)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_with_dash_and_euro_in_text_does_not_crash():
    p = E.Params(rows=16, depth=1, n_items=30, window=8, dwell=80, sigma=0)
    res_n, res_l = E.run_one(p, seed=1)
    pdf_bytes = generate_hst_pdf(p, 1, res_n, res_l, "null", "Ein Test – mit Gedankenstrich und 5€ Text")
    assert pdf_bytes[:4] == b"%PDF"
