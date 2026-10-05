"""Orakel-Test: unabhängige Positionsmodell-Simulation und Brute-Force-Untergrenze (alle Einlagerungsfolgen)
gegen hst_simulation. Beide Orakel teilen keinen Code mit hst_rules/hst_simulation."""

import itertools
import random

import helpers  # noqa: F401  (Pfad-Setup)

import hst_constants as C
import hst_rules as R
import hst_scenario as S
import hst_simulation as SIM
import hst_visualization as V


def _d(r):
    return 20.0 + 15.0 * r


def _my_sim(items, n_rows, depth, policy, forced=None):
    """Positionsmodell: je Reihe eine Liste (hinten -> vorne). forced = feste Reihenfolge der Einlagerungen."""
    order = {r: [] for r in range(n_rows)}
    pos, est = {}, {it.idx: it.pickup_est for it in items}
    tot_ret = extra = 0.0
    n_pk = reloc = ovf = ai = 0

    def nearest():
        c = [r for r in range(n_rows) if len(order[r]) < depth]
        return min(c, key=lambda r: (_d(r), r)) if c else None

    def look(i):
        c = [r for r in range(n_rows) if len(order[r]) < depth]
        if not c:
            return None
        nb = [r for r in c if all(est[i] <= est[j] for j in order[r])]
        if nb:    # engste Passung: kleinste vorderste Abholzeit (leere Reihe = unendlich)
            return min(nb, key=lambda r: (est[order[r][-1]] if order[r] else float("inf"), _d(r), r))
        return min(c, key=lambda r: (-est[order[r][-1]], _d(r), r))

    ev = sorted([(it.arrival, 0, it.idx) for it in items] + [(it.pickup, 1, it.idx) for it in items])
    for _t, kind, i in ev:
        if kind == 0:
            if forced is not None:
                r = forced[ai]
                ai += 1
            else:
                r = nearest() if policy == C.POLICY_NEAREST else look(i)
            if r is None or len(order[r]) >= depth:
                ovf += 1
                pos[i] = -1
            else:
                pos[i] = r
                order[r].append(i)
        elif pos[i] != -1:
            r = pos[i]
            k = order[r].index(i)
            blockers = order[r][k + 1:][::-1]
            order[r] = order[r][:k]
            tot_ret += _d(r)
            n_pk += 1
            for b in blockers:
                nr = nearest()
                if nr is None:
                    pos[b] = -1
                    ovf += 1
                else:
                    pos[b] = nr
                    order[nr].append(b)
                    reloc += 1
                    extra += 2 * abs(_d(r) - _d(nr))
    n = len(items)
    return dict(ret=tot_ret, npk=n_pk, reloc=reloc, extra=extra, ovf=ovf, total=(tot_ret + extra) / n if n else 0.0)


def test_simulation_matches_independent_position_model():
    rng = random.Random(3)
    for _ in range(80):
        n, nr, dp = rng.randint(0, 12), rng.randint(1, 5), rng.randint(1, 4)
        items = S.make_shift(n, 2, rng.choice([5, 20, 60]), rng.choice([0, 50, 150]), rng.randint(0, 10**6))
        for pol in C.POLICY_KEYS:
            res = SIM.simulate(S.copy_items(items), nr, dp, pol, record_steps=True)
            my = _my_sim(S.copy_items(items), nr, dp, pol)
            assert abs(res.retrieval_dist_sum - my["ret"]) < 1e-9
            assert res.n_pickups == my["npk"] and res.relocations == my["reloc"] and res.overflow == my["ovf"]
            assert abs(res.relocation_extra_dist - my["extra"]) < 1e-9
            assert res.n_pickups + res.overflow == n          # jeder Auftrag wird abgeholt oder landet im Overflow
            assert all(len(o) <= dp for st in res.steps for o in st.occupancy)


