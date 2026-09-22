import helpers  # noqa: F401

import hst_constants as C
import hst_scenario as S
import hst_simulation as SIM


def test_no_row_exceeds_depth_at_any_step():
    for seed in range(15):
        items = S.make_shift(40, 6, 60, seed % 3 * 40, seed=seed)
        for policy in C.POLICY_KEYS:
            res = SIM.simulate(S.copy_items(items), 5, 3, policy, record_steps=True)
            for step in res.steps:
                for row_occ in step.occupancy:
                    assert len(row_occ) <= 3


def test_conservation_pickups_plus_overflow_equals_item_count():
    """Jeder Auftrag endet in genau einem von zwei Zuständen: erfolgreich abgeholt (n_pickups)
    oder als Overflow gezählt (nie platziert ODER als Blockierer nicht mehr umsetzbar) - beides
    schließt sich aus und ist erschöpfend, also gilt n_pickups + overflow == n_items EXAKT
    (unabhängig von R, H, Auslastung oder Regel)."""
    for seed in range(25):
        items = S.make_shift(20 + seed, 6, 60, seed % 5 * 30, seed=seed)
        for policy in C.POLICY_KEYS:
            res = SIM.simulate(S.copy_items(items), 3 + seed % 4, 1 + seed % 4, policy, record_steps=False)
            assert res.n_pickups + res.overflow == len(items)


def test_relocation_can_never_fail_structural_invariant():
    """Strukturelle Eigenschaft dieses Modells: eine Reihe, aus der gerade Ziel + Blockierer
    entfernt wurden, hat IMMER mehr freie Plätze als es Blockierer gab (freie Plätze = depth -
    pos, Blockierer = urspr. Länge - pos - 1 <= depth - pos - 1), das Fahrzeug kann also jeden
    Blockierer notfalls in dieselbe Reihe zurückstellen - eine Umsetzung kann in diesem Modell nie
    an fehlendem Platz scheitern, `res.overflow` steigt ausschließlich durch Ankunfts-Overflow.
    Test über viele Instanzen: overflow-Events treten nur bei "arrive"-Schritten auf."""
    for seed in range(20):
        items = S.make_shift(30, 4, 60, 0, seed=seed)
        for policy in C.POLICY_KEYS:
            res = SIM.simulate(S.copy_items(items), 3, 2, policy, record_steps=True)
            overflow_steps = [s for s in res.steps if s.kind == "overflow"]
            assert len(overflow_steps) == res.overflow


def test_result_properties_zero_when_empty():
    res = SIM.Result(policy="naechster", n_rows=2, depth=2, n_items=0, n_pickups=0)
    assert res.mean_retrieval_dist == 0.0
    assert res.reloc_per_item == 0.0
    assert res.overflow_rate == 0.0
    assert res.total_dist_per_item == 0.0


def test_total_dist_per_item_formula_with_forced_overflow():
    """Erzwingt Ankunfts-Overflow (Kapazitaet 1, 3 Auftraege gleichzeitig im Hof) und prueft die
    Gesamtstrecke-je-Auftrag-Formel exakt gegen eine unabhaengige Handrechnung: sie normiert die
    mittlere Anfahrt auf n_pickups/n_items (nicht auf 1), damit Overflow-Auftraege (die nie
    abgeholt werden) die Kennzahl nicht verzerren - siehe hst_simulation.Result.total_dist_per_item."""
    items = [
        S.Item(idx=0, arrival=0.0, pickup=100.0, pickup_est=100.0, row=-1),
        S.Item(idx=1, arrival=0.1, pickup=200.0, pickup_est=200.0, row=-1),   # findet keinen Platz (Kapazitaet 1)
        S.Item(idx=2, arrival=0.2, pickup=300.0, pickup_est=300.0, row=-1),   # findet keinen Platz
    ]
    res = SIM.simulate(items, n_rows=1, depth=1, policy=C.POLICY_NEAREST, record_steps=False)
    assert res.n_pickups == 1
    assert res.overflow == 2
    assert res.relocation_extra_dist == 0.0
    expected = res.mean_retrieval_dist * (1 / 3) + 0.0
    assert res.total_dist_per_item == expected
    assert abs(res.total_dist_per_item - C.row_distance(0) / 3) < 1e-9


def test_event_tiebreak_arrival_before_pickup_at_same_time():
    """Bei exakter Zeitgleichheit muss eine ANKUNFT vor einer ABHOLUNG verarbeitet werden (die
    Reihe ist zu diesem Zeitpunkt noch belegt) - sonst würde die Abholung faelschlich zuerst Platz
    schaffen. Kapazitaet 1: A (Abholzeit 10) belegt den einzigen Platz; B kommt exakt bei t=10 an
    und MUSS Overflow sein, weil A formal noch im Hof steht."""
    items = [
        S.Item(idx=0, arrival=0.0, pickup=10.0, pickup_est=10.0, row=-1),   # A
        S.Item(idx=1, arrival=10.0, pickup=20.0, pickup_est=20.0, row=-1),  # B, exakt zeitgleich mit A's Abholung
    ]
    res = SIM.simulate(items, n_rows=1, depth=1, policy=C.POLICY_NEAREST, record_steps=False)
    assert res.overflow == 1
    assert res.n_pickups == 1


def test_h1_gives_identical_step_sequences_for_both_policies():
    """Strukturtest zum H=1-Nullbefund: bei H=1 sind ALLE Ereignisse (nicht nur die Kennzahlen)
    fuer beide Regeln identisch - der Plan ist bitgleich, nicht nur im Mittel."""
    for seed in range(10):
        items = S.make_shift(40, 8, 100, 60, seed=seed)
        res_n, res_l = SIM.run_pair(items, n_rows=16, depth=1, record_steps=True)
        assert len(res_n.steps) == len(res_l.steps)
        for sn, sl in zip(res_n.steps, res_l.steps):
            assert sn.kind == sl.kind
            assert sn.row == sl.row
            assert sn.occupancy == sl.occupancy
