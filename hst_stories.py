"""Abnahmekriterien der Presets: an der Grundgesamtheit (Stichprobe, mehrere hundert Instanzen)
UND an der einen gezeigten Schicht (Seed aus hst_constants.PRESETS). Schwellen mit Abstand zu den
gemessenen Werten (siehe tools/PRESET_SWEEP.md) - Muster blz_stories.py/stk_stories.py.

WICHTIG (Befund/Korrektur, siehe README): mit der echten Wegkettenrechnung gewinnt die vorausschauende
Regel in KEINER gemessenen Bedingung Gesamtstrecke - "savings" ist die Ersparnis von vorausschauend
gegen naechster freier Platz und ist hier durchgehend <= 0 (naiv ist gleich gut oder billiger)."""

import hst_evaluation as E


def savings_pct(rows):
    return E.savings_pct(rows)


def reloc_factor(rows):
    naiv = E.mean([r.naiv_reloc for r in rows])
    look = E.mean([r.look_reloc for r in rows])
    return naiv / look if look > 1e-9 else float("inf")


def overflow_share(rows, who="naiv"):
    return E.mean([getattr(r, f"{who}_overflow") for r in rows])


def criteria(name, rows):
    naiv_total = E.mean([r.naiv_total for r in rows])
    look_total = E.mean([r.look_total for r in rows])
    sav = savings_pct(rows)
    rf = reloc_factor(rows)
    of_n = overflow_share(rows, "naiv")

    if name == "Offene Fläche":
        exact = all(abs(r.naiv_total - r.look_total) <= 1e-9 for r in rows)
        return [(exact, f"H=1: naiv und vorausschauend liefern für jede Instanz exakt dieselbe Gesamtstrecke ({naiv_total:.1f} m): {exact}"),
                (of_n <= 0.10, f"Overflow moderat (<= 10 % der Ankünfte): {of_n * 100:.1f} %")]
    if name == "Leicht genestet":
        return [(naiv_total <= 68.0, f"naiv Gesamtstrecke <= 68 m: {naiv_total:.1f}"),
                (sav <= -3.0, f"vorausschauend mindestens 3 % teurer: {sav:.1f} %"),
                (rf >= 3.0, f"naiv mindestens 3x mehr Umsetzungen als vorausschauend: Faktor {rf:.2f}")]
    if name == "Stark genestet, ruhig":
        return [(sav <= -15.0, f"vorausschauend mindestens 15 % teurer (größte gemessene Spanne): {sav:.1f} %"),
                (rf >= 1.3, f"naiv mindestens 1,3x mehr Umsetzungen: Faktor {rf:.2f}")]
    if name == "Stark genestet, viel Verkehr":
        return [(sav <= -8.0, f"vorausschauend mindestens 8 % teurer bei hoher Auslastung: {sav:.1f} %"),
                (of_n >= 0.05, f"spürbarer Overflow bei hoher Auslastung (>= 5 %): {of_n * 100:.1f} %")]
    if name == "Überlastet":
        return [(of_n >= 0.08, f"Overflow dominiert (>= 8 % der Ankünfte): {of_n * 100:.1f} %"),
                (abs(sav) <= 6.0, f"Regel-Unterschied bei Gesamtstrecke klein (|savings| <= 6 %, Overflow trägt mehr): {sav:.1f} %")]
    raise KeyError(name)


def holds(name, row):
    return all(ok for ok, _ in criteria(name, (row,)))
