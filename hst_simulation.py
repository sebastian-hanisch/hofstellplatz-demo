"""Ablauf im Hof: spielt eine Schicht für eine Einlagerungsregel durch, zählt die Kennzahlen und
zeichnet je Ereignis einen Schritt auf (für die Hofansicht mit Schrittregler)."""

from dataclasses import dataclass, field

import hst_constants as C
import hst_rules as R
import hst_scenario as S


@dataclass
class Step:
    time: float
    kind: str            # "arrive" | "pickup" | "overflow"
    item_idx: int
    row: int              # betroffene Reihe (Ankunft/Abholung) bzw. -1 bei Overflow
    occupancy: tuple       # Momentaufnahme je Reihe: Tupel von Tupeln (item_idx,...), vorne = Gasse
    relocations: tuple = ()  # bei "pickup": ((blocker_idx, alte_reihe, neue_reihe_oder_None), ...)


@dataclass
class Result:
    policy: str
    n_rows: int
    depth: int
    retrieval_dist_sum: float = 0.0
    n_pickups: int = 0
    relocations: int = 0
    relocation_extra_dist: float = 0.0
    overflow: int = 0
    n_items: int = 0
    steps: list = field(default_factory=list)

    @property
    def mean_retrieval_dist(self):
        return self.retrieval_dist_sum / self.n_pickups if self.n_pickups else 0.0

    @property
    def reloc_per_item(self):
        return self.relocations / self.n_items if self.n_items else 0.0

    @property
    def reloc_extra_dist_per_item(self):
        return self.relocation_extra_dist / self.n_items if self.n_items else 0.0

    @property
    def total_dist_per_item(self):
        return self.mean_retrieval_dist * (self.n_pickups / self.n_items if self.n_items else 0.0) + self.reloc_extra_dist_per_item

    @property
    def overflow_rate(self):
        return self.overflow / self.n_items if self.n_items else 0.0


def _events(items):
    """(Zeit, Priorität, Art, Auftrag) - Ankunft vor Abholung bei exakter Zeitgleichheit ist
    irrelevant (Standzeit >= MIN_DWELL_MIN), aber deterministisch sortiert."""
    ev = []
    for it in items:
        ev.append((it.arrival, 0, "arrive", it))
        ev.append((it.pickup, 1, "pickup", it))
    ev.sort(key=lambda e: (e[0], e[1], e[3].idx))
    return ev


def _snapshot(rows):
    return tuple(tuple(it.idx for it in row) for row in rows)


def simulate(items, n_rows, depth, policy, record_steps=True):
    rows = [[] for _ in range(n_rows)]
    place_fn = R.PLACERS[policy]
    res = Result(policy=policy, n_rows=n_rows, depth=depth, n_items=len(items))

    for time_, _prio, kind, item in _events(items):
        if kind == "arrive":
            r = place_fn(rows, depth, item)
            if r is None:
                res.overflow += 1
                item.row = -1
                if record_steps:
                    res.steps.append(Step(time_, "overflow", item.idx, -1, _snapshot(rows)))
                continue
            item.row = r
            rows[r].append(item)
            if record_steps:
                res.steps.append(Step(time_, "arrive", item.idx, r, _snapshot(rows)))
        else:  # pickup
            if item.row == -1:
                continue      # war im Overflow, hat nie einen Platz bekommen
            r = item.row
            res.retrieval_dist_sum += C.row_distance(r)
            res.n_pickups += 1
            moves, extra_dist = R.retrieve(rows, depth, r, item.idx)
            res.relocations += sum(1 for _, new_r in moves if new_r is not None)
            res.overflow += sum(1 for _, new_r in moves if new_r is None)
            res.relocation_extra_dist += extra_dist
            if record_steps:
                res.steps.append(Step(time_, "pickup", item.idx, r, _snapshot(rows),
                                       relocations=tuple((b.idx, r, new_r) for b, new_r in moves)))
    return res


def run_pair(items, n_rows, depth, record_steps=True):
    """Beide Regeln über dieselbe Instanz (unabhängige Kopien, siehe hst_scenario.copy_items)."""
    items_nearest = S.copy_items(items)
    items_look = S.copy_items(items)
    res_nearest = simulate(items_nearest, n_rows, depth, "naechster", record_steps)
    res_look = simulate(items_look, n_rows, depth, "vorausschauend", record_steps)
    return res_nearest, res_look
