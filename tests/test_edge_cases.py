"""Randfälle des Pricings mit Zeitfenstern (DEMO-PLAYBOOK §12): Punktfenster, Ankunft genau am Fensterende und genau am Fensterbeginn, unerreichbare Kunden,
Rückkehr genau bei H, Fenster nach H, n = 1 und n = 2, Gleichstände."""

import zfl_algorithm as A
import zfl_scenario as S


def line(windows, H=100, svc=2, dem=None, Q=99, pi=None):
    """Kunden auf einer Geraden: Kunde i liegt i Einheiten vom Depot entfernt (Manhattan-Abstand), windows[i-1] = (e, l)."""
    n = len(windows)
    pts = [(0, 0)] + [(i, 0) for i in range(1, n + 1)]
    inst = S.instance_from_data(pts, dem or [0] + [1] * n, [0] + [w[0] for w in windows], [H] + [w[1] for w in windows], H, Q, svc, "manhattan")
    return inst, pi or [0] + [10] * n


def test_single_customer():
    inst, pi = line([(0, 50)])
    r = A.price(inst, pi, 1)
    assert r.best_route == (1,) and r.best_value == 1 + 1 - 10 and r.generated == 2 and r.window_out == 0


def test_exactly_two_customers():
    inst, pi = line([(0, 50), (0, 50)])
    r = A.price(inst, pi, 2)
    assert r.best_route == (1, 2) and r.best_value == 1 + 1 + 2 - 20   # Depot - 1 - 2 - Depot: Fahrt 1 + 1 + 2, minus die Dualpreise 10 + 10
    assert A.check_feasible(inst, (2, 1)) and A.check_feasible(inst, (1, 2))


def test_point_window_forces_the_arrival_time():
    """Punktfenster e = l: die Ankunft muss genau treffen, sonst wartet man bis e (zu früh) oder scheidet aus (zu spät)."""
    inst, pi = line([(7, 7)])                                           # Entfernung 1: Ankunft 1, wartet 6 bis 7
    r = A.price(inst, pi, 1, trace=True)
    assert r.generated == 2 and r.trace.labels[1].wait == 6 and r.trace.labels[1].time == 7
    inst2, _ = line([(1, 1)])                                           # Ankunft genau 1: kein Warten
    r2 = A.price(inst2, pi, 1, trace=True)
    assert r2.trace.labels[1].wait == 0 and r2.waiting == 0


def test_arrival_exactly_at_the_window_end_is_feasible_and_one_later_is_not():
    inst, pi = line([(0, 1)])                                           # Ankunft 1 = Fensterende
    assert A.price(inst, pi, 1).generated == 2
    inst2, _ = line([(0, 0.999)])                                       # Fensterende vor der Ankunft
    r = A.price(inst2, pi, 1)
    assert r.generated == 1 and r.window_out == 1 and r.best_route == ()


def test_arrival_exactly_at_the_window_start_does_not_wait():
    inst, pi = line([(1, 9)])
    r = A.price(inst, pi, 1, trace=True)
    assert r.trace.labels[1].arrival == 1 == r.trace.labels[1].time and r.waiting == 0


def test_customer_the_window_does_not_allow_is_unreachable():
    """Das Fenster von Kunde 1 endet vor der Entfernung zum Depot (Fensterende 0,5 < Entfernung 1): der Kunde kommt in keiner Route vor, Kunde 2 bleibt erreichbar."""
    inst = S.instance_from_data([(0, 0), (1, 0), (2, 0)], [0, 1, 1], [0, 0, 0], [100, 0.5, 50], 100, 99, 2, "manhattan")
    r = A.price(inst, [0, 10, 10], 2)
    assert all(1 not in route for _, route in r.routes) and r.best_route == (2,)
    assert not A.check_feasible(inst, (1,)) and A.check_feasible(inst, (2,))


def test_return_exactly_at_the_horizon():
    inst, pi = line([(0, 50)], H=4)                                     # Fahrt 1, Bedienung 2, zurück 1: genau 4
    assert A.price(inst, pi, 1).best_route == (1,)
    inst2, _ = line([(0, 50)], H=3.999)
    assert A.price(inst2, pi, 1).best_route == ()
    assert A.check_feasible(inst, (1,)) and not A.check_feasible(inst2, (1,))


def test_window_after_the_horizon_cannot_be_served():
    """Das Fenster beginnt nach H: Warten bis dahin lässt die Rückkehr scheitern; die Ankunft ist zulässig, die Route nicht."""
    inst, pi = line([(150, 200)], H=100)
    r = A.price(inst, pi, 1)
    assert r.generated == 2 and r.best_route == () and not A.check_feasible(inst, (1,))


def test_two_customers_at_the_same_place_with_equal_windows_and_prices():
    """Gleichstand: zwei Kunden an derselben Stelle mit gleichem Fenster und gleichem Dualpreis. Beide Reihenfolgen kosten gleich; gemeldet wird die kleinere Route."""
    pts = [(0, 0), (3, 0), (3, 0)]
    inst = S.instance_from_data(pts, [0, 1, 1], [0, 0, 0], [100, 50, 50], 100, 99, 2, "manhattan")
    r = A.price(inst, [0, 10, 10], 2)
    assert r.best_value == 3 + 0 + 3 - 20 and r.best_route == (1, 2)
    assert A.check_feasible(inst, (2, 1))


def test_waiting_does_not_change_the_cost():
    inst, pi = line([(30, 40)])
    r = A.price(inst, pi, 1, trace=True)
    assert r.trace.labels[1].wait == 29 and r.trace.labels[1].cost == 1 - 10


def test_unreachable_everything_gives_an_empty_result_not_an_error():
    inst = S.instance_from_data([(0, 0), (5, 0)], [0, 1], [0, 0], [10, 1], 10, 9, 2, "manhattan")
    r = A.price(inst, [0, 99], 1)
    assert r.routes == () and r.best_value == 0.0 and r.generated == 1


def test_memory_k_1_allows_cycles_and_k_2_or_more_does_not_for_two_customers():
    """Zwei nahe Kunden mit hohem Dualpreis: bei k = 1 darf die Route zwischen ihnen pendeln (nichtelementar, besserer Wert), ab k = 2 = n nicht."""
    inst, pi = line([(0, 90), (0, 90)])
    elementary = 1 + 1 + 2 - 20
    assert A.price(inst, pi, 2).best_value == elementary == A.price(inst, pi, 5).best_value
    cyc = A.price(inst, pi, 1)
    assert cyc.best_value < elementary and len(set(cyc.best_route)) < len(cyc.best_route)
