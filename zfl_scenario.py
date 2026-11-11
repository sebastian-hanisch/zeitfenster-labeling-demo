"""Szenario: Instanzen mit Zeitfenstern.

Zwei Arten von Instanzen, beide ohne Bibliotheken (nur Standardbibliothek):

* `make_instance`: Solomon-artige Zufallsinstanz (Quadrat 100 x 100, Zeit = Entfernung, Bedienzeit 10, Horizont 300, Kapazität 70), Fenster der
  Breite w um einen zufälligen Mittelpunkt, auf die zulässige Zeitspanne beschnitten. Nicht die Originalinstanzen von Solomon.
* `hand_instance`: das Handbeispiel mit 6 Kunden auf einem Gitter, festen ganzen Zahlen und Manhattan-Abstand; von Hand nachrechenbar.

Zufall nur über einen Generator, der aus dem Seed der Instanz gebildet wird (kein globaler Zustand). Dieselbe Reihenfolge der Ziehungen wie
in der Vormessung, damit die festen Messreihen (`data/`) zu denselben Instanzen gehören.
"""

import math
import random
from dataclasses import dataclass

import zfl_constants as C


@dataclass(frozen=True)
class Inst:
    """Ein Pricing-Netz: Depot 0 und Kunden 1..n, Entfernungen d, Lasten, Zeitfenster [ready, due] je Knoten."""

    n: int
    pts: tuple                       # Punkte, Index 0 ist das Depot
    d: tuple                         # Entfernungsmatrix; Fahrzeit = Entfernung
    dem: tuple                       # Last je Knoten (Depot: 0)
    ready: tuple                     # Fensterbeginn e je Knoten
    due: tuple                       # Fensterende l je Knoten
    H: float                         # Horizont: spätester Zeitpunkt der Rückkehr zum Depot
    Q: float                         # Kapazität
    svc: float                       # Bedienzeit je Kunde
    width: float = 0.0               # Fensterbreite, mit der die Fenster gebaut wurden (nur zur Anzeige)

    def window(self, j: int) -> tuple:
        return self.ready[j], self.due[j]


def make_instance(n: int, seed: int, width: float, clustered: bool = False, H: float = C.HORIZON, Q: int = C.CAPACITY, svc: float = C.SERVICE) -> Inst:
    """Deterministisch aus (n, seed, width, clustered): gleiche Eingabe, gleiche Instanz."""
    rng = random.Random(seed)
    if clustered:
        centres = [(rng.uniform(15, 85), rng.uniform(15, 85)) for _ in range(C.N_GROUPS)]
        cust = []
        for _ in range(n):
            cx, cy = rng.choice(centres)
            cust.append((min(100.0, max(0.0, rng.gauss(cx, C.GROUP_SPREAD))), min(100.0, max(0.0, rng.gauss(cy, C.GROUP_SPREAD)))))
    else:
        cust = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    pts = [C.DEPOT] + cust
    d = tuple(tuple(math.dist(a, b) for b in pts) for a in pts)
    dem = [0] + [rng.randint(C.DEMAND_LOW, C.DEMAND_HIGH) for _ in range(n)]
    ready, due = [0.0] * (n + 1), [H] * (n + 1)
    for i in range(1, n + 1):
        lo = d[0][i]
        hi = H - svc - d[0][i]
        c = rng.uniform(lo, hi)
        ready[i] = max(lo, c - width / 2)
        due[i] = min(hi, c + width / 2)
    return Inst(n, tuple(pts), d, tuple(dem), tuple(ready), tuple(due), H, Q, svc, width)


def first_round_duals(inst: Inst) -> list:
    """Dualpreise der ersten Spaltenerzeugungs-Runde: je Kunde das Doppelte der Entfernung zum Depot (so viel spart eine Einzelroute, die man ersetzt)."""
    return [0.0] + [2 * inst.d[0][i] for i in range(1, inst.n + 1)]


def instance_from_data(pts, dem, ready, due, H, Q, svc, metric="euclid", width=0.0) -> Inst:
    """Eine Instanz aus rohen Daten (für Tests und Randfälle); `metric` ist "euclid" oder "manhattan"."""
    if metric == "manhattan":
        d = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in pts) for a in pts)
    else:
        d = tuple(tuple(math.dist(a, b) for b in pts) for a in pts)
    return Inst(len(pts) - 1, tuple(pts), d, tuple(dem), tuple(ready), tuple(due), H, Q, svc, width)


def hand_instance(width: int) -> Inst:
    """Das Handbeispiel: Depot und 6 Kunden auf einem Gitter, Manhattan-Abstand, Bedienzeit 2, Horizont 36, Kapazität 99 (wirkt nicht); das Fenster
    der Breite w liegt um den festen Mittelpunkt des Kunden, beschnitten auf [Entfernung, 34 - Entfernung]."""
    pts = C.HAND_POINTS
    n = len(pts) - 1
    d = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in pts) for a in pts)
    half = width // 2
    ready, due = [0], [C.HAND_HORIZON]
    for i in range(1, n + 1):
        ready.append(max(d[0][i], C.HAND_CENTRES[i] - half))
        due.append(min(C.HAND_HORIZON - C.HAND_SERVICE - d[0][i], C.HAND_CENTRES[i] + half))
    return Inst(n, tuple(pts), d, tuple(C.HAND_DEMAND), tuple(ready), tuple(due), C.HAND_HORIZON, C.HAND_CAPACITY, C.HAND_SERVICE, width)


def hand_duals() -> list:
    return list(C.HAND_DUALS)
