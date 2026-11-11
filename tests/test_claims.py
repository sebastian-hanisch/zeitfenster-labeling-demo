"""Jede Zahl der README steht hier (DEMO-PLAYBOOK §4): nachgerechnet an den festen Zufalls-Seeds, aus den festen Messreihen in data/ oder als Band.

Wie jede Zahl geprüft ist, steht in der Tabelle „Zahl → Test“ der README. Drei Arten:
* exakt: Zählungen (ganze Zahlen) des Kerns an festen Zufalls-Seeds, hier neu gerechnet;
* Messreihe: Zahlen aus data/band_p03.json und data/band_v1.json. Die Tabellen der README werden wortgleich aus diesen Dateien erzeugt und hier gesucht; die Dateien stammen aus den
  Rohausgaben der Vormessung (jede Zeile mit Quelle). Ein Teil der Zeilen wird hier neu gerechnet (Stichprobe), der Rest steht nur in der Datei;
* Band: die Spaltenerzeugung hängt von den Dualpreisen des LP-Lösers ab, die Label-Zahl wird deshalb nur in einem Band nachgerechnet, die Schranke (der LP-Wert) genau.
Zeiten werden nicht festgeschrieben."""

import importlib.util
import json
import statistics
from pathlib import Path

import pytest

import zfl_algorithm as A
import zfl_constants as C
import zfl_evaluation as ev
import zfl_scenario as S
import zfl_texts as T

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
VORMESSUNG = ROOT.parent / "label-setting-planung" / "vormessung"


# --- Tabellen der README stehen wortgleich dort -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("typ", C.TYPES)
def test_readme_has_the_band_table_verbatim(typ):
    assert ev.band_table_markdown(typ) in README


def test_readme_has_the_hand_table_verbatim():
    assert ev.hand_table_markdown() in README


def test_readme_has_the_v1_table_verbatim():
    assert ev.v1_table_markdown() in README


def test_readme_has_the_assumptions_text_of_the_app_verbatim():
    assert T.ASSUMPTIONS_MARKDOWN.strip() in README


# --- Messreihe eines Pricing-Aufrufs: Stichprobe neu gerechnet ---------------------------------------------------------------------------------

def _band_cell(typ, width):
    labs, doms, waits, wavg, fo = [], [], [], [], []
    for seed in C.BAND_SEEDS:
        inst = S.make_instance(C.BAND_N, seed, width, clustered=typ == "gruppiert")
        r = A.price(inst, S.first_round_duals(inst), C.BAND_K)
        labs.append(r.generated)
        doms.append(r.dominated / r.generated)
        waits.append(r.waiting / r.generated)
        wavg.append(r.wait_sum / r.waiting if r.waiting else 0.0)
        fo.append(r.window_out / r.generated)
    return dict(median=statistics.median(labs), mittel=statistics.mean(labs), max=max(labs), dom=100 * statistics.mean(doms), wait=100 * statistics.mean(waits),
                wavg=statistics.mean(wavg), fo=statistics.mean(fo))


RECOMPUTED = [(typ, w) for typ in C.TYPES for w in (20, 40, 70, 100)] + [("zufällig", 150)]


@pytest.mark.parametrize("typ,width", RECOMPUTED)
def test_band_row_is_reproduced_at_the_fixed_seeds(typ, width):
    """12 Instanzen (Zufalls-Seeds 0 bis 11), 30 Kunden, ng-Gedächtnis 5: jede Spalte der Zeile, in der Genauigkeit der Datei. Nicht neu gerechnet werden (zu langsam für die Suite): gruppiert bei 150 und 200, zufällig bei 200."""
    row = next(r for r in ev.band_p03_rows(typ) if r["breite"] == width)
    cell = _band_cell(typ, width)
    assert f"{cell['median']:.0f}" == str(row["median"])
    assert f"{cell['mittel']:.1f}" == f"{row['mittel']:.1f}"
    assert cell["max"] == row["max"]
    assert f"{cell['dom']:.1f}" == f"{row['dominiert_mittel_prozent']:.1f}"
    assert f"{cell['wait']:.1f}" == f"{row['wartet_mittel_prozent']:.1f}"
    assert f"{cell['wavg']:.1f}" == f"{row['wartezeit_je_wartendem_label_mittel']:.1f}"
    assert f"{cell['fo']:.2f}" == f"{row['fenster_aus_je_label_mittel']:.2f}"


