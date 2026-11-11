"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für das Verfahren gelten müssen, ohne dass man das Ergebnis kennt.

Belegt sind hier nur Aussagen, die aus dem Modell folgen: breitere (ineinandergelegte) Fenster machen den besten Wert nie schlechter; Fenster [0, H] geben das Ergebnis der
reinen Zeitgrenze; Warten ändert die Kosten eines Labels nicht; jedes Label liegt im Fenster seines Knotens; jede Rückkehr liegt höchstens bei H; dieselbe Eingabe gibt in zwei
Prozessen mit verschiedenem Hash-Seed dieselben Zählungen. Ausdrücklich KEINE Eigenschaft „die Label-Zahl wird mit breiteren Fenstern nie kleiner“: ein zusätzliches Label kann
andere dominieren, die Label-Zahl wird nur gemessen."""

import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import zfl_algorithm as A
import zfl_scenario as S

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("clustered", [False, True])
@pytest.mark.parametrize("n,k", [(7, 7), (12, 5)])
def test_wider_nested_windows_never_make_the_best_value_worse(n, k, clustered):
    """Dieselben Mittelpunkte, nur die Breite wächst: jedes engere Fenster liegt im breiteren. Die zulässigen Routen wachsen, der beste Wert sinkt nie."""
    for seed in range(20):
        values = []
        for width in (20, 60, 100, 150):
            inst = S.make_instance(n, seed, width, clustered=clustered)
            values.append(A.price(inst, S.first_round_duals(inst), k).best_value)
        assert all(b <= a + 1e-9 for a, b in zip(values, values[1:])), (n, k, clustered, seed, values)


def test_the_windows_are_really_nested():
    for seed in range(10):
        narrow, wide = S.make_instance(10, seed, 20), S.make_instance(10, seed, 100)
        assert all(wide.ready[i] <= narrow.ready[i] and narrow.due[i] <= wide.due[i] for i in range(1, 11))


def test_full_windows_equal_the_pure_time_limit():
    """Fenster [0, H] (ohne Beschneiden): das Ergebnis ist das der reinen Zeitgrenze, hier unabhängig als Summe aus Fahrt und Bedienzeit gerechnet (kein Warten möglich)."""
    for seed in range(25):
        base = S.make_instance(6, seed, 60)
        inst = S.Inst(base.n, base.pts, base.d, base.dem, tuple([0.0] * 7), tuple([base.H] * 7), base.H, base.Q, base.svc, base.width)
        pi = S.first_round_duals(inst)
        best = 0.0
        for size in range(1, 7):
            for seq in itertools.permutations(range(1, 7), size):
                legs = [0] + list(seq) + [0]
                travel = sum(base.d[a][b] for a, b in zip(legs, legs[1:]))
                if travel + base.svc * size <= base.H and sum(base.dem[j] for j in seq) <= base.Q:
                    best = min(best, travel - sum(pi[j] for j in seq))
        assert A.price(inst, pi, 6).best_value == pytest.approx(best, abs=1e-9), seed


def test_waiting_does_not_change_the_cost_of_a_label():
    """Kosten eines Labels = Fahrstrecke entlang des Weges minus Dualpreise, auch wenn auf dem Weg gewartet wurde."""
    waited = 0
    for seed in range(15):
        inst = S.make_instance(10, seed, 60)
        pi = S.first_round_duals(inst)
        r = A.price(inst, pi, 5, trace=True)
        for rec in r.trace.labels[1:]:
            legs = (0,) + rec.path
            assert rec.cost == pytest.approx(sum(inst.d[a][b] for a, b in zip(legs, legs[1:])) - sum(pi[j] for j in rec.path)), (seed, rec.serial)
            waited += rec.wait > 0
    assert waited > 100                                           # es wurde wirklich gewartet


def test_every_label_lies_inside_its_window_and_every_route_returns_in_time():
    for clustered in (False, True):
        for seed in range(10):
            inst = S.make_instance(15, seed, 100, clustered=clustered)
            r = A.price(inst, S.first_round_duals(inst), 5, trace=True)
            for rec in r.trace.labels[1:]:
                assert inst.ready[rec.node] - 1e-9 <= rec.time <= inst.due[rec.node] + 1e-9
                assert rec.time >= rec.arrival - 1e-9 and rec.time - rec.arrival == pytest.approx(rec.wait)
            for _, route in r.routes:
                assert A.check_feasible(inst, route, elementary=False)
                assert A.schedule(inst, route)[1] <= inst.H + 1e-9


def test_a_label_never_waits_longer_than_until_the_window_opens():
    inst = S.make_instance(15, 2, 40)
    r = A.price(inst, S.first_round_duals(inst), 5, trace=True)
    for rec in r.trace.labels[1:]:
        assert rec.wait == pytest.approx(max(0.0, inst.ready[rec.node] - rec.arrival))


def test_same_input_gives_the_same_counts_in_two_processes_with_different_hash_seeds():
    code = (
        "import json, sys; sys.path.insert(0, sys.argv[1]); import zfl_algorithm as A, zfl_scenario as S\n"
        "out = []\n"
        "for clustered in (False, True):\n"
        "    inst = S.make_instance(14, 3, 70, clustered=clustered); r = A.price(inst, S.first_round_duals(inst), 5)\n"
        "    out.append([r.generated, r.dominated, r.waiting, r.window_out, r.best_route])\n"
        "print(json.dumps(out))\n"
    )
    results = []
    for hash_seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        done = subprocess.run([sys.executable, "-c", code, str(ROOT)], capture_output=True, text=True, env=env, timeout=120)
        assert done.returncode == 0, done.stderr
        results.append(json.loads(done.stdout))
    assert results[0] == results[1]