def test_both_rules_never_beat_brute_force_optimum_of_placements():
    """Untergrenze: kein Plan aus Einlagerungsentscheidungen (Aufzählung aller Reihenfolgen ohne Overflow) ist billiger
    als das Optimum; beide Regeln liegen darüber."""
    rng = random.Random(5)
    checked = 0
    for _ in range(40):
        n, nr, dp = rng.randint(2, 5), rng.randint(1, 3), rng.randint(1, 3)
        if nr * dp < n:
            continue
        items = S.make_shift(n, 1, rng.choice([10, 20, 40]), 0, rng.randint(0, 10**6))
        best = None
        for assign in itertools.product(range(nr), repeat=n):
            r = _my_sim(S.copy_items(items), nr, dp, C.POLICY_NEAREST, forced=list(assign))
            if r["ovf"] == 0 and (best is None or r["total"] < best):
                best = r["total"]
        if best is None:
            continue
        for pol in C.POLICY_KEYS:
            res = SIM.simulate(S.copy_items(items), nr, dp, pol, record_steps=False)
            if res.overflow == 0:
                assert res.total_dist_per_item >= best - 1e-9
                checked += 1
    assert checked > 20


def test_h_curve_labels_show_real_capacity():
    """Die H-Kurve hält die Kapazität nur bis auf Rundung fest (R' = round(R·H/H')); die Achse nennt die tatsächliche Kapazität."""
    fig = V.h_curve_figure([(1, 15, 1.0, 1.0), (2, 8, 1.0, 1.0), (3, 5, 1.0, 1.0), (4, 4, 1.0, 1.0)])
    assert list(fig.data[0].x) == ["H=1 (15×1 = 15 Plätze)", "H=2 (8×2 = 16 Plätze)", "H=3 (5×3 = 15 Plätze)", "H=4 (4×4 = 16 Plätze)"]


def test_place_lookahead_is_tightest_fit_against_brute_force():
    """Einlagerungsregel gegen eine unabhängige Brute-Force-Wahl über alle Reihen: unter den Reihen ohne Verdrängung
    (eigene Abholzeit <= alle Abholzeiten der Reihe) die KLEINSTE vorderste Abholzeit (>= eigene), leere Reihe zuletzt;
    Gleichstand: kleinste Distanz, dann kleinster Index; ohne solche Reihe: größte vorderste Abholzeit."""
    rng = random.Random(11)
    n_tight = n_fallback = n_tie = 0
    for _ in range(600):
        n_rows, depth = rng.randint(1, 6), rng.randint(1, 4)
        # kleine Wertemenge erzeugt Gleichstände; Reihen füllen sich zufällig, einige bleiben leer
        rows = [[S.Item(idx=100 * r + k, arrival=0.0, pickup=0.0, pickup_est=float(rng.choice([10, 20, 30, 40, 50, 60])), row=r)
                 for k in range(rng.randint(0, depth))] for r in range(n_rows)]
        own = float(rng.choice([5, 10, 20, 35, 45, 60, 70]))
        item = S.Item(idx=-1, arrival=0.0, pickup=own, pickup_est=own, row=-1)
        got = R.place_lookahead(rows, depth, item)
        free = [r for r in range(n_rows) if len(rows[r]) < depth]
        if not free:
            assert got is None
            continue
        free_clear = [r for r in free if all(own <= o.pickup_est for o in rows[r])]
        if free_clear:
            def front(r):
                return rows[r][-1].pickup_est if rows[r] else float("inf")
            best = min(front(r) for r in free_clear)
            ties = [r for r in free_clear if front(r) == best]
            want = min(ties, key=lambda r: (20.0 + 15.0 * r, r))
            assert got == want
            assert got in free_clear and front(got) >= own
            assert all(front(r) >= front(got) for r in free_clear)       # keine verdrängungsfreie Reihe passt enger
            n_tight += 1
            n_tie += len(ties) > 1
        else:
            worst_top = max(rows[r][-1].pickup_est for r in free)
            ties = [r for r in free if rows[r][-1].pickup_est == worst_top]
            assert got == min(ties, key=lambda r: (20.0 + 15.0 * r, r))
            n_fallback += 1
    assert n_tight > 100 and n_fallback > 20 and n_tie > 10       # alle Zweige kommen vor
