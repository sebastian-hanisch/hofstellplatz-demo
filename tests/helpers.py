"""Testhilfen: Pfad-Setup und eine unabhängige Brute-Force-Nachrechnung der Wegkette auf
Kleinstinstanzen (teilt keinen Code mit hst_rules/hst_simulation)."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import hst_constants as C  # noqa: E402


def dist(r):
    return C.BASE_DIST_M + r * C.ROW_SPACING_M


def brute_force_relocation_cost(r_old, new_rows):
    """Unabhängige Nachrechnung der Umsetz-Wegkette: das Fahrzeug fährt von r_old (wo es gerade
    einen Blockierer aufgenommen hat) zu new_rows[0], zurück nach r_old, zu new_rows[1], zurück,
    usw. - Summe aller Legs, jedes Leg = |dist(a) - dist(b)| (nicht übers Tor). Reine
    Listen-Iteration, kein Aufruf von hst_rules/hst_constants.leg_distance."""
    total = 0.0
    here = r_old
    for nr in new_rows:
        total += abs(dist(here) - dist(nr))
        total += abs(dist(nr) - dist(r_old))
        here = r_old
    return total


def reference_simulate(items, n_rows, depth, policy):
    """Unabhängige Nachrechnung von Ablauf und Wegkette - anderer Code als hst_rules.py/
    hst_simulation.py (keine PLACERS, kein retrieve()), aber dieselbe Fachlogik: LIFO-Reihen,
    nächster freier Platz nach (Distanz, Index), vorausschauend nach (verdrängungsfrei, "eng"),
    Umsetzen per nächster freier Platz mit echter (direkter) Wegkette. Rückgabe: dict mit
    retrieval_dist_sum, n_pickups, relocations, relocation_extra_dist, overflow."""
    rows = [[] for _ in range(n_rows)]
    events = []
    for it in items:
        events.append((it.arrival, 0, "a", it))
        events.append((it.pickup, 1, "p", it))
    events.sort(key=lambda e: (e[0], e[1], e[3].idx))

    def free_rows():
        return [r for r in range(n_rows) if len(rows[r]) < depth]

    def choose_nearest():
        cand = free_rows()
        if not cand:
            return None
        best = cand[0]
        for r in cand[1:]:
            if (dist(r), r) < (dist(best), best):
                best = r
        return best

    def choose_lookahead(item):
        cand = free_rows()
        if not cand:
            return None
        non_block = [r for r in cand if not rows[r] or item.pickup_est <= min(o.pickup_est for o in rows[r])]
        pool = non_block if non_block else cand
        best = pool[0]
        for r in pool[1:]:
            top_best = rows[best][-1].pickup_est if rows[best] else -1.0
            top_r = rows[r][-1].pickup_est if rows[r] else -1.0
            if (-top_r, dist(r), r) < (-top_best, dist(best), best):
                best = r
        return best

    retrieval_dist_sum = 0.0
    n_pickups = 0
    relocations = 0
    relocation_extra = 0.0
    overflow = 0

    for _t, _prio, kind, item in events:
        if kind == "a":
            r = choose_nearest() if policy == "naechster" else choose_lookahead(item)
            if r is None:
                overflow += 1
                item.row = -1
                continue
            item.row = r
            rows[r].append(item)
        else:
            if item.row == -1:
                continue
            r = item.row
            stack = rows[r]
            pos = next(k for k, o in enumerate(stack) if o.idx == item.idx)
            blockers = list(reversed(stack[pos + 1:]))
            del stack[pos:]
            retrieval_dist_sum += dist(r)
            n_pickups += 1
            for b in blockers:
                nr = choose_nearest()
                if nr is None:
                    b.row = -1
                    overflow += 1
                    continue
                b.row = nr
                rows[nr].append(b)
                relocations += 1
                relocation_extra += 2.0 * abs(dist(r) - dist(nr))
    return dict(retrieval_dist_sum=retrieval_dist_sum, n_pickups=n_pickups, relocations=relocations, relocation_extra_dist=relocation_extra, overflow=overflow)
