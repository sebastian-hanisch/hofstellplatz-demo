import helpers

import hst_constants as C
import hst_rules as R
import hst_scenario as S
import hst_simulation as SIM


def _item(idx, arrival, pickup, pickup_est=None):
    return S.Item(idx=idx, arrival=arrival, pickup=pickup, pickup_est=pickup if pickup_est is None else pickup_est, row=-1)


# ---------------------------------------------------------------------------------------------
# Handbeispiel (siehe tools/PRESET_SWEEP.md-Doku im Modul-Docstring von hst_rules.py): von Hand
# durchgerechnete Wegkette mit einer echten Umsetzung UND einer Selbst-Umsetzung (dieselbe Reihe).
# ---------------------------------------------------------------------------------------------
def test_hand_example_relocation_chain():
    # Q (tief, spaete Abholung), P (vorne, frueh - sauber abholbar), dann A/B in Reihe 1.
    items = [
        _item(0, arrival=0.0, pickup=1000.0),     # Q -> Reihe 0 (tief)
        _item(1, arrival=0.1, pickup=5.0),        # P -> Reihe 0 (vorne), zuerst abgeholt
        _item(2, arrival=0.2, pickup=50.0),       # A -> Reihe 1 (tief), Reihe 0 ist voll
        _item(3, arrival=0.3, pickup=2000.0),     # B -> Reihe 1 (vorne)
    ]
    res = SIM.simulate(items, n_rows=2, depth=2, policy=C.POLICY_NEAREST, record_steps=False)

    dist0, dist1 = C.row_distance(0), C.row_distance(1)
    # P (frontmost) sauber abholbar: keine Umsetzung. A blockiert von B: B -> Reihe 0 (naeher, dist0 < dist1).
    # Q blockiert von B (das jetzt in Reihe 0 vor Q steht): B -> Reihe 0 (dieselbe Reihe, Distanz 0). B selbst sauber.
    expected_retrieval = dist0 + dist1 + dist0 + dist0   # P, A, Q, B
    expected_relocations = 2
    expected_extra = 2.0 * abs(dist1 - dist0) + 2.0 * 0.0

    assert res.retrieval_dist_sum == expected_retrieval
    assert res.n_pickups == 4
    assert res.relocations == expected_relocations
    assert res.relocation_extra_dist == expected_extra
    assert res.overflow == 0

    # Unabhaengige Nachrechnung mit der Handformel (tests/helpers.py, nicht hst_rules.py).
    assert helpers.brute_force_relocation_cost(1, [0]) == 2.0 * abs(dist1 - dist0)
    assert helpers.brute_force_relocation_cost(0, [0]) == 0.0


# ---------------------------------------------------------------------------------------------
# Unabhaengige Nachrechnung (tests/helpers.reference_simulate) gegen hst_simulation.simulate,
# ueber viele kleine Zufallsinstanzen und beide Regeln.
# ---------------------------------------------------------------------------------------------
def test_reference_cross_check_many_small_instances():
    for seed in range(60):
        n_items = 3 + seed % 6
        n_rows = 1 + seed % 3
        depth = 1 + seed % 3
        for policy in C.POLICY_KEYS:
            items_a = S.make_shift(n_items, window_hours=2, mean_dwell_min=20, sigma_pct=(seed % 4) * 30, seed=seed)
            items_b = S.copy_items(items_a)
            res = SIM.simulate(items_a, n_rows, depth, policy, record_steps=False)
            ref = helpers.reference_simulate(items_b, n_rows, depth, policy)
            assert res.retrieval_dist_sum == ref["retrieval_dist_sum"], (seed, policy)
            assert res.n_pickups == ref["n_pickups"], (seed, policy)
            assert res.relocations == ref["relocations"], (seed, policy)
            assert res.relocation_extra_dist == ref["relocation_extra_dist"], (seed, policy)
            assert res.overflow == ref["overflow"], (seed, policy)


# ---------------------------------------------------------------------------------------------
# Randfaelle der Platzierung.
# ---------------------------------------------------------------------------------------------
def test_place_nearest_no_free_row_returns_none():
    rows = [[_item(0, 0, 10)], [_item(1, 0, 10)]]
    assert R.place_nearest(rows, depth=1) is None


