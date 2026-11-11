"""Kern gegen Handrechnung (Mini-Instanz = Handbeispiel) und je Regel einzeln (DEMO-PLAYBOOK §1b).

Jede Regel des Kerns ist eine Funktion und wird an handgesetzten Werten geprüft; jede Regel mit Wirkung wird abgeschaltet und muss das Ergebnis auf mindestens einer
Instanz ändern (Zweig-Test). Der unabhängige Vergleich mit einer Aufzählung steht in tests/test_oracle_zeitfenster_labeling.py."""

import time

import pytest
from conftest import (
    HAND_BEST,
    HAND_DOMINATED,
    HAND_LABELS,
    HAND_ROUTES,
    HAND_SAME_TIME,
    HAND_WAIT_SUM,
    HAND_WAITING,
    HAND_WIDTHS,
    HAND_WINDOW_OUT,
)

import zfl_algorithm as A
import zfl_scenario as S

# --- Handrechnung ----------------------------------------------------------------------------------------------------------------------------


def test_hand_geometry_and_windows(hand):
    inst = hand(6)
    # Depot (5, 5), Kunde 1 bei (6, 6): Entfernung |6 - 5| + |6 - 5| = 2
    assert inst.d[0][1] == abs(6 - 5) + abs(6 - 5) == 2
    # Fenster bei w = 6, Mitte 27: [27 - 3, 27 + 3] = [24, 30], beschnitten auf [2, 34 - 2] = [2, 32]
    assert inst.window(1) == (27 - 3, 27 + 3)
    # Kunde 2: Mitte 14, [11, 17]; Entfernung 6, beschnitten auf [6, 28]: unverändert
    assert inst.window(2) == (14 - 3, 14 + 3)
    # bei w = 60 wird das Fenster von Kunde 1 beschnitten: [27 - 30, 27 + 30] auf [2, 32]
    assert hand(60).window(1) == (2, 34 - 2)


def test_label_l1_waits_22_and_costs_minus_6(hand, duals):
    """Label L1 (Weg 1): Ankunft 2, Fenster beginnt bei 24, wartet 22; Kosten 2 - 8 = -6 (Warten ändert die Kosten nicht)."""
    r = A.price(hand(6), duals, 6, trace=True)
    l1 = r.trace.labels[1]
    assert l1.path == (1,)
    assert l1.arrival == 2 == abs(6 - 5) + abs(6 - 5)
    assert l1.wait == 22 == 24 - 2
    assert l1.time == 24
    assert l1.cost == 2 - 8 == -6


def test_label_l7_waits_3_and_is_dominated_at_equal_time(hand, duals):
    """Label L7 (Weg 2-1): nach Kunde 2 (Ankunft 6, wartet bis 11, Bedienung bis 13) 8 Einheiten nach Kunde 1: Ankunft 21, wartet 3 bis 24, Kosten 6 + 8 - 10 - 8 = -4.
    L1 (Zeit 24, Kosten -6, Kunde 1 besucht) dominiert es; nach dem Warten haben beide dieselbe Zeit 24."""
    r = A.price(hand(6), duals, 6, trace=True)
    l7 = r.trace.labels[7]
    assert l7.path == (2, 1)
    d21 = abs(6 - 0) + abs(6 - 4)
    assert l7.arrival == 11 + 2 + d21 == 21
    assert l7.wait == 3 and l7.time == 24
    assert l7.cost == 6 + d21 - 10 - 8 == -4
    assert (l7.status, l7.by, l7.same_time) == ("dominiert", 1, True)


def test_extension_l3_to_customer_2_fails_at_the_window_end(hand, duals):
    """L3 (Weg 3) hat die Zeit 19; nach Bedienung (2) und 11 Einheiten Fahrt wäre die Ankunft bei Kunde 2 gleich 32 > Fensterende 17."""
    r = A.price(hand(6), duals, 6, trace=True)
    arrival = 19 + 2 + (abs(8 - 0) + abs(7 - 4))
    assert arrival == 32
    assert any(w.parent == 3 and w.node == 2 and w.arrival == 32 and w.due == 17 for w in r.trace.window_out)


