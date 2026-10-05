"""Preset-Abstimmung per Sweep (mit der ECHTEN Wegkettenrechnung aus hst_rules.py/hst_simulation.py,
nicht der groben Schätzung des Vorab-Checks).

Aufruf (im Projektordner): ./venv/Scripts/python.exe tools/tune_presets.py <modus>
  population   Grundgesamtheit (Seeds 100000-100299, wie hst_constants.SAMPLE_SEED_BASE): Kriterien
               aller Presets, Kennzahlen je Regel, Reloc-Faktor, Overflow-Anteil.
  shown        die gezeigte Schicht (Seed aus PRESETS): Kriterien und Lage in der Grundgesamtheit.
  sigma        Sweep über den Schätzfehler sigma (Bedingungen "Leicht genestet" und "Überlastet", je 300
               Instanzen): "Leicht genestet" fällt monoton, bei "Überlastet" kippt der kleine Vorteil bei
               sigma = 25 % (siehe README "Befunde/Korrekturen").
  conditions   die sechs Bedingungen des Vorab-Checks (H=1/2/4, mittel/hoch, Kapazität 16, 300 Instanzen).
  sweep        breiter Sweep R = 2..8, H = 2..4, Auslastung 50-97 % (126 Zellen je 300 Instanzen, sigma = 0;
               rund 10 Minuten): Zahl der Zellen mit klarem Vorteil / ohne klaren Unterschied / klarem Nachteil.

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
    for name in ("Leicht genestet", "Überlastet"):
        p = C.PRESETS[name]
        print(f"### {name}")
        for sg in C.SIGMA_CURVE_POINTS:
            pp = E.Params(p["rows"], p["depth"], p["n_items"], p["window"], p["dwell"], sg)
            rows = E.sample(pp, POP_TRIALS)
            print(f"  sigma={sg:4d}%  savings(vorausschauend)={ST.savings_pct(rows):7.2f} %  ({E.verdict(rows)[0]})")


def cmd_conditions():
    for h, r in ((1, 16), (2, 8), (4, 4)):
        for label, n in (("mittel", 55), ("hoch", 75)):
            rows = E.sample(E.Params(r, h, n, C.WINDOW_DEFAULT, C.DWELL_DEFAULT, 0), POP_TRIALS)
            print(f"H={h}, {label:6s}  naiv={E.mean([x.naiv_total for x in rows]):6.1f} m  look={E.mean([x.look_total for x in rows]):6.1f} m  "
                  f"savings={ST.savings_pct(rows):6.1f} %  ({E.verdict(rows)[0]})")


def cmd_sweep():
    cells = []
    for r in range(2, 9):
        for h in (2, 3, 4):
            for util in (0.5, 0.6, 0.7, 0.8, 0.9, 0.97):
                # mittlere Belegung = n * Standzeit / Fenster; Auslastung = Belegung / Kapazität
                n = max(2, round(util * r * h * C.WINDOW_DEFAULT * 60 / C.DWELL_DEFAULT))
                rows = E.sample(E.Params(r, h, n, C.WINDOW_DEFAULT, C.DWELL_DEFAULT, 0), POP_TRIALS)
                cells.append((r, h, util, n, ST.savings_pct(rows), ST.reloc_factor(rows), E.verdict(rows)[0]))
    verdicts = {v: sum(1 for c in cells if c[6] == v) for v in ("besser", "unklar", "schlechter")}
    print(f"{len(cells)} Zellen: {verdicts}")
    for h in (2, 3, 4):
        sv = [c[4] for c in cells if c[1] == h]
        print(f"  H={h}: savings {min(sv):.1f} % bis {max(sv):.1f} %")
    finite = [c[5] for c in cells if c[5] != float("inf")]
    print(f"  Umsetz-Faktor naiv/vorausschauend {min(finite):.1f} bis {max(finite):.1f}")
    print("  klar günstiger:", [(c[0], c[1], c[2], round(c[4], 1)) for c in cells if c[6] == "besser"])
    print("  schlechteste Zelle:", min(cells, key=lambda c: c[4]))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "population"
    {"population": cmd_population, "shown": cmd_shown, "sigma": cmd_sigma, "conditions": cmd_conditions, "sweep": cmd_sweep}.get(mode, lambda: sys.exit(__doc__))()
