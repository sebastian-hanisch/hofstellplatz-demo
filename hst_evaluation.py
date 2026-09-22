"""Auswertung: Stichprobe (Grundgesamtheit), H-Kurve (bei fester Kapazität R*H), Kipppunkt-Kurve
über den Schätzfehler sigma, Urteil (gepaarte Differenz, klar ab mehr als VERDICT_Z Standardfehlern)
und die bedingte Meldung der Hauptansicht."""

import math
import statistics
from dataclasses import dataclass

import hst_constants as C
import hst_scenario as S
import hst_simulation as SIM


@dataclass(frozen=True)
class Params:
    rows: int
    depth: int
    n_items: int
    window: int
    dwell: int
    sigma: int


def run_one(p, seed, record_steps=False):
    items = S.make_shift(p.n_items, p.window, p.dwell, p.sigma, seed)
    return SIM.run_pair(items, p.rows, p.depth, record_steps=record_steps)


@dataclass(frozen=True)
class Row:
    seed: int
    naiv_total: float
    look_total: float
    naiv_reloc: float
    look_reloc: float
    naiv_overflow: float
    look_overflow: float


def sample_row(p, seed):
    res_n, res_l = run_one(p, seed)
    return Row(seed, res_n.total_dist_per_item, res_l.total_dist_per_item, res_n.reloc_per_item, res_l.reloc_per_item, res_n.overflow_rate, res_l.overflow_rate)


def sample(p, n_trials=C.SAMPLE_TRIALS_DEFAULT, base_seed=C.SAMPLE_SEED_BASE):
    return tuple(sample_row(p, base_seed + i) for i in range(n_trials))


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def stderr(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return (var / len(xs)) ** 0.5


def paired_diff(rows, field_naiv, field_look):
    return [getattr(r, field_look) - getattr(r, field_naiv) for r in rows]


def savings_pct(rows):
    """Mittlere prozentuale Ersparnis von 'vorausschauend' gegen 'naechster freier Platz' bei der
    Gesamtstrecke je Auftrag (negativ = vorausschauend ist TEURER, siehe README 'Befunde/Korrekturen')."""
    nt = mean([r.naiv_total for r in rows])
    d = mean(paired_diff(rows, "naiv_total", "look_total"))
    return -d / nt * 100 if nt else 0.0


def verdict(rows):
    """('besser' | 'schlechter' | 'unklar', Mittel, Standardfehler) für die Gesamtstrecke je Auftrag."""
    d = paired_diff(rows, "naiv_total", "look_total")
    m, se = mean(d), stderr(d)
    if se == 0.0 or abs(m) <= C.VERDICT_Z * se:
        return "unklar", m, se
    return ("besser" if m < 0 else "schlechter"), m, se


def h_curve(rows, depth_now, n_items, window, dwell, sigma, n_trials=C.H_CURVE_TRIALS):
    """Gesamtstrecke je Auftrag über H = 1..4 bei FESTER Kapazität rows*depth_now (R' je H
    nachgeführt: R' = max(1, round(Kapazität / H)), wie im Vorab-Check)."""
    cap = rows * depth_now
    out = []
    for h in C.DEPTH_LEVELS:
        r = max(1, round(cap / h))
        p = Params(r, h, n_items, window, dwell, sigma)
        rws = sample(p, n_trials, C.H_CURVE_SEED_BASE + h * 100000)
        out.append((h, r, mean([x.naiv_total for x in rws]), mean([x.look_total for x in rws])))
    return out


def sigma_curve(rows, depth, n_items, window, dwell, n_trials=C.SIGMA_CURVE_TRIALS):
    """Gesamtstrecke je Auftrag über den Schätzfehler sigma (naiv ist von sigma unabhängig -
    es sieht die Abholzeit nie; nur die Schätzung des vorausschauenden Verfahrens wird ungenauer)."""
    out = []
    for i, sg in enumerate(C.SIGMA_CURVE_POINTS):
        p = Params(rows, depth, n_items, window, dwell, sg)
        rws = sample(p, n_trials, C.SIGMA_CURVE_SEED_BASE + i * 100000)
        out.append((sg, mean([x.naiv_total for x in rws]), mean([x.look_total for x in rws])))
    return out


def diagnosis(p, res_n, res_l, rows_sample=None):
    """Bedingte Meldung der Hauptansicht: ('kind', text). kind in {'null','overflow','naiv','look','unklar'}."""
    if p.depth == 1:
        return "null", "Offene Fläche (H=1): keine Verdrängung möglich - beide Regeln liefern für jede Instanz exakt denselben Plan, es gibt nichts zu gewinnen."
    overflow_share = max(res_n.overflow_rate, res_l.overflow_rate)
    diff_pct = (res_n.total_dist_per_item - res_l.total_dist_per_item) / res_n.total_dist_per_item * 100 if res_n.total_dist_per_item else 0.0
    if overflow_share >= 0.08:
        return "overflow", f"Overflow ist hier der größere Hebel als die Einlagerungsregel: {overflow_share * 100:.0f} % der Ankünfte finden keinen freien Platz (beide Regeln gleich betroffen, gleiche Gesamtkapazität)."
    if diff_pct <= -3.0:
        return "naiv", f"Die vorausschauende Regel ist in dieser Schicht **{abs(diff_pct):.0f} % teurer**, nicht günstiger: die Umsetzung ist real billig (direkte Fahrt zur nächsten freien Reihe), der Umweg der vorausschauenden Platzwahl lohnt sich nicht."
    if diff_pct >= 3.0:
        return "look", f"Die vorausschauende Regel spart hier **{diff_pct:.0f} %** Gesamtstrecke."
    return "unklar", "Kein klarer Unterschied zwischen den Regeln in dieser Schicht (Delta unter 3 %)."
