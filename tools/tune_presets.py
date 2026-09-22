"""Preset-Abstimmung per Sweep (mit der ECHTEN Wegkettenrechnung aus hst_rules.py/hst_simulation.py,
nicht der groben Schätzung des Vorab-Checks).

Aufruf (im Projektordner): ./venv/Scripts/python.exe tools/tune_presets.py <modus>
  population   Grundgesamtheit (Seeds 100000-100299, wie hst_constants.SAMPLE_SEED_BASE): Kriterien
               aller Presets, Kennzahlen je Regel, Reloc-Faktor, Overflow-Anteil.
  shown        die gezeigte Schicht (Seed aus PRESETS): Kriterien und Lage in der Grundgesamtheit.
  sigma        Sweep über den Schätzfehler sigma (Bedingung "Leicht genestet"): prüft, ob es einen
               Kipppunkt gibt (siehe README "Befunde/Korrekturen") - es gibt keinen, sigma macht die
               vorausschauende Regel nur gleichmäßig teurer.

Grundsätze wie in den anderen Hafen-/Baumbasierte-Demos: den Preset-Seed nicht nach der schönsten
Einzelschicht wählen, sondern prüfen, dass er die Population repräsentiert; deterministisch, ohne
Zeitlimit (reine Python-Simulation, kein Solver)."""
import statistics
import sys

sys.path.insert(0, ".")
import hst_constants as C
import hst_evaluation as E
import hst_stories as ST

NAMES = list(C.PRESETS)
POP_TRIALS = 300


def params(name):
    p = C.PRESETS[name]
    return E.Params(p["rows"], p["depth"], p["n_items"], p["window"], p["dwell"], p["sigma"])


def cmd_population():
    for name in NAMES:
        rows = E.sample(params(name), POP_TRIALS)
        print(f"\n### {name}")
        for ok, text in ST.criteria(name, rows):
            print(("  OK   " if ok else "  FAIL ") + text)
        naiv_total = E.mean([r.naiv_total for r in rows])
        look_total = E.mean([r.look_total for r in rows])
        print(f"    Gesamtstrecke/Auftrag  naiv={naiv_total:7.2f}  look={look_total:7.2f}  savings(look)={ST.savings_pct(rows):6.2f} %")
        print(f"    Reloc-Faktor (naiv/look) {ST.reloc_factor(rows):5.2f}   Overflow naiv={ST.overflow_share(rows, 'naiv') * 100:5.1f} %  look={ST.overflow_share(rows, 'look') * 100:5.1f} %")


def cmd_shown():
    for name in NAMES:
        p = C.PRESETS[name]
        row = E.sample_row(params(name), p["seed"])
        print(f"\n### {name}, Seed {p['seed']}: {'trägt' if ST.holds(name, row) else 'TRÄGT NICHT'}")
        for ok, text in ST.criteria(name, (row,)):
            print(("  OK   " if ok else "  FAIL ") + text)
        pop = E.sample(params(name), POP_TRIALS)
        pop_sav = ST.savings_pct(pop)
        print(f"    savings gezeigt={-((row.look_total - row.naiv_total) / row.naiv_total * 100 if row.naiv_total else 0.0):6.2f} %   savings Population={pop_sav:6.2f} %")


def cmd_sigma():
    p = C.PRESETS["Leicht genestet"]
    base = E.Params(p["rows"], p["depth"], p["n_items"], p["window"], p["dwell"], 0)
    for sg in C.SIGMA_CURVE_POINTS:
        pp = E.Params(base.rows, base.depth, base.n_items, base.window, base.dwell, sg)
        rows = E.sample(pp, 200, base_seed=700000)
        sav = ST.savings_pct(rows)
        print(f"  sigma={sg:4d}%  savings(vorausschauend)={sav:7.2f} %")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "population"
    {"population": cmd_population, "shown": cmd_shown, "sigma": cmd_sigma}.get(mode, lambda: sys.exit(__doc__))()
