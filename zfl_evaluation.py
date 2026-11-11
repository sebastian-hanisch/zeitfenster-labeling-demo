"""Kennzahlen, feste Messreihen, Verdikt-Logik. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text).

Zahlen werden deutsch gesetzt (Dezimalkomma, Tausenderpunkt). Messgröße ist die Zahl der erzeugten Labels, nie die Zeit.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import median

import zfl_algorithm as A
import zfl_constants as C
import zfl_scenario as S

DATA = Path(__file__).resolve().parent / "data"


# --- Zahlen setzen ---------------------------------------------------------------------------------------------------------------------------

def de(x: float, nd: int = 1) -> str:
    """Deutsche Schreibweise: Dezimalkomma, Tausenderpunkt (ab vier Stellen vor dem Komma), ein echtes Minuszeichen."""
    return f"{x:,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", ".").replace("-", "−")


def de_int(x) -> str:
    """Ganze Zahl mit Tausenderpunkt (ab vier Stellen); ein echtes Minuszeichen."""
    return f"{int(round(x)):,}".replace(",", ".").replace("-", "−")


def num(x: float) -> str:
    """Zeit- und Kostenwerte des Handbeispiels: ganze Zahlen ohne Nachkommastellen, sonst eine Stelle."""
    return de_int(x) if float(x).is_integer() else de(x, 1)


# --- Einstellungen ---------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    hand_w: int = C.DEFAULT_HAND_WIDTH
    n: int = C.DEFAULT_N
    breite: int = C.DEFAULT_WIDTH
    typ: str = C.DEFAULT_TYPE
    k: int = C.DEFAULT_K
    seed: int = C.DEFAULT_SEED

    @property
    def clustered(self) -> bool:
        return self.typ == "gruppiert"


# --- Handbeispiel ----------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class HandRun:
    w: int
    inst: object
    pi: tuple
    result: object            # PriceResult mit Protokoll
    routes: tuple             # alle zulässigen Routen (Aufzählung), aufsteigend nach reduzierten Kosten
    enum_best: float          # bester Wert der Aufzählung (0, wenn keine Route negative Kosten hat)

    @property
    def matches(self) -> bool:
        return self.result.best_value == self.enum_best


@lru_cache(maxsize=None)
def hand_run(w: int) -> HandRun:
    """Handbeispiel bei Fensterbreite w: Label-Setting (elementar, k = n) mit Protokoll und, als anderer Rechenweg, die Aufzählung aller zulässigen Routen."""
    inst = S.hand_instance(w)
    pi = tuple(S.hand_duals())
    result = A.price(inst, pi, inst.n, trace=True)
    routes = tuple(A.enumerate_routes(inst, pi))
    enum_best = min([rc for rc, _ in routes] + [0])
    return HandRun(w, inst, pi, result, routes, enum_best)


def hand_overview() -> list:
    """Eine Zeile je Breite des Handbeispiels: zulässige Routen, bester Wert, Labels, Dominanzen, Warten, Fenster-Aus."""
    rows = []
    for w in C.HAND_WIDTHS:
        run = hand_run(w)
        r = run.result
        rows.append({
            "w": w, "routes": len(run.routes), "best": r.best_value, "best_route": r.best_route, "enum_best": run.enum_best, "labels": r.generated,
            "dominated": r.dominated, "waiting": r.waiting, "wait_sum": r.wait_sum, "window_out": r.window_out, "same_time": r.same_time,
            "matches": run.matches,
        })
    return rows


def hand_customer_rows(inst) -> list:
    rows = []
    for i in range(1, inst.n + 1):
        e, l = inst.window(i)
        rows.append({"Kunde": i, "Punkt": f"({inst.pts[i][0]}, {inst.pts[i][1]})", "Entfernung zum Depot": num(inst.d[0][i]), "Last": inst.dem[i],
                     "Fenster": f"[{num(e)}, {num(l)}]", "Dualpreis": num(C.HAND_DUALS[i])})
    return rows


def visited_text(mem: int, n: int) -> str:
    return "{" + ", ".join(str(i) for i in range(1, n + 1) if (mem >> i) & 1) + "}"


def decision_text(rec) -> str:
    same = " (nach dem Warten gleiche Zeit)" if rec.same_time else ""
    if rec.status == "dominiert":
        return f"dominiert von L{rec.by}{same}"
    if rec.status == "ersetzt":
        return f"entfällt später, dominiert vom neuen L{rec.by}{same}"
    return "bleibt"


def hand_label_rows(run: HandRun) -> list:
    """Das Protokoll als Tabelle: ein Label je Zeile, mit Ankunft, Fenster, Wartezeit und der Entscheidung der Dominanz."""
    inst = run.inst
    rows = []
    for rec in run.result.trace.labels:
        if rec.serial == 0:
            rows.append({"Label": "L0", "Weg": "Start im Depot", "Kunde": "", "Ankunft": "", "Fenster": "", "Wartet": "", "Zeit": num(0), "Kosten": num(0),
                         "besucht": "{}", "Entscheidung": "Start"})
            continue
        e, l = inst.window(rec.node)
        rows.append({
            "Label": f"L{rec.serial}", "Weg": "-".join(map(str, rec.path)), "Kunde": str(rec.node), "Ankunft": num(rec.arrival), "Fenster": f"[{num(e)}, {num(l)}]",
            "Wartet": num(rec.wait) if rec.wait else "nein", "Zeit": num(rec.time), "Kosten": num(rec.cost), "besucht": visited_text(rec.mem, inst.n),
            "Entscheidung": decision_text(rec),
        })
    return rows


def hand_window_out_rows(run: HandRun) -> list:
    return [{"Von Label": f"L{w.parent}", "Nach Kunde": w.node, "Ankunft": num(w.arrival), "Fensterende": num(w.due),
             "Entscheidung": f"Ankunft {num(w.arrival)} > Fensterende {num(w.due)}: unzulässig"} for w in run.result.trace.window_out]


def timeline_stops(inst, route) -> list:
    """Halte einer Route für den Zeitstrahl: Fahrt, Warten, Bedienung, Fenster (aus dem Fahrplan-Prüfer, nicht aus dem Label-Setting)."""
    return A.schedule(inst, route)[0]


# --- Instanz mit Größenregler ----------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class LiveRun:
    settings: Settings
    inst: object
    pi: tuple
    result: object
    valid: bool               # die beste Route besteht den unabhängigen Prüfer und ihre Kosten stimmen

    @property
    def dominated_percent(self) -> float:
        return 100.0 * self.result.dominated / self.result.generated

    @property
    def waiting_percent(self) -> float:
        return 100.0 * self.result.waiting / self.result.generated

    @property
    def wait_mean(self) -> float:
        return self.result.wait_sum / self.result.waiting if self.result.waiting else 0.0

    @property
    def window_out_per_label(self) -> float:
        return self.result.window_out / self.result.generated


def live_run(s: Settings, max_labels: int = C.LABEL_LIMIT) -> LiveRun:
    """Ein Pricing-Aufruf mit den Dualpreisen der ersten Runde auf einer Solomon-artigen Instanz."""
    inst = S.make_instance(s.n, s.seed, s.breite, clustered=s.clustered)
    pi = tuple(S.first_round_duals(inst))
    res = A.price(inst, pi, s.k, max_labels=max_labels)
    valid = True
    if res.best_route:
        elementary = s.k >= s.n
        valid = A.check_feasible(inst, res.best_route, elementary) and abs(A.reduced_cost(inst, pi, res.best_route) - res.best_value) < 1e-6
    return LiveRun(s, inst, pi, res, valid)


# --- Feste Messreihen ------------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def load_band_p03() -> dict:
    return json.loads((DATA / "band_p03.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_band_v1() -> dict:
    return json.loads((DATA / "band_v1.json").read_text(encoding="utf-8"))


def band_p03_rows(typ: str) -> list:
    return sorted((r for r in load_band_p03()["zeilen"] if r["typ"] == typ), key=lambda r: r["breite"])


def band_factors(rows) -> list:
    """Faktor des Medians von Stufe zu Stufe: (Breite davor, Breite danach, Faktor)."""
    return [(a["breite"], b["breite"], b["median"] / a["median"]) for a, b in zip(rows, rows[1:])]


def band_reference(s: Settings):
    """Die Zeile der festen Messreihe zu den Reglern, wenn sie passt (n = 30, ng-Gedächtnis 5, Breite aus der Reihe), sonst None."""
    if s.n != C.BAND_N or s.k != C.BAND_K or s.breite not in C.BAND_WIDTHS:
        return None
    return next(r for r in band_p03_rows(s.typ) if r["breite"] == s.breite)


def v1_table() -> list:
    """V1 je (Breite, k): Läufe, abgebrochene Läufe, Median der Labels und Mittel des Anteils dominierter Labels über die fertigen Läufe, Median der Sekunden
    (nur zur Information)."""
    rows = load_band_v1()["zeilen"]
    out = []
    for w in C.V1_WIDTHS:
        for k in C.V1_KS:
            cell = [r for r in rows if r["breite"] == w and r["k"] == k]
            done = [r for r in cell if not r["abgebrochen"]]
            out.append({
                "breite": w, "k": k, "laeufe": len(cell), "abgebrochen": len(cell) - len(done),
                "median_labels": median(r["labels"] for r in done) if done else None,
                "dominiert_prozent": 100 * sum(r["dominiert_anteil"] for r in done) / len(done) if done else None,
                "median_sekunden": median(r["pricing_sekunden"] for r in done) if done else None,
            })
    return out


def v1_median(w: int, k: int):
    return next(r["median_labels"] for r in v1_table() if r["breite"] == w and r["k"] == k)


# --- Verdikte (reine Funktionen) -------------------------------------------------------------------------------------------------------------

def verdict_hand(row: dict) -> tuple:
    """Verdikt zu Experiment 1: die Zählung des Handbeispiels bei einer Breite, geprüft gegen die Aufzählung aller zulässigen Routen."""
    route = "-".join(map(str, row["best_route"])) or "keine"
    text = (f"Bei Breite {row['w']}: {de_int(row['labels'])} Labels erzeugt, {de_int(row['dominated'])} davon dominiert, {de_int(row['waiting'])} kamen vor dem "
            f"Fensterbeginn an und warteten (zusammen {num(row['wait_sum'])} Zeiteinheiten), {de_int(row['window_out'])} Verlängerungen scheiterten am Fensterende. "
            f"Bester Wert {num(row['best'])} (Route {route}), ")
    if row["matches"]:
        return "success", text + f"derselbe Wert wie in der Aufzählung aller {de_int(row['routes'])} zulässigen Routen."
    return "error", text + f"aber die Aufzählung aller {de_int(row['routes'])} zulässigen Routen findet {num(row['enum_best'])}: Das Label-Setting widerspricht der Aufzählung."


def verdict_breite_nutzen(rows: list) -> tuple:
    """Verdikt zu Experiment 2 (Handbeispiel): wird der beste Wert mit breiteren Fenstern nie schlechter, und wie wächst die Label-Zahl? Nur für die
    Breiten dieser Zeilen; die Label-Zahl wächst nicht allgemein monoton (ein zusätzliches Label kann andere dominieren), sie wird gezählt."""
    bests = [r["best"] for r in rows]
    labels = [r["labels"] for r in rows]
    never_worse = all(a >= b for a, b in zip(bests, bests[1:]))
    grows = sum(1 for a, b in zip(labels, labels[1:]) if b > a)
    steps = len(labels) - 1
    best_part = (f"Der beste Wert wird mit jeder breiteren Stufe nie schlechter ({' ≥ '.join(num(b) for b in bests)})" if never_worse
                 else f"Der beste Wert wird nicht in jeder Stufe besser oder gleich ({', '.join(num(b) for b in bests)})")
    text = (f"{best_part}; die Zahl der Labels steigt in {grows} von {steps} Stufen ({' → '.join(de_int(x) for x in labels)}), die Zahl der zulässigen Routen von "
            f"{de_int(rows[0]['routes'])} auf {de_int(rows[-1]['routes'])}. Das gilt für dieses Beispiel mit {len(rows)} Breiten.")
    return ("success" if never_worse else "warning"), text


def verdict_live(run: LiveRun) -> tuple:
    """Verdikt zu Experiment 3: Zählung eines Pricing-Aufrufs; Abbruch und fehlende verbessernde Route haben eigene Meldungen."""
    r = run.result
    if r.aborted:
        return "warning", (f"Abgebrochen nach {de_int(C.LABEL_LIMIT)} erzeugten Labels: Diese Rechnung ist für die App zu groß. Kleinere Breite oder weniger Kunden wählen.")
    wait_text = "Warten ist selten (unter 10 % der Labels)." if run.waiting_percent < C.WAIT_RARE_PERCENT else "Warten ist häufig (mindestens 10 % der Labels)."
    head = (f"Ein Pricing-Aufruf mit {run.settings.n} Kunden erzeugt {de_int(r.generated)} Labels; {de(run.dominated_percent)} % davon werden dominiert, "
            f"{de(run.waiting_percent)} % kommen vor dem Fensterbeginn an und warten (im Mittel {de(run.wait_mean)} Zeiteinheiten), je erzeugtem Label scheitern "
            f"{de(run.window_out_per_label, 2)} Verlängerungen am Fensterende. {wait_text} ")
    if not r.routes:
        return "warning", head + "Es gibt keinen Weg mit negativen reduzierten Kosten: bei diesen Fenstern lohnt sich keine neue Route."
    return "info", head + f"Beste reduzierte Kosten einer Route: {de(r.best_value)}."


def verdict_band(rows_by_type: dict) -> tuple:
    """Verdikt zu Experiment 4: wächst der Median der Labels von Breitenstufe zu Breitenstufe um mindestens den Faktor 1,5? Zählung je Typ."""
    parts, all_grow = [], True
    for typ, rows in rows_by_type.items():
        factors = [f for _, _, f in band_factors(rows)]
        big = sum(1 for f in factors if f >= C.GROWTH_FACTOR)
        all_grow = all_grow and big == len(factors)
        parts.append(f"{typ}: in {big} von {len(factors)} Stufen um mindestens das {de(C.GROWTH_FACTOR)}-Fache (kleinster Faktor {de(min(factors), 2)}, größter {de(max(factors), 2)})")
    text = "Der Median der erzeugten Labels wächst, " + "; ".join(parts) + "."
    if all_grow:
        return "success", text
    return "info", text + " Wo der Faktor darunter liegt, sind die Stufen gleichauf."


def verdict_waiting(rows_by_type: dict) -> tuple:
    """Verdikt zu Experiment 5: ab welcher gemessenen Breite (und bei jeder größeren) wartet weniger als ein Zehntel der Labels?"""
    parts = []
    for typ, rows in rows_by_type.items():
        first = next((r for i, r in enumerate(rows) if all(x["wartet_mittel_prozent"] < C.WAIT_RARE_PERCENT for x in rows[i:])), None)
        if first is None:
            parts.append(f"{typ}: in keiner gemessenen Breite")
        else:
            parts.append(f"{typ}: ab Breite {first['breite']} ({de(first['wartet_mittel_prozent'])} %)")
    return "info", "Weniger als 10 % der Labels warten (Mittel über 12 Instanzen), " + "; ".join(parts) + "."


# --- Tabellen für die README (der Test sucht sie wortgleich dort) ----------------------------------------------------------------------------

def band_table_markdown(typ: str) -> str:
    """Messreihe eines Pricing-Aufrufs als Markdown-Tabelle (Zahlen aus data/band_p03.json)."""
    lines = ["| Breite | Median | Mittel | Maximum | dominiert (%) | wartet (%) | Wartezeit je wartendem Label | Fenster-Aus je Label |", "|---|---|---|---|---|---|---|---|"]
    for r in band_p03_rows(typ):
        lines.append(f"| {r['breite']} | {de_int(r['median'])} | {de(r['mittel'])} | {de_int(r['max'])} | {de(r['dominiert_mittel_prozent'])} | {de(r['wartet_mittel_prozent'])} | "
                     f"{de(r['wartezeit_je_wartendem_label_mittel'])} | {de(r['fenster_aus_je_label_mittel'], 2)} |")
    return "\n".join(lines)


def hand_table_markdown() -> str:
    """Handbeispiel bei den fünf Breiten als Markdown-Tabelle (Zählungen des Kerns; die Aufzählung liefert die Zahl der zulässigen Routen)."""
    lines = ["| Breite w | zulässige Routen | bester Wert | Route | Labels | dominiert | wartend | Wartezeit insgesamt | Fenster-Aus | Dominanzen bei gleicher Zeit |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in hand_overview():
        lines.append(f"| {r['w']} | {r['routes']} | {num(r['best'])} | {'-'.join(map(str, r['best_route']))} | {r['labels']} | {r['dominated']} | {r['waiting']} | {num(r['wait_sum'])} | "
                     f"{r['window_out']} | {r['same_time']} |")
    return "\n".join(lines)


def v1_table_markdown() -> str:
    """Ganze Spaltenerzeugung (V1) als Markdown-Tabelle: Median der Labels der fertigen Läufe je Breite und ng-Gedächtnis."""
    lines = ["| Breite | k | Läufe | abgebrochen | Median der Labels (fertige Läufe) | dominiert, Mittel (%) |", "|---|---|---|---|---|---|"]
    for r in v1_table():
        k = "elementar" if r["k"] == C.BAND_N else str(r["k"])
        med = "–" if r["median_labels"] is None else de_int(r["median_labels"])
        dom = "–" if r["dominiert_prozent"] is None else de(r["dominiert_prozent"])
        lines.append(f"| {r['breite']} | {k} | {r['laeufe']} | {r['abgebrochen']} | {med} | {dom} |")
    return "\n".join(lines)
