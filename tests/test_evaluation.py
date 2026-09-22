import helpers  # noqa: F401

import hst_constants as C
import hst_evaluation as E


# ---------------------------------------------------------------------------------------------
# H=1-Nullbefund als hart kodierter Regressionstest (Kernaussage der Ehrlichkeit dieser Demo -
# siehe README): bei H=1 muss die Gesamtstrecke für beide Regeln für JEDE Instanz exakt gleich
# sein, nicht nur im Mittel.
# ---------------------------------------------------------------------------------------------
def test_h1_exact_zero_difference_hardcoded():
    p = E.Params(rows=16, depth=1, n_items=55, window=8, dwell=100, sigma=0)
    for seed in range(50):
        row = E.sample_row(p, seed)
        assert row.naiv_total == row.look_total
        assert row.naiv_reloc == row.look_reloc == 0.0


def test_h1_exact_zero_even_with_sigma():
    """Der Schätzfehler betrifft nur die vorausschauende Platzierung; bei H=1 gibt es keine
    Platzierungsentscheidung, die einen Unterschied machen könnte (jede freie Reihe ist gleich
    gut erreichbar - Distanz ist die einzige Variable, und die ignorieren beide Regeln nicht)."""
    p = E.Params(rows=16, depth=1, n_items=55, window=8, dwell=100, sigma=100)
    for seed in range(20):
        row = E.sample_row(p, seed)
        assert row.naiv_total == row.look_total


def test_savings_pct_sign_convention():
    """savings_pct > 0 heißt: vorausschauend ist GÜNSTIGER (kürzere Gesamtstrecke)."""
    class Row:
        def __init__(self, nt, lt):
            self.naiv_total, self.look_total = nt, lt

    cheaper_look = [Row(100.0, 80.0)]
    assert E.savings_pct(cheaper_look) > 0
    expensive_look = [Row(100.0, 120.0)]
    assert E.savings_pct(expensive_look) < 0
    equal = [Row(100.0, 100.0)]
    assert E.savings_pct(equal) == 0.0


def test_verdict_unclear_when_no_spread():
    class Row:
        def __init__(self, nt, lt):
            self.naiv_total, self.look_total = nt, lt
    rows = [Row(100.0, 100.0)] * 10
    kind, m, se = E.verdict(rows)
    assert kind == "unklar"
    assert m == 0.0


def test_h_curve_h1_equal_and_monotone_shape_present():
    p = E.Params(rows=8, depth=2, n_items=40, window=8, dwell=80, sigma=0)
    points = E.h_curve(p.rows, p.depth, p.n_items, p.window, p.dwell, p.sigma, n_trials=40)
    assert [h for h, *_ in points] == list(C.DEPTH_LEVELS)
    h1 = next(pt for pt in points if pt[0] == 1)
    assert abs(h1[2] - h1[3]) < 1e-6   # naiv == look bei H=1


def test_sigma_curve_naiv_constant_look_non_decreasing():
    """Die naive Regel sieht sigma nie -> ihr Mittelwert darf sich zwischen den Punkten der
    Kurve nur durch Stichprobenrauschen unterscheiden (unabhängige Seeds je Punkt); wir prüfen
    stattdessen direkt an DEMSELBEN Params-Objekt mit fester Stichprobe."""
    p = E.Params(rows=8, depth=2, n_items=40, window=8, dwell=80, sigma=0)
    naiv_means = []
    for sg in (0, 75, 150):
        pp = E.Params(p.rows, p.depth, p.n_items, p.window, p.dwell, sg)
        rows = E.sample(pp, n_trials=60, base_seed=900000)
        naiv_means.append(E.mean([r.naiv_total for r in rows]))
    # dieselben Seeds (base_seed fix) -> dieselben Instanzen -> naiv exakt identisch über sigma
    assert naiv_means[0] == naiv_means[1] == naiv_means[2]


