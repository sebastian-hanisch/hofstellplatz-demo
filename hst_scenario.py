"""Erzeugt eine Schicht: Ankünfte gleichverteilt im Fenster, Verweildauer exponentiell (Rechtsschiefe,
vgl. feedback_skewed_gains_show_distribution), plus ein Schätzfehler auf die Abholzeit (eigener
Zufallsstrom, damit dieselbe Instanz bei sigma=0 und sigma>0 identisch bleibt - nur die vom
vorausschauenden Verfahren GESEHENE Schätzung ändert sich)."""

import random
from dataclasses import dataclass, replace

import hst_constants as C


@dataclass
class Item:
    idx: int
    arrival: float        # Minuten seit Schichtbeginn
    pickup: float          # wahre Abholzeit (Minuten seit Schichtbeginn) - bestimmt die echten Ereignisse
    pickup_est: float      # vom vorausschauenden Verfahren gesehene Schätzung (== pickup bei sigma=0)
    row: int = -1           # während der Simulation belegt: Reihe, in der der Auftrag aktuell steht (-1 = Overflow/noch nicht angekommen)


def _noise_stream(seed):
    """Eigener Zufallsstrom für den Schätzfehler, unabhängig von Ankunft/Standzeit."""
    return random.Random(seed * 1_000_003 + 7)


def make_shift(n_items, window_hours, mean_dwell_min, sigma_pct, seed):
    """n_items Aufträge über ein Fenster von window_hours Stunden; Standzeit exponentiell um
    mean_dwell_min (mindestens MIN_DWELL_MIN); pickup_est = pickup + Rauschen mit Streuung
    sigma_pct % von mean_dwell_min (eigener Strom, sigma=0 -> keine Streuung, exakte Schätzung)."""
    rng = random.Random(seed)
    noise = _noise_stream(seed)
    window_min = window_hours * 60.0
    items = []
    for i in range(n_items):
        arrival = rng.uniform(0.0, window_min)
        dwell = max(C.MIN_DWELL_MIN, rng.expovariate(1.0 / mean_dwell_min))
        pickup = arrival + dwell
        if sigma_pct > 0:
            err = noise.gauss(0.0, sigma_pct / 100.0 * mean_dwell_min)
            pickup_est = max(arrival + 1.0, pickup + err)
        else:
            pickup_est = pickup
        items.append(Item(idx=i, arrival=arrival, pickup=pickup, pickup_est=pickup_est, row=-1))
    return items


def copy_items(items):
    """Frische Kopien für einen zweiten (unabhängigen) Simulationslauf über dieselbe Instanz."""
    return [replace(it) for it in items]