@pytest.mark.parametrize("i", range(5))
def test_hand_values_per_width(hand, duals, i):
    """Alle Zählungen des Handbeispiels je Breite (Handrechen-Skript der Planung)."""
    w = HAND_WIDTHS[i]
    r = A.price(hand(w), duals, 6)
    assert r.best_value == HAND_BEST[i]
    assert r.generated == HAND_LABELS[i]
    assert r.dominated == HAND_DOMINATED[i]
    assert r.waiting == HAND_WAITING[i]
    assert r.wait_sum == HAND_WAIT_SUM[i]
    assert r.window_out == HAND_WINDOW_OUT[i]
    assert r.same_time == HAND_SAME_TIME[i]
    assert len(A.enumerate_routes(hand(w), duals)) == HAND_ROUTES[i]
    assert A.check_feasible(hand(w), r.best_route) and A.reduced_cost(hand(w), duals, r.best_route) == HAND_BEST[i]


def test_best_route_at_width_6_is_4_1_5(hand, duals):
    r = A.price(hand(6), duals, 6)
    assert r.best_route == (4, 1, 5) and r.best_value == -18


def test_trace_agrees_with_the_counters(hand, duals):
    for w in HAND_WIDTHS:
        r = A.price(hand(w), duals, 6, trace=True)
        recs = r.trace.labels
        assert len(recs) == r.generated
        assert sum(1 for x in recs if x.status != "bleibt") == r.dominated
        assert sum(1 for x in recs if x.wait > 0) == r.waiting
        assert sum(1 for x in recs if x.same_time) == r.same_time
        assert len(r.trace.window_out) == r.window_out


# --- Einzelne Regeln -------------------------------------------------------------------------------------------------------------------------


def test_arrival_time_leaves_the_depot_at_once_but_serves_before_leaving_a_customer(hand):
    inst = hand(6)
    assert A.arrival_time(inst, 0, 0, 1) == 2                    # Depot: sofort los, Entfernung 2
    assert A.arrival_time(inst, 2, 11, 1) == 11 + 2 + 8          # Kunde 2: Bedienzeit 2, Entfernung 8


def test_fits_window_is_inclusive_at_the_end(hand):
    inst = hand(6)                                               # Kunde 1: [24, 30]
    assert A.fits_window(inst, 1, 30) and not A.fits_window(inst, 1, 30.001)
    assert A.fits_window(inst, 1, 2)                             # zu früh ist erlaubt (man wartet)


def test_service_start_waits_until_the_window_opens(hand):
    inst = hand(6)
    assert A.service_start(inst, 1, 2) == 24                     # zu früh: Warten bis 24
    assert A.service_start(inst, 1, 24) == 24                    # genau zum Beginn: kein Warten
    assert A.service_start(inst, 1, 27) == 27                    # im Fenster: unverändert


def test_can_return_is_inclusive_at_the_horizon(hand):
    inst = hand(6)                                               # H = 36, Bedienzeit 2, Kunde 1 liegt 2 vom Depot
    assert A.can_return(inst, 1, 32) and not A.can_return(inst, 1, 32.5)


def test_dominates_checks_every_criterion():
    base = [10, 5.0, 3, 0b0110, 1, -1, False, 0]

    def mk(t=10, c=5.0, q=3, mem=0b0110):
        return [t, c, q, mem, 1, -1, False, 0]

    assert A.dominates(base, mk())                                # gleich dominiert (gegenseitig)
    assert A.dominates(mk(t=9, c=4.0, q=2, mem=0b0010), mk())
    assert not A.dominates(mk(t=11), mk())                        # später
    assert not A.dominates(mk(c=5.5), mk())                       # teurer
    assert not A.dominates(mk(q=4), mk())                         # schwerer
    assert not A.dominates(mk(mem=0b1110), mk())                  # sperrt einen Kunden mehr
    assert not A.dominates(mk(mem=0b0001), mk())                  # sperrt einen anderen Kunden


def test_memory_rules(hand):
    inst = hand(6)
    assert A.ng_masks(inst, 1)[3] == 1 << 3                       # k = 1: nur der Kunde selbst
    assert A.ng_masks(inst, 6)[3] == sum(1 << i for i in range(1, 7))     # k = n: alle (elementar)
    # nach dem Besuch von 3 bleibt nur gesperrt, was auch in NG(3) liegt, dazu 3 selbst
    assert A.memory_after(0b1111110, 0b0001000, 3) == 0b0001000


# --- Jede Regel mit Wirkung abschaltbar (Zweig-Tests) -----------------------------------------------------------------------------------------


def test_switching_off_the_window_end_rule_changes_the_result(hand, duals, monkeypatch):
    normal = A.price(hand(6), duals, 6)
    monkeypatch.setattr(A, "fits_window", lambda inst, j, arr: True)
    off = A.price(hand(6), duals, 6)
    assert off.generated > normal.generated and off.window_out == 0


