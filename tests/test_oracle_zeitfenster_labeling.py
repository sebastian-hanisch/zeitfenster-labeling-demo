"""Orakel-Test: das Label-Setting mit Zeitfenstern gegen eine Aufzählung auf einem anderen Rechenweg (ORACLE-PLAYBOOK §2 und §5).

Das Orakel kennt weder `price` noch `schedule` noch die Regelfunktionen des Kerns: Es nimmt rohe Daten (Punkte, Fenster, Lasten, Dualpreise), zählt jede Reihenfolge
von Kunden auf und führt dazu eine Fahrplan-Liste mit einer Uhr (Fahrt, Warten, Bedienung beim Verlassen). Verglichen werden der beste Wert, jede vom Kern gemeldete Route
(zulässig? Kosten?) und die Zulässigkeitsprüfung `check_feasible` je Aufzählungsroute. Elementar (k = n), nichtelementar (k = 1) und ng-Gedächtnis (k = 3) sind abgedeckt.
Instanzen: feste Zufallsstände, Gleichstände und Punktfenster eingeschlossen; Laufzeit unter 10 Sekunden."""

import itertools
import math
import random

import pytest
from conftest import HAND_BEST, HAND_ROUTES, HAND_WIDTHS

import zfl_algorithm as A
import zfl_scenario as S

# --- Orakel ----------------------------------------------------------------------------------------------------------------------------------


def dist(a, b, metric):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) if metric == "manhattan" else math.hypot(a[0] - b[0], a[1] - b[1])


def run_schedule(raw, seq):
    """Fahrplan mit einer Uhr: Rückgabe (zulässig, reduzierte Kosten). `raw` ist ein Wörterbuch aus Rohdaten; Kunde i liegt bei raw["pts"][i]."""
    pts, e, l, dem, pi, metric = raw["pts"], raw["e"], raw["l"], raw["dem"], raw["pi"], raw["metric"]
    clock, here, load, cost = 0.0, 0, 0, 0.0
    for c in seq:
        step = dist(pts[here], pts[c], metric)
        clock += step                      # Fahrt
        cost += step - pi[c]
        if clock > l[c] + 1e-9:
            return False, None
        clock = max(clock, e[c])           # Warten
        load += dem[c]
        if load > raw["Q"]:
            return False, None
        clock += raw["svc"]                # Bedienung; die Abfahrt folgt sofort
        here = c
    back = dist(pts[here], pts[0], metric)
    if seq and clock + back > raw["H"] + 1e-9:
        return False, None
    return True, cost + (back if seq else 0.0)


def elementary_routes(raw):
    n = len(raw["pts"]) - 1
    out = {}
    for size in range(1, n + 1):
        for seq in itertools.permutations(range(1, n + 1), size):
            ok, cost = run_schedule(raw, seq)
            if ok:
                out[seq] = cost
    return out


def ng_sets(raw, k):
    n = len(raw["pts"]) - 1
    sets = {}
    for j in range(1, n + 1):
        near = sorted(range(1, n + 1), key=lambda i: (dist(raw["pts"][j], raw["pts"][i], raw["metric"]), i))[:k]
        sets[j] = set(near) | {j}
    return sets


def walk_routes(raw, k, depth):
    """Alle Routen, die das Gedächtnis NG der Größe k einhält (k = 1: nur die sofortige Wiederholung ist verboten), bis zur Tiefe `depth`."""
    n = len(raw["pts"]) - 1
    ng = ng_sets(raw, k)
    out = {}

    def rec(seq, forbidden):
        if seq:
            ok, cost = run_schedule(raw, seq)
            if not ok:
                return
            out[tuple(seq)] = cost
        if len(seq) == depth:
            return
        for j in range(1, n + 1):
            if j in forbidden:
                continue
            rec(seq + [j], {x for x in forbidden | {j} if x in ng[j]})

    rec([], set())
    return out


def inst_of(raw):
    return S.instance_from_data(raw["pts"], raw["dem"], raw["e"], raw["l"], raw["H"], raw["Q"], raw["svc"], raw["metric"])