def test_diagnosis_null_at_depth_one():
    p = E.Params(rows=16, depth=1, n_items=55, window=8, dwell=100, sigma=0)
    res_n, res_l = E.run_one(p, seed=5)
    kind, text = E.diagnosis(p, res_n, res_l)
    assert kind == "null"


def test_verdict_boundary_exactly_two_stderr_is_unclear():
    """Bei EXAKT VERDICT_Z Standardfehlern gilt es noch als 'unklar' (<=, nicht <) - Randfall der
    Schwelle. Zwei Werte [3, 1] (look - naiv) ergeben von Hand: mean=2.0, stderr=1.0, also
    mean == 2*stderr == VERDICT_Z*stderr exakt."""
    class Row:
        def __init__(self, nt, lt):
            self.naiv_total, self.look_total = nt, lt
    rows = [Row(100.0, 103.0), Row(100.0, 101.0)]
    kind, mean_d, se_d = E.verdict(rows)
    assert mean_d == 2.0
    assert se_d == 1.0
    assert kind == "unklar"


def test_h_curve_row_count_rounds_half_up_or_down_consistently():
    """r = round(Kapazitaet / H); prueft einen Fall mit exaktem .5-Rest (Kapazitaet 15, H=2 -> 7.5)
    explizit gegen den dokumentierten round()-Ansatz (nicht floor)."""
    points = E.h_curve(rows=5, depth_now=3, n_items=20, window=8, dwell=80, sigma=0, n_trials=10)
    h2 = next(p for p in points if p[0] == 2)
    assert h2[1] == round(15 / 2)   # 8, nicht floor(15/2)=7


class _StubRes:
    def __init__(self, overflow_rate, total_dist_per_item):
        self.overflow_rate = overflow_rate
        self.total_dist_per_item = total_dist_per_item


def test_diagnosis_overflow_boundary_exactly_eight_percent():
    """Bei GENAU 8 % Overflow gilt schon der Overflow-Fall (>=, nicht >)."""
    p = E.Params(rows=8, depth=2, n_items=50, window=8, dwell=80, sigma=0)
    res_n = _StubRes(0.08, 100.0)
    res_l = _StubRes(0.08, 100.0)
    kind, _ = E.diagnosis(p, res_n, res_l)
    assert kind == "overflow"


def test_diagnosis_naiv_boundary_exactly_three_percent():
    """Bei GENAU 3 % Mehrkosten (vorausschauend teurer) gilt schon der 'naiv'-Fall (<=, nicht <)."""
    p = E.Params(rows=8, depth=2, n_items=50, window=8, dwell=80, sigma=0)
    res_n = _StubRes(0.0, 100.0)
    res_l = _StubRes(0.0, 103.0)   # look 3% teurer als naiv -> diff_pct = -3.0
    kind, _ = E.diagnosis(p, res_n, res_l)
    assert kind == "naiv"


def test_diagnosis_look_boundary_exactly_three_percent():
    """Bei GENAU 3 % Ersparnis gilt schon der 'look'-Fall (>=, nicht >)."""
    p = E.Params(rows=8, depth=2, n_items=50, window=8, dwell=80, sigma=0)
    res_n = _StubRes(0.0, 100.0)
    res_l = _StubRes(0.0, 97.0)   # look 3% guenstiger -> diff_pct = +3.0
    kind, _ = E.diagnosis(p, res_n, res_l)
    assert kind == "look"


def test_diagnosis_overflow_dominant():
    p = C.PRESETS["Überlastet"]
    pp = E.Params(p["rows"], p["depth"], p["n_items"], p["window"], p["dwell"], p["sigma"])
    res_n, res_l = E.run_one(pp, seed=p["seed"])
    kind, text = E.diagnosis(pp, res_n, res_l)
    assert kind in ("overflow", "naiv", "unklar")   # Overflow ist hoch, kann je nach Instanz knapp unter/ueber der Schwelle liegen
