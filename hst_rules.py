"""Die zwei Einlagerungsregeln (Nächster freier Platz / Vorausschauend) und die gemeinsame
Umsetz-Regel bei Blockade - mit ECHTER Wegkettenrechnung statt der groben Schätzung des
Vorab-Checks (vorab_stellplatz/measure.py: dort Distanz(alte Reihe) + Distanz(neue Reihe) je
Umsetzung, als ob jede Fahrt übers Tor zurückliefe).

Echte Wegkette: die Reihen liegen alle entlang desselben Zugangswegs (row_distance = Abstand vom
Tor entlang dieses Wegs, wie yard_constants.py). Um einen Blockierer umzusetzen, fährt das
Hoffahrzeug DIREKT von der alten in die neue Reihe (hst_constants.leg_distance, nicht über das
Tor) und wieder zurück, um den nächsten Blockierer oder den Zielauftrag zu holen. Bei k
Blockierern mit Zielreihen n_1..n_k (Räumreihenfolge: der vorderste zuerst, siehe _pop_blockers)
ist die Umsetz-Wegkette also 2 * Summe(leg_distance(r, n_i)) - die Rückfahrt nach r ist nötig, um
den nächsten Blockierer bzw. anschließend den Zielauftrag selbst zu greifen (dessen Anfahrt separat
als "Anfahrt je Abholung" gezählt wird, siehe hst_simulation.py)."""

import hst_constants as C


def row_free_slots(rows, r, depth):
    return depth - len(rows[r])


def _candidates(rows, depth):
    return [r for r in range(len(rows)) if len(rows[r]) < depth]


def place_nearest(rows, depth, _item=None):
    """Nächster freier Platz: kleinste Distanz zum Tor, dann kleinster Reihenindex. None = Overflow."""
    cand = _candidates(rows, depth)
    if not cand:
        return None
    cand.sort(key=lambda r: (C.row_distance(r), r))
    return cand[0]


def place_lookahead(rows, depth, item):
    """Vorausschauend: bevorzugt eine Reihe ohne Verdrängung (item.pickup_est <= min der Reihe);
    darunter die mit der spätesten vordersten Abholzeit (möglichst eng), sonst kleinste Distanz;
    ohne blockierfreie Reihe: insgesamt die mit der spätesten vordersten Abholzeit. Tie-Break
    identisch zu place_nearest (Distanz, dann Reihenindex) - siehe test_rules.py (Sensitivität
    mit umgekehrtem Tie-Break)."""
    cand = _candidates(rows, depth)
    if not cand:
        return None
    non_blocking = [r for r in cand if not rows[r] or item.pickup_est <= min(o.pickup_est for o in rows[r])]

    def key(r):
        top = rows[r][-1].pickup_est if rows[r] else -1.0
        return (-top, C.row_distance(r), r)

    pool = non_blocking if non_blocking else cand
    pool = sorted(pool, key=key)
    return pool[0]


PLACERS = {C.POLICY_NEAREST: place_nearest, C.POLICY_LOOKAHEAD: place_lookahead}


def _pop_blockers(rows, r, item_idx):
    """Entfernt Zielauftrag UND alle davorstehenden (später geparkten) Blockierer sofort aus der
    Reihe (schafft garantiert Platz zum Umsetzen, auch in derselben Reihe - vgl. Kommentar in
    vorab_stellplatz/measure.py). Rückgabe: Blockierer in RÄUMREIHENFOLGE (vorderster zuerst)."""
    stack = rows[r]
    pos = next(k for k, o in enumerate(stack) if o.idx == item_idx)
    blockers_deep_to_front = stack[pos + 1:]     # Listenreihenfolge: von knapp hinter dem Ziel bis vorne (Gasse)
    del stack[pos:]
    return list(reversed(blockers_deep_to_front))  # vorderster (Gasse) zuerst geräumt


def retrieve(rows, depth, r, item_idx):
    """Holt item_idx aus Reihe r ab: räumt Blockierer per place_nearest in andere Reihen um
    (dieselbe Umsetz-Regel für beide Einlagerungsregeln, isoliert die Einlagerungsentscheidung -
    Design wie blz_rules.py/stk_rules.py). Rückgabe: (Liste (blocker, neue_reihe_oder_None),
    Umsetz-Wegkette in Metern (echte Wegkette, siehe Moduldoc))."""
    blockers = _pop_blockers(rows, r, item_idx)
    moves = []
    extra_dist = 0.0
    for blocker in blockers:
        new_r = place_nearest(rows, depth)
        if new_r is None:
            blocker.row = -1
            moves.append((blocker, None))
            continue
        blocker.row = new_r
        rows[new_r].append(blocker)
        moves.append((blocker, new_r))
        extra_dist += 2.0 * C.leg_distance(r, new_r)
    return moves, extra_dist
