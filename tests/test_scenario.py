import statistics

import helpers  # noqa: F401  (Pfad-Setup)

import hst_constants as C
import hst_scenario as S


def test_row_distance_hardcoded_values():
    """Maßstab wie yard_constants.py: 20 m Basisabstand, 15 m Reihenabstand (hart kodiert gegen
    Verschiebung der Konstanten, die sonst kein Test bemerken würde)."""
    assert C.row_distance(0) == 20.0
    assert C.row_distance(1) == 35.0
    assert C.row_distance(3) == 65.0
    assert C.MIN_DWELL_MIN == 5.0
    assert C.VERDICT_Z == 2.0


def test_sigma_noise_magnitude_matches_percentage():
    """sigma=100 % soll eine Streuung von rund 1x der mittleren Standzeit ergeben (Stichprobe der
    Schätzfehler über viele Items/Seeds), nicht z. B. die Hälfte oder das Doppelte."""
    errors = []
    for seed in range(200):
        items = S.make_shift(5, 8, 100, 100, seed=seed)
        errors.extend(it.pickup_est - it.pickup for it in items if it.pickup_est > it.arrival + 1.0 + 1e-9)
    sd = statistics.pstdev(errors)
    assert 80.0 <= sd <= 120.0   # erwartet ~100 (sigma=100% von mean_dwell=100 min)


def test_arrivals_within_window_and_dwell_minimum():
    items = S.make_shift(60, 8, 100, 0, seed=1)
    window_min = 8 * 60.0
    assert len(items) == 60
    for it in items:
        assert 0.0 <= it.arrival <= window_min
        assert it.pickup - it.arrival >= C.MIN_DWELL_MIN - 1e-9
        assert it.pickup > it.arrival


def test_sigma_zero_means_exact_estimate():
    items = S.make_shift(40, 8, 100, 0, seed=7)
    for it in items:
        assert it.pickup_est == it.pickup


def test_sigma_positive_perturbs_estimate_but_not_truth():
    items0 = S.make_shift(40, 8, 100, 0, seed=7)
    items_sigma = S.make_shift(40, 8, 100, 80, seed=7)
    # gleiche Instanz (Ankunft/Standzeit) bei unterschiedlichem sigma - eigener Zufallsstrom
    for a, b in zip(items0, items_sigma):
        assert a.arrival == b.arrival
        assert a.pickup == b.pickup
    assert any(a.pickup_est != b.pickup_est for a, b in zip(items0, items_sigma))
    for it in items_sigma:
        assert it.pickup_est >= it.arrival + 1.0 - 1e-9


def test_noise_stream_is_pinned_regression():
    """Regressionsschutz für den Zufallsstrom des Schätzfehlers (eigener Strom, Offset +7 in
    _noise_stream): pinnt arrival/pickup/pickup_est des ersten Auftrags bei einem festen Seed -
    jede Änderung an Formel ODER Strom-Offset würde einen dieser exakten Werte verschieben."""
    items = S.make_shift(3, 8, 100, 50, seed=11)
    assert items[0].arrival == 217.14218568471293
    assert items[0].pickup == 299.18852383102256
    assert items[0].pickup_est == 324.57191218225455


def test_different_seeds_give_different_shifts():
    a = S.make_shift(30, 8, 100, 0, seed=1)
    b = S.make_shift(30, 8, 100, 0, seed=2)
    assert [x.arrival for x in a] != [x.arrival for x in b]


def test_copy_items_is_independent():
    items = S.make_shift(10, 8, 100, 0, seed=3)
    copy = S.copy_items(items)
    copy[0].row = 5
    assert items[0].row != 5
