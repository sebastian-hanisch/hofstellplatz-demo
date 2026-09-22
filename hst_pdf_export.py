"""PDF-Export (fpdf2): Szenario, Kennzahlen, Verfahrensvergleich. Umlaute ä/ö/ü/ß sind mit den
fpdf2-Kernschriften unproblematisch (feedback_fpdf2_umlauts_are_fine); Gedankenstrich "–" und "€"
stürzen ab und werden ersetzt."""

from fpdf import FPDF

_REPLACE = {"–": "-", "—": "-", "€": "EUR", "σ": "sigma", "→": "->", "≤": "<=", "≥": ">="}


def _clean(text):
    for old, new in _REPLACE.items():
        text = text.replace(old, new)
    return text


def generate_hst_pdf(p, seed, res_n, res_l, diag_kind, diag_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _clean("Stellplatzdisposition auf dem Hof - Ergebnis"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _clean(f"Reihen R={p.rows}, Reihentiefe H={p.depth} (Kapazitaet {p.rows * p.depth}), Ankuenfte={p.n_items}, "
                          f"Schichtfenster={p.window} h, mittlere Standzeit={p.dwell} min, Schaetzfehler sigma={p.sigma} %, Seed={seed}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Befund dieser Schicht", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _clean(diag_text))
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Kennzahlen je Regel", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    headers = ["Regel", "Gesamtstrecke/Auftrag (m)", "Anfahrt/Abholung (m)", "Umsetzungen/Auftrag", "Overflow"]
    widths = [55, 45, 40, 35, 20]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, _clean(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 10)
    for label, res in (("Naechster freier Platz", res_n), ("Vorausschauend", res_l)):
        row = [label, f"{res.total_dist_per_item:.1f}", f"{res.mean_retrieval_dist:.1f}", f"{res.reloc_per_item:.2f}", f"{res.overflow}"]
        for val, w in zip(row, widths):
            pdf.cell(w, 7, _clean(val), border=1)
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, _clean("Sebastian Hanisch - Operations Research und Machine Learning. Alle Zahlen aus einer Simulation mit echter Wegkettenrechnung (keine Messung an einem echten Hof)."))
    return bytes(pdf.output())