def test_switching_off_waiting_changes_the_result(hand, duals, monkeypatch):
    normal = A.price(hand(6), duals, 6)
    monkeypatch.setattr(A, "service_start", lambda inst, j, arr: arr)      # kein Warten: die Zeit ist die Ankunft
    off = A.price(hand(6), duals, 6)
    assert off.waiting == 0 and (off.generated, off.dominated) != (normal.generated, normal.dominated)


def test_switching_off_dominance_changes_the_result(hand, duals, monkeypatch):
    normal = A.price(hand(24), duals, 6)
    monkeypatch.setattr(A, "dominates", lambda a, b: False)
    off = A.price(hand(24), duals, 6)
    assert off.dominated == 0 and off.generated > normal.generated
    assert off.best_value == normal.best_value                              # die Dominanz streicht nur Überflüssiges


def test_memory_k_changes_the_result_on_a_solomon_like_instance():
    inst = S.make_instance(15, 3, 100)
    pi = S.first_round_duals(inst)
    a = A.price(inst, pi, 1)
    b = A.price(inst, pi, 5)
    assert a.generated != b.generated


def test_capacity_rule_changes_the_result():
    inst = S.make_instance(12, 1, 100)
    pi = S.first_round_duals(inst)
    loose = S.Inst(inst.n, inst.pts, inst.d, inst.dem, inst.ready, inst.due, inst.H, 10_000, inst.svc, inst.width)
    assert A.price(loose, pi, 5).generated > A.price(inst, pi, 5).generated


# --- Abbruch, Prüfer ------------------------------------------------------------------------------------------------------------------------


def test_max_labels_aborts_and_says_so():
    inst = S.make_instance(30, 0, 100)
    pi = S.first_round_duals(inst)
    r = A.price(inst, pi, 5, max_labels=500)
    assert r.aborted and r.generated < 500 + 31
    assert not A.price(S.hand_instance(6), S.hand_duals(), 6, max_labels=500).aborted


def test_worst_case_at_the_slider_maximum_finishes():
    """Hängertest am Regler-Maximum: 30 Kunden, Breite 150, gruppiert, ng 5, Zufalls-Seed 5 (die größte der 12 Instanzen der Messreihe bei dieser Breite: 92.845 Labels). Kein Zeitvergleich, nur ein großzügiges Netz."""
    t0 = time.perf_counter()
    inst = S.make_instance(30, 5, 150, clustered=True)
    r = A.price(inst, S.first_round_duals(inst), 5, max_labels=600_000)
    assert not r.aborted and r.generated == 92845
    assert time.perf_counter() - t0 < 120


def test_check_feasible_rejects_each_violation(hand):
    inst = hand(6)
    assert A.check_feasible(inst, (4, 1, 5))
    assert not A.check_feasible(inst, (4, 4))                    # doppelter Kunde
    assert not A.check_feasible(inst, (7,))                      # Kunde gibt es nicht
    assert not A.check_feasible(inst, (3, 2))                    # Ankunft 32 > Fensterende 17
    tight = S.Inst(inst.n, inst.pts, inst.d, inst.dem, inst.ready, inst.due, inst.H, 8, inst.svc, 6)
    assert not A.check_feasible(tight, (4, 1, 5))                # Last 3 + 6 + 2 = 11 > 8
    late = S.Inst(inst.n, inst.pts, inst.d, inst.dem, inst.ready, inst.due, 30, inst.Q, inst.svc, 6)
    assert not A.check_feasible(late, (4, 1, 5))                 # Rückkehr nach H


def test_schedule_lists_leave_arrival_wait_and_service(hand):
    stops, back = A.schedule(hand(6), (2, 1))
    s2, s1 = stops
    assert (s2.leave, s2.arrival, s2.start, s2.wait, s2.end) == (0, 6, 11, 5, 13)
    assert (s1.leave, s1.arrival, s1.start, s1.wait, s1.end) == (13, 21, 24, 3, 26)
    assert back == 26 + 2                                        # zurück von Kunde 1 zum Depot: Entfernung 2


def test_the_generator_is_deterministic_and_changes_with_the_seed():
    a = S.make_instance(10, 4, 60)
    assert a == S.make_instance(10, 4, 60)
    assert a != S.make_instance(10, 5, 60)
    assert S.make_instance(10, 4, 60, clustered=True) != a
