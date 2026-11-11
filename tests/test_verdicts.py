"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds."""

import zfl_algorithm as A
import zfl_constants as C
import zfl_evaluation as ev


def _row(**kw):
    base = dict(w=6, routes=38, best=-18.0, best_route=(4, 1, 5), enum_best=-18.0, labels=27, dominated=6, waiting=9, wait_sum=106.0, window_out=62, same_time=3, matches=True)
    base.update(kw)
    return base


def _live(generated=1000, dominated=700, waiting=250, wait_sum=5000.0, window_out=3000, aborted=False, routes=((-5.0, (1, 2)),), n=30):
    best_value, best_route = (routes[0][0], routes[0][1]) if routes else (0.0, ())
    res = A.PriceResult(best_value, best_route, tuple(routes), generated, dominated, waiting, wait_sum, window_out, 0, aborted)
    return ev.LiveRun(ev.Settings(n=n), None, (), res, True)


# --- Zahlen setzen ---------------------------------------------------------------------------------------------------------------------------

def test_german_number_format():
    assert ev.de(71.44) == "71,4" and ev.de(-2.5, 2) == "−2,50" and ev.de_int(42510) == "42.510" and ev.de_int(999) == "999" and ev.de_int(-1234) == "−1.234"
    assert ev.num(24.0) == "24" and ev.num(24.5) == "24,5" and ev.num(-6) == "−6"


# --- Experiment 1 ----------------------------------------------------------------------------------------------------------------------------

def test_verdict_hand_names_every_count_and_the_enumeration():
    kind, text = ev.verdict_hand(_row())
    assert kind == "success"
    for part in ("Bei Breite 6", "27 Labels erzeugt", "6 davon dominiert", "9 kamen vor dem Fensterbeginn", "106 Zeiteinheiten", "62 Verlängerungen", "−18", "4-1-5", "aller 38 zulässigen Routen"):
        assert part in text, part


def test_verdict_hand_is_an_error_when_label_setting_and_enumeration_differ():
    kind, text = ev.verdict_hand(_row(matches=False, enum_best=-20.0))
    assert kind == "error" and "−20" in text and "widerspricht" in text


def test_verdict_hand_without_route():
    kind, text = ev.verdict_hand(_row(best=0.0, best_route=(), enum_best=0.0))
    assert kind == "success" and "Route keine" in text


# --- Experiment 2 ----------------------------------------------------------------------------------------------------------------------------

def test_verdict_breite_nutzen_counts_steps_and_names_values():
    rows = [dict(best=-12.0, labels=15, routes=16), dict(best=-18.0, labels=27, routes=38), dict(best=-21.0, labels=67, routes=119)]
    kind, text = ev.verdict_breite_nutzen(rows)
    assert kind == "success"
    assert "−12 ≥ −18 ≥ −21" in text and "in 2 von 2 Stufen (15 → 27 → 67)" in text and "von 16 auf 119" in text and "mit 3 Breiten" in text


def test_verdict_breite_nutzen_warns_when_the_best_value_gets_worse_and_counts_non_growing_labels():
    rows = [dict(best=-12.0, labels=30, routes=16), dict(best=-10.0, labels=20, routes=38)]
    kind, text = ev.verdict_breite_nutzen(rows)
    assert kind == "warning" and "nicht in jeder Stufe" in text and "in 0 von 1 Stufen" in text
    assert ev.verdict_breite_nutzen([dict(best=-5.0, labels=9, routes=3), dict(best=-5.0, labels=9, routes=3)])[0] == "success"   # gleich bleibt erlaubt


# --- Experiment 3 ----------------------------------------------------------------------------------------------------------------------------

def test_verdict_live_numbers_and_waiting_threshold():
    kind, text = ev.verdict_live(_live())
    assert kind == "info"
    for part in ("30 Kunden erzeugt 1.000 Labels", "70,0 % davon werden dominiert", "25,0 % kommen vor dem Fensterbeginn an", "im Mittel 20,0 Zeiteinheiten",
                 "3,00 Verlängerungen", "Warten ist häufig", "−5,0"):
        assert part in text, part
    assert "Warten ist selten" in ev.verdict_live(_live(waiting=99))[1]                      # 9,9 %
    assert "Warten ist häufig" in ev.verdict_live(_live(waiting=100))[1]                     # genau 10,0 % zählt als häufig
    assert float(C.WAIT_RARE_PERCENT) == 10.0


def test_verdict_live_without_negative_route_and_aborted():
    kind, text = ev.verdict_live(_live(routes=()))
    assert kind == "warning" and "keinen Weg mit negativen reduzierten Kosten" in text
    kind, text = ev.verdict_live(_live(aborted=True))
    assert kind == "warning" and f"{ev.de_int(C.LABEL_LIMIT)} erzeugten Labels" in text


def test_verdict_live_has_no_division_by_zero_for_zero_waiting():
    live = _live(waiting=0)
    assert live.wait_mean == 0.0 and "0,0 % kommen" in ev.verdict_live(live)[1]


# --- Experiment 4 ----------------------------------------------------------------------------------------------------------------------------

def _band(medians, typ="zufällig"):
    return [dict(breite=w, median=m, typ=typ) for w, m in zip((20, 40, 70), medians)]


def test_verdict_band_threshold_is_inclusive_at_1_5():
    kind, text = ev.verdict_band({"zufällig": _band([100, 150, 225])})
    assert kind == "success" and "in 2 von 2 Stufen" in text and "kleinster Faktor 1,50, größter 1,50" in text
    kind, text = ev.verdict_band({"zufällig": _band([100, 149, 225])})
    assert kind == "info" and "in 1 von 2 Stufen" in text and "gleichauf" in text


def test_verdict_band_names_both_types():
    kind, text = ev.verdict_band({"zufällig": _band([100, 200, 400]), "gruppiert": _band([10, 20, 40], "gruppiert")})
    assert kind == "success" and "zufällig: in 2 von 2" in text and "gruppiert: in 2 von 2" in text and "größter 2,00" in text


# --- Experiment 5 ----------------------------------------------------------------------------------------------------------------------------

def _wait_rows(shares):
    return [dict(breite=w, wartet_mittel_prozent=s) for w, s in zip((20, 40, 70, 100), shares)]


def test_verdict_waiting_threshold_is_exclusive_at_10_percent():
    text = ev.verdict_waiting({"zufällig": _wait_rows([70.0, 20.0, 9.9, 5.0]), "gruppiert": _wait_rows([80.0, 60.0, 30.0, 10.0])})[1]
    assert "zufällig: ab Breite 70 (9,9 %)" in text and "gruppiert: in keiner gemessenen Breite" in text      # genau 10,0 % ist nicht selten


def test_verdict_waiting_counts_only_the_last_run_below_the_threshold():
    """Steigt der Anteil später wieder über 10 %, zählt erst die Breite, ab der er dauerhaft darunter bleibt."""
    assert "ab Breite 100 (9,5 %)" in ev.verdict_waiting({"zufällig": _wait_rows([70.0, 5.0, 12.0, 9.5])})[1]