def test_the_largest_instance_of_the_band_at_width_150_clustered():
    """Die größte der 12 Instanzen bei gruppiert, Breite 150 (Zufalls-Seed 5) hat genau so viele Labels wie das Maximum der Datei."""
    inst = S.make_instance(30, 5, 150, clustered=True)
    assert A.price(inst, S.first_round_duals(inst), 5).generated == next(r for r in ev.band_p03_rows("gruppiert") if r["breite"] == 150)["max"]


def test_band_files_equal_the_raw_output_of_the_pre_measurement_if_it_is_there():
    """Nur lokal, wo der Ordner der Vormessung neben dem Demo-Ordner liegt: erneutes Einlesen der Rohausgaben gibt dieselben Dateien."""
    log, raw = VORMESSUNG / "run_p03.log", VORMESSUNG / "out_v1_n30.txt"
    if not (log.exists() and raw.exists()):
        pytest.skip("Rohausgaben der Vormessung liegen nicht neben dem Demo-Ordner")
    spec = importlib.util.spec_from_file_location("bands_aus_vormessung", ROOT / "tools" / "bands_aus_vormessung.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.parse_p03(log)["zeilen"] == ev.load_band_p03()["zeilen"]
    assert mod.parse_v1(raw)["zeilen"] == ev.load_band_v1()["zeilen"]


def test_band_files_have_the_documented_shape_and_a_source_in_every_row():
    p03, v1 = ev.load_band_p03(), ev.load_band_v1()
    assert len(p03["zeilen"]) == 12 and len(v1["zeilen"]) == 108
    assert p03["bedingungen"]["instanzen_je_zelle"] == 12 and v1["bedingungen"]["instanzen_je_zelle"] == 6
    assert all(r["quelle"].startswith("run_p03.log, Zeile") for r in p03["zeilen"])
    assert all(r["quelle"].startswith("out_v1_n30.txt, Zeile") for r in v1["zeilen"])
    assert {(r["breite"], r["k"], r["seed"]) for r in v1["zeilen"]} == {(w, k, s) for w in C.V1_WIDTHS for k in C.V1_KS for s in C.V1_SEEDS}


# --- Aussagen über den Verlauf der Messreihe (jede mit Zählung) -------------------------------------------------------------------------------

@pytest.mark.parametrize("typ", C.TYPES)
def test_every_trend_sentence_of_the_readme_holds_in_all_five_steps(typ):
    """„steigt“ oder „fällt“ von Breite zu Breite gilt in allen 5 Stufen beider Typen: Median und dominierter Anteil steigen, der wartende Anteil, die Wartezeit je wartendem Label und
    die Fenster-Aus je Label fallen."""
    rows = ev.band_p03_rows(typ)
    pairs = list(zip(rows, rows[1:]))
    assert len(pairs) == 5
    assert all(b["median"] > a["median"] for a, b in pairs)
    assert all(b["dominiert_mittel_prozent"] > a["dominiert_mittel_prozent"] for a, b in pairs)
    assert all(b["wartet_mittel_prozent"] < a["wartet_mittel_prozent"] for a, b in pairs)
    assert all(b["wartezeit_je_wartendem_label_mittel"] < a["wartezeit_je_wartendem_label_mittel"] for a, b in pairs)
    assert all(b["fenster_aus_je_label_mittel"] < a["fenster_aus_je_label_mittel"] for a, b in pairs)


def test_growth_numbers_of_the_readme():
    z, g = ev.band_p03_rows("zufällig"), ev.band_p03_rows("gruppiert")
    fz, fg = z[-1]["median"] / z[0]["median"], g[-1]["median"] / g[0]["median"]
    assert (z[0]["median"], z[-1]["median"], g[0]["median"], g[-1]["median"]) == (1413, 42510, 2870, 68216)
    assert (ev.de(fz), ev.de(fg), round(fg), round(fz)) == ("30,1", "23,8", 24, 30)
    for text in ("Faktor 30,1", "Faktor 23,8", "24- bis 30-Fache"):
        assert text in README
    factors = [f for t in C.TYPES for _, _, f in ev.band_factors(ev.band_p03_rows(t))]
    assert (ev.de(min(factors), 2), ev.de(max(factors), 2), len(factors)) == ("1,62", "2,16", 10)
    assert "1,6 bis 2,2" in README
    assert all(f >= C.GROWTH_FACTOR for f in factors)                                   # „in allen 10 Stufen mindestens das 1,5-Fache“


def test_clustered_median_is_larger_than_random_at_every_width_and_maximum_to_median():
    z, g = ev.band_p03_rows("zufällig"), ev.band_p03_rows("gruppiert")
    assert all(b["median"] > a["median"] for a, b in zip(z, g))
    row = next(r for r in g if r["breite"] == 100)
    assert (row["median"], row["max"], ev.de(row["max"] / row["median"])) == (20414, 61378, "3,0")


def test_waiting_becomes_rare_from_these_widths_on():
    z, g = ev.band_p03_rows("zufällig"), ev.band_p03_rows("gruppiert")
    assert [r["breite"] for r in z if r["wartet_mittel_prozent"] < 10] == [150, 200] and [r["breite"] for r in g if r["wartet_mittel_prozent"] < 10] == [200]
    kind, text = ev.verdict_waiting({"zufällig": z, "gruppiert": g})
    assert "zufällig: ab Breite 150 (7,5 %)" in text and "gruppiert: ab Breite 200 (9,2 %)" in text
    assert "ab Breite 150 (7,5 %)" in README and "ab Breite 200 (9,2 %)" in README


# --- Ganze Spaltenerzeugung (V1) -------------------------------------------------------------------------------------------------------------

def test_v1_numbers_of_the_readme_equal_the_aggregate_of_the_raw_rows():
    """Median der Labels der fertigen Läufe (6 Instanzen je Zelle), wie ihn die Auswertung der Vormessung ausweist (zweite, unabhängig geführte Zusammenfassung)."""
    expected = {(40, 1): 16938, (40, 3): 20525, (40, 5): 20904, (40, 8): 24998, (40, 12): 25650, (40, 30): 40175,
                (100, 1): 57330, (100, 3): 71951, (100, 5): 92038, (100, 8): 108188, (100, 12): 127900, (100, 30): 140285,
                (200, 1): 160456, (200, 3): 282955, (200, 5): 348904, (200, 8): 424689, (200, 12): 548908}
    for (w, k), labels in expected.items():
        assert f"{ev.v1_median(w, k):.0f}" == str(labels), (w, k)          # gerade Läufe-Zahl: Mittel der beiden mittleren Werte, wie die Auswertung auf ganze Zahlen gerundet
    assert ev.v1_median(200, 30) is None
    aborted = {(r["breite"], r["k"]): r["abgebrochen"] for r in ev.v1_table()}
    assert aborted[(100, 30)] == 3 and aborted[(200, 30)] == 6 and sum(v for key, v in aborted.items() if key[1] != 30) == 0
    assert (ev.de(ev.v1_median(200, 1) / ev.v1_median(40, 1)), ev.de(ev.v1_median(200, 5) / ev.v1_median(40, 5))) == ("9,5", "16,7")
    for text in ("9,5-Fache", "16,7-Fache"):
        assert text in README


def _colgen(inst, k):
    """Spaltenerzeugung wie in der Vormessung (Überdeckungs-Master, Startspalten = Einzelrouten, je Runde bis zu 15 neue Spalten); nur für diese Stichprobe."""
    np = pytest.importorskip("numpy")
    linprog = pytest.importorskip("scipy.optimize").linprog
    n = inst.n

    def cost(r):
        return sum(inst.d[a][b] for a, b in zip((0,) + r, r + (0,)))

    cols = [(i,) for i in range(1, n + 1)]
    costs = [cost(r) for r in cols]
    generated, iterations = 0, 0
    while True:
        iterations += 1
        matrix = np.zeros((n, len(cols)))
        for c, r in enumerate(cols):
            for i in r:
                matrix[i - 1, c] += 1
        res = linprog(costs, A_ub=-matrix, b_ub=-np.ones(n), bounds=(0, None), method="highs")
        pi = [0.0] + list(-res.ineqlin.marginals)
        priced = A.price(inst, pi, k)
        generated += priced.generated
        have = set(cols)
        fresh = [r for _, r in priced.routes if r not in have]
        if not fresh:
            return res.fun, iterations, len(cols), generated
        for r in fresh:
            cols.append(r)
            costs.append(cost(r))


@pytest.mark.parametrize("width,seed,k", [(40, 0, 1), (40, 0, 5), (40, 1, 1), (40, 2, 3), (100, 0, 1), (100, 0, 5)])
def test_v1_sample_is_reproduced_as_a_band(width, seed, k):
    """Stichprobe der ganzen Spaltenerzeugung: die Schranke (LP-Wert) genau auf 4 Stellen, Iterationen, Spalten und Labels in einem Band von ±25 %, weil die Dualpreise eines
    entarteten LPs vom Löser und seiner Version abhängen können."""
    ref = next(r for r in ev.load_band_v1()["zeilen"] if (r["breite"], r["seed"], r["k"]) == (width, seed, k))
    bound, iterations, columns, labels = _colgen(S.make_instance(30, seed, width), k)
    assert bound == pytest.approx(ref["schranke"], abs=1e-3)
    for got, want in ((iterations, ref["iterationen"]), (columns, ref["spalten"]), (labels, ref["labels"])):
        assert 0.75 * want <= got <= 1.25 * want, (got, want)


# --- Handbeispiel -----------------------------------------------------------------------------------------------------------------------------

def test_hand_example_numbers_of_the_readme():
    rows = {r["w"]: r for r in ev.hand_overview()}
    assert [rows[w]["labels"] for w in C.HAND_WIDTHS] == [15, 27, 67, 159, 272] and [rows[w]["routes"] for w in C.HAND_WIDTHS] == [16, 38, 119, 292, 686]
    assert [rows[w]["best"] for w in C.HAND_WIDTHS] == [-12, -18, -21, -26, -28] and all(r["matches"] for r in rows.values())
    labs = [rows[w]["labels"] for w in C.HAND_WIDTHS]
    bests = [rows[w]["best"] for w in C.HAND_WIDTHS]
    assert all(b > a for a, b in zip(labs, labs[1:])) and all(b <= a for a, b in zip(bests, bests[1:]))     # in diesem Beispiel, nicht allgemein


def test_three_of_six_dominations_at_width_6_have_the_same_time_because_both_labels_wait():
    run = ev.hand_run(6)
    recs = run.result.trace.labels
    same = [r for r in recs if r.same_time]
    assert (run.result.same_time, run.result.dominated, len(same)) == (3, 6, 3)
    for r in same:
        assert r.wait > 0 and recs[r.by].wait > 0 and r.time == recs[r.by].time        # beide warten bis zum Fensterbeginn desselben Kunden
    assert sorted((r.serial, r.by) for r in same) == [(7, 1), (9, 4), (10, 5)]


def test_first_label_waits_22_and_the_extension_to_customer_2_fails():
    recs = ev.hand_run(6).result.trace.labels
    assert recs[1].wait == 22 and recs[1].cost == -6 and recs[7].path == (2, 1)
    assert any(w.parent == 3 and w.node == 2 and w.arrival == 32 and w.due == 17 for w in ev.hand_run(6).result.trace.window_out)


def test_the_label_list_of_the_app_has_one_row_per_generated_label():
    for w in C.HAND_WIDTHS:
        run = ev.hand_run(w)
        assert len(ev.hand_label_rows(run)) == run.result.generated and len(ev.hand_window_out_rows(run)) == run.result.window_out


# --- Sätze der README über Zeit (Messung dieser README, nicht im Test) ----------------------------------------------------------------------

def test_the_readme_labels_its_timing_sentence_as_not_tested():
    assert "Messung dieser README, nicht im Test" in README and "2,3 Sekunden" in README


# --- Aussagen nach unabhängiger Prüfung: gerundete Mediane, Einschränkungen im Text ---------------------------------------------------------------

def test_the_readme_names_the_rounded_medians_of_the_band_tables():
    """Die Tabellen zeigen ganze Zahlen; die tatsächlichen Mediane sind Mittel zweier Werte: 2.869,5 und 5.274,5 (gruppiert, Breite 20 und 40), 22.869,5 (zufällig, Breite 150)."""
    assert _band_cell("gruppiert", 20)["median"] == 2869.5 and _band_cell("gruppiert", 40)["median"] == 5274.5 and _band_cell("zufällig", 150)["median"] == 22869.5
    for stueck in ("2.870 statt 2.869,5", "5.274 statt 5.274,5", "22.870 statt 22.869,5"):
        assert stueck in README, stueck


def test_the_widening_sentence_names_the_measured_series_and_the_elementary_row_its_three_finished_runs():
    assert "Je breiter die Fenster, desto mehr Labels (in den gemessenen Reihen)" in README
    assert "In den gemessenen Reihen wächst die Label-Zahl mit der Breite" in README
    row = next(r for r in ev.v1_table() if r["breite"] == 100 and r["k"] == C.BAND_N)
    assert (row["laeufe"], row["abgebrochen"]) == (6, 3) and "beruht daher nur auf den 3 fertigen, schnelleren Läufen" in README