def test_place_nearest_single_free_row():
    rows = [[_item(0, 0, 10)], []]
    assert R.place_nearest(rows, depth=1) == 1


def test_place_lookahead_prefers_non_blocking_row():
    early_row = [_item(0, 0, 10)]     # vorderste Abholzeit 10, 1 freier Platz (Tiefe 2)
    late_row = [_item(1, 0, 500)]     # vorderste Abholzeit 500, 1 freier Platz
    rows = [early_row, late_row]
    newcomer = _item(2, 0, pickup=50, pickup_est=50)
    # Reihe 0 (Abholzeit 10): der Neuankömmling (Abholzeit 50) würde vorne stehen und den
    # früheren Auftrag blockieren (50 <= 10 ist falsch). Reihe 1 (Abholzeit 500): der
    # Neuankömmling wird VOR dem dortigen Auftrag abgeholt, blockiert ihn also nicht (50 <= 500
    # ist wahr) - Reihe 1 wird gewählt, obwohl sie weiter weg liegt.
    assert R.place_lookahead(rows, depth=2, item=newcomer) == 1


def test_place_lookahead_boundary_equal_pickup_is_non_blocking():
    """Randfall: pickup_est GLEICH dem Minimum der Reihe zählt als NICHT blockierend (<=, nicht <)
    - sonst würde die naehere Reihe bei exakter Gleichheit faelschlich als blockierend gelten."""
    rows = [[_item(0, 0, pickup=42, pickup_est=42)], []]   # Reihe 0: min pickup_est = 42
    newcomer = _item(1, 0, pickup=42, pickup_est=42)       # exakt gleich
    assert R.place_lookahead(rows, depth=2, item=newcomer) == 0   # naeher (Reihe 0), da nicht blockierend


def test_tiebreak_identical_for_both_policies_same_pickup():
    # Zwei gleich leere Reihen, gleiche pickup_est ueberall: beide Regeln muessen dieselbe (kleinste
    # Distanz, dann kleinster Index) Reihe waehlen.
    rows_a, rows_b = [[], []], [[], []]
    item = _item(0, 0, pickup=10, pickup_est=10)
    assert R.place_nearest(rows_a, depth=2) == R.place_lookahead(rows_b, depth=2, item=item) == 0


def test_lookahead_tiebreak_reversed_candidate_order():
    """Sensitivitaetscheck wie im Vorab-Check: baut die Kandidatenliste in umgekehrter Reihenfolge
    auf und prueft, dass beide Platzierungsfunktionen bei identischem Zustand dasselbe Ergebnis
    liefern wie mit der Original-Reihenfolge - kein Kandidatenlisten-Artefakt
    (feedback_bestfit_tiebreak_order_artefact)."""
    import hst_rules as rules_mod

    def place_nearest_reversed(rows, depth, _item=None):
        cand = [r for r in range(len(rows)) if len(rows[r]) < depth]
        cand = list(reversed(cand))
        if not cand:
            return None
        cand.sort(key=lambda r: (C.row_distance(r), r))
        return cand[0]

    def place_lookahead_reversed(rows, depth, item):
        cand = [r for r in range(len(rows)) if len(rows[r]) < depth]
        cand = list(reversed(cand))
        if not cand:
            return None
        non_blocking = [r for r in cand if not rows[r] or item.pickup_est <= min(o.pickup_est for o in rows[r])]

        def key(r):
            top = rows[r][-1].pickup_est if rows[r] else -1.0
            return (-top, C.row_distance(r), r)

        pool = non_blocking if non_blocking else cand
        return sorted(pool, key=key)[0]

    for seed in range(20):
        n_rows, depth = 4, 3
        rows_state = [[] for _ in range(n_rows)]
        items = S.make_shift(6, 4, 40, 0, seed=seed)
        for it in items[:5]:
            r_fwd = rules_mod.place_nearest([list(r) for r in rows_state], depth)
            r_rev = place_nearest_reversed([list(r) for r in rows_state], depth)
            assert r_fwd == r_rev
            r_fwd_l = rules_mod.place_lookahead([list(r) for r in rows_state], depth, it)
            r_rev_l = place_lookahead_reversed([list(r) for r in rows_state], depth, it)
            assert r_fwd_l == r_rev_l
            if r_fwd is not None and len(rows_state[r_fwd]) < depth:
                rows_state[r_fwd].append(it)