def random_raw(seed, n, metric="manhattan", H=40, svc=2, Q=12, halves=(0, 1, 3, 6, 12), box=10):
    rng = random.Random(seed)
    pts = [(5, 5)] + [(rng.randint(5 - box // 2, 5 + box // 2), rng.randint(5 - box // 2, 5 + box // 2)) for _ in range(n)]
    e, l = [0], [H]
    for i in range(1, n + 1):
        c = rng.randint(2, H - 4)
        half = rng.choice(halves)                                # 0: Punktfenster
        e.append(max(0, c - half))
        l.append(c + half)
    pi = [0] + [rng.randint(0, 14) for _ in range(n)]
    dem = [0] + [rng.randint(1, 5) for _ in range(n)]
    return dict(pts=pts, e=e, l=l, dem=dem, pi=pi, H=H, Q=Q, svc=svc, metric=metric)


# --- Handbeispiel ----------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("i", range(5))
def test_oracle_matches_the_hand_example(hand, duals, i):
    """Das Orakel (Uhr, Aufzählung) und der Kern stimmen mit den Handwerten überein: zulässige Routen und bester Wert."""
    w = HAND_WIDTHS[i]
    inst = hand(w)
    raw = dict(pts=list(inst.pts), e=list(inst.ready), l=list(inst.due), dem=list(inst.dem), pi=list(duals), H=inst.H, Q=inst.Q, svc=inst.svc, metric="manhattan")
    routes = elementary_routes(raw)
    assert len(routes) == HAND_ROUTES[i]
    assert min(routes.values()) == HAND_BEST[i]
    assert A.price(inst, duals, 6).best_value == HAND_BEST[i]


# --- Zufallsinstanzen ------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("metric", ["manhattan", "euclid"])
def test_elementary_label_setting_equals_enumeration(metric):
    """90 Zufallsinstanzen mit 3 bis 6 Kunden, elementar: bester Wert, jede gemeldete Route zulässig mit richtigen Kosten, check_feasible gleich dem Orakel."""
    for seed in range(45):
        n = 3 + seed % 4
        raw = random_raw(seed, n, metric)
        inst = inst_of(raw)
        routes = elementary_routes(raw)
        best = min([c for c in routes.values()] + [0.0])
        res = A.price(inst, raw["pi"], n)
        assert res.best_value == pytest.approx(best, abs=1e-9), (metric, seed)
        for rc, route in res.routes:
            assert route in routes and rc == pytest.approx(routes[route]), (metric, seed, route)
        for seq in itertools.permutations(range(1, min(n, 4) + 1), 2):
            assert A.check_feasible(inst, seq) == (seq in routes), (metric, seed, seq)


def test_reported_routes_are_unique_sorted_and_cost_what_the_enumeration_says():
    """Die gemeldeten Routen sind verschieden, nach Kosten sortiert, höchstens 15, jede zulässig mit den Kosten der Aufzählung; die erste ist die beste negative Route.
    (Dominierte Routen fehlen in der Meldung mit Absicht: das Label-Setting sucht die besten, nicht alle.)"""
    for seed in range(30):
        raw = random_raw(100 + seed, 5)
        routes = elementary_routes(raw)
        res = A.price(inst_of(raw), raw["pi"], 5)
        costs = [rc for rc, _ in res.routes]
        assert costs == sorted(costs) and len(res.routes) <= 15 and len({r for _, r in res.routes}) == len(res.routes), seed
        assert all(route in routes and rc == pytest.approx(routes[route]) for rc, route in res.routes), seed
        negative = [c for c in routes.values() if c < -1e-7]
        assert (costs[0] if costs else 0.0) == pytest.approx(min(negative + [0.0]), abs=1e-9), seed


@pytest.mark.parametrize("k,n,horizon", [(1, 3, 26), (1, 4, 24), (3, 5, 22), (2, 4, 24)])
def test_ng_label_setting_equals_walk_enumeration(k, n, horizon):
    """Nichtelementar (k = 1) und ng-Gedächtnis (k = 2, 3): Tiefensuche über alle Wege, die das Gedächtnis einhalten. Der Horizont (kurz gegen die Bedienzeit) begrenzt die Tiefe."""
    total, repeated = 0, 0
    for seed in range(25):
        raw = random_raw(200 + seed, n, H=horizon, svc=4, Q=1000, halves=(3, 6, 12, 20), box=4)
        walks = walk_routes(raw, k, depth=12)
        assert max((len(s) for s in walks), default=0) < 12, (k, seed)      # die Tiefengrenze greift nie: der Horizont begrenzt die Wege
        total += len(walks)
        repeated += sum(1 for s in walks if len(set(s)) < len(s))
        best = min([c for c in walks.values()] + [0.0])
        res = A.price(inst_of(raw), raw["pi"], k)
        assert res.best_value == pytest.approx(best, abs=1e-9), (k, n, seed)
        for rc, route in res.routes:
            assert route in walks and rc == pytest.approx(walks[route]), (k, seed, route)
    assert total > 300                                                      # die Aufzählung ist nicht leer
    assert repeated > 0 or k > 1                                            # bei k = 1 kommen wiederholte Kunden wirklich vor


def test_solomon_like_instances_with_euclidean_distances():
    """Kleine Solomon-artige Instanzen des Generators (6 Kunden), alle drei Breiten, zufällig und gruppiert: Kern gegen Aufzählung aus den Rohdaten der Instanz."""
    for clustered in (False, True):
        for width in (20, 60, 150):
            for seed in range(5):
                inst = S.make_instance(6, seed, width, clustered=clustered)
                pi = S.first_round_duals(inst)
                raw = dict(pts=list(inst.pts), e=list(inst.ready), l=list(inst.due), dem=list(inst.dem), pi=pi, H=inst.H, Q=inst.Q, svc=inst.svc, metric="euclid")
                best = min([c for c in elementary_routes(raw).values()] + [0.0])
                assert A.price(inst, pi, 6).best_value == pytest.approx(best, abs=1e-9), (clustered, width, seed)
