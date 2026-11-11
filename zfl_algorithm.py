"""Kern der Demo (nur Standardbibliothek): Label-Setting im Pricing-Problem mit Zeitfenstern.

Gesucht ist eine Route vom Depot über Kunden zurück zum Depot, die die reduzierten Kosten (Fahrtkosten minus Dualpreise der besuchten Kunden)
klein macht. Jeder Kunde hat ein Zeitfenster [e, l]: wer vor e ankommt, wartet bis e (das kostet nichts), wer nach l ankommt, darf nicht bedienen.

Ein Label beschreibt einen Teilweg: Zeit t (nach dem Warten), Kosten c, Last q, Gedächtnis (welche Kunden nicht noch einmal besucht werden
dürfen) und Knoten. Jede Regel ist eine eigene Funktion mit ausdrücklichen Ein- und Ausgaben (DEMO-PLAYBOOK §1b); `price` ruft sie nur der Reihe nach auf.

Messgröße ist die Zahl der erzeugten Labels, nicht die Zeit. Diese Fassung ist eine Kopie des Messkerns der Vormessung (Präfix zfl_), erweitert um Zähler
für Warten und Fenster-Aus und um eine Protokollspur für das Handbeispiel.
"""

import heapq
from dataclasses import dataclass, field

from zfl_scenario import Inst

EPS = 1e-9

# Aufbau eines Labels (Liste, weil die Dominanz das Feld DEAD später setzt):
T, C, Q, MEM, NODE, PARENT, DEAD, SERIAL = range(8)


# --- Einzelne Regeln -------------------------------------------------------------------------------------------------------------------------

def ng_masks(inst: Inst, k: int) -> list:
    """Gedächtnis-Nachbarschaft NG(j): die k nächsten Kunden von j inklusive j selbst, als Bitmaske. k = 1: nur j selbst (nur sofortige Wiederholung
    verboten); k >= n: alle Kunden (elementar, jeder Kunde höchstens einmal)."""
    masks = [0] * (inst.n + 1)
    for j in range(1, inst.n + 1):
        order = sorted(range(1, inst.n + 1), key=lambda i: (inst.d[j][i], i))
        m = 0
        for i in order[:k]:
            m |= 1 << i
        masks[j] = m | (1 << j)
    return masks


def memory_after(mem: int, ng_j: int, j: int) -> int:
    """Gedächtnis nach dem Besuch von j: nur was auch in NG(j) liegt, bleibt verboten, dazu j selbst."""
    return (mem & ng_j) | (1 << j)


def arrival_time(inst: Inst, i: int, t: float, j: int) -> float:
    """Ankunft bei j, wenn man bei i zur Zeit t fertig ist (bei i = Depot fährt man sofort los, sonst nach der Bedienung bei i)."""
    return t + (inst.svc if i != 0 else 0.0) + inst.d[i][j]


def fits_window(inst: Inst, j: int, arr: float) -> bool:
    """Zeitfenster-Regel: wer später als das Fensterende ankommt, scheidet aus (Ankunft genau zum Fensterende ist zulässig)."""
    return arr <= inst.due[j] + EPS


def service_start(inst: Inst, j: int, arr: float) -> float:
    """Warten: wer vor dem Fensterbeginn ankommt, wartet bis dahin; die Zeit des Labels ist der Beginn der Bedienung."""
    return max(arr, inst.ready[j])


def can_return(inst: Inst, i: int, t: float) -> bool:
    """Rückkehr zum Depot: nach der Bedienung bei i und der Fahrt zurück muss die Zeit höchstens H sein (genau H ist zulässig)."""
    return t + inst.svc + inst.d[i][0] <= inst.H + EPS


def dominates(a, b) -> bool:
    """a dominiert b (gleicher Knoten): a ist höchstens so teuer, höchstens so spät, belädt höchstens so viel und verbietet höchstens dieselben
    Kunden. Warten kann Zeiten zusammenfallen lassen: zwei Labels, die bis zum Fensterbeginn warten, haben danach dieselbe Zeit."""
    return a[C] <= b[C] + EPS and a[T] <= b[T] + EPS and a[Q] <= b[Q] and (a[MEM] & ~b[MEM]) == 0


# --- Protokoll (nur für das Handbeispiel) ----------------------------------------------------------------------------------------------------

@dataclass
class LabelRecord:
    serial: int
    parent: int          # Nummer des Vorgängers, -1 beim Start-Label
    path: tuple          # Kunden in Besuchsfolge
    node: int
    arrival: float       # Ankunft vor dem Warten
    wait: float          # Wartezeit (0, wenn nicht gewartet)
    time: float          # Zeit nach dem Warten
    cost: float
    load: float
    mem: int
    status: str = "bleibt"        # "bleibt", "dominiert" (beim Erzeugen) oder "ersetzt" (später vom neuen Label verdrängt)
    by: int = -1                  # Nummer des Labels, das dominiert hat
    same_time: bool = False       # dominiert bei gleicher Zeit nach dem Warten


@dataclass
class WindowOut:
    parent: int
    node: int
    arrival: float
    due: float


@dataclass
class Trace:
    labels: list = field(default_factory=list)          # LabelRecord je erzeugtem Label, in Erzeugungsreihenfolge (Index = Nummer)
    window_out: list = field(default_factory=list)      # WindowOut je am Fensterende gescheiterter Verlängerung


# --- Ergebnis --------------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class PriceResult:
    best_value: float            # beste reduzierte Kosten einer Route (0, wenn keine Route negative Kosten hat)
    best_route: tuple            # Kunden dieser Route in Besuchsfolge (leer, wenn keine negative gefunden)
    routes: tuple                # (reduzierte Kosten, Route) der besten verbessernden Routen, aufsteigend
    generated: int               # erzeugte Labels, einschließlich des Start-Labels
    dominated: int               # davon (oder später) dominierte
    waiting: int                 # erzeugte Labels, die vor dem Fensterbeginn ankamen
    wait_sum: float              # Summe der Wartezeiten dieser Labels
    window_out: int              # wegen Fensterende verworfene Verlängerungen
    same_time: int               # Dominanzen, bei denen beide Labels nach dem Warten dieselbe Zeit hatten
    aborted: bool                # Rechnung wegen max_labels abgebrochen
    trace: object = None         # Trace, nur auf Wunsch


# --- Komposition -----------------------------------------------------------------------------------------------------------------------------

def price(inst: Inst, pi, k: int, max_routes: int = 15, max_labels: int = None, trace: bool = False) -> PriceResult:
    """Pricing mit Label-Setting nach Zeit, volle Dominanz (Kosten, Zeit, Last, Gedächtnis), Zeitfenster mit Warten.

    pi[0] = 0, pi[j] der Dualpreis von Kunde j. k: Größe der Gedächtnis-Nachbarschaft (1 = nichtelementar, n = elementar).
    Ohne max_labels läuft die Rechnung bis zum Ende; mit max_labels bricht sie nach so vielen erzeugten Labels ab (aborted = True)."""
    n = inst.n
    ng = ng_masks(inst, k)
    d = inst.d
    labels = [[0.0, 0.0, 0, 0, 0, -1, False, 0]]
    at_node = [[] for _ in range(n + 1)]
    heap = [(0.0, 0)]
    generated = 1
    dominated = waiting = window_out = same_time = 0
    wait_sum = 0.0
    ended = []
    aborted = False
    tr = Trace() if trace else None
    if tr is not None:
        tr.labels.append(LabelRecord(0, -1, (), 0, 0.0, 0.0, 0.0, 0.0, 0, 0))
    while heap:
        _, li = heapq.heappop(heap)
        L = labels[li]
        if L[DEAD]:
            continue
        if max_labels is not None and generated > max_labels:
            aborted = True
            break
        t, c, q, mem, i = L[T], L[C], L[Q], L[MEM], L[NODE]
        if i != 0 and can_return(inst, i, t):
            ended.append((c + d[i][0], li))
        for j in range(1, n + 1):
            if j == i or (mem >> j) & 1:
                continue
            q2 = q + inst.dem[j]
            if q2 > inst.Q:
                continue
            arr = arrival_time(inst, i, t, j)
            if not fits_window(inst, j, arr):
                window_out += 1
                if tr is not None:
                    tr.window_out.append(WindowOut(L[SERIAL], j, arr, inst.due[j]))
                continue
            t2 = service_start(inst, j, arr)
            c2 = c + d[i][j] - pi[j]
            m2 = memory_after(mem, ng[j], j)
            serial = generated
            generated += 1
            wait = t2 - arr
            if wait > EPS:
                waiting += 1
                wait_sum += wait
            new = [t2, c2, q2, m2, j, li, False, serial]
            if tr is not None:
                tr.labels.append(LabelRecord(serial, L[SERIAL], tr.labels[L[SERIAL]].path + (j,), j, arr, wait if wait > EPS else 0.0, t2, c2, q2, m2))
            lst = at_node[j]
            killer = None
            for oi in lst:
                O = labels[oi]
                if O[DEAD]:
                    continue
                if dominates(O, new):
                    killer = O
                    break
            if killer is not None:
                dominated += 1
                if abs(killer[T] - t2) <= EPS:
                    same_time += 1
                if tr is not None:
                    rec = tr.labels[serial]
                    rec.status, rec.by, rec.same_time = "dominiert", killer[SERIAL], abs(killer[T] - t2) <= EPS
                continue
            survivors = []
            for oi in lst:
                O = labels[oi]
                if O[DEAD]:
                    continue
                if dominates(new, O):
                    O[DEAD] = True
                    dominated += 1
                    same_time_here = abs(O[T] - t2) <= EPS
                    if same_time_here:
                        same_time += 1
                    if tr is not None:
                        rec = tr.labels[O[SERIAL]]
                        rec.status, rec.by, rec.same_time = "ersetzt", serial, same_time_here
                else:
                    survivors.append(oi)
            at_node[j] = survivors
            labels.append(new)
            idx = len(labels) - 1
            at_node[j].append(idx)
            heapq.heappush(heap, (t2, idx))
    best = {}
    for rc, li in ended:
        route = []
        x = li
        while x != -1:
            route.append(labels[x][NODE])
            x = labels[x][PARENT]
        route = tuple(reversed(route))[1:]
        if rc < -1e-7 and route not in best:
            best[route] = rc
    out = tuple(sorted(((rc, r) for r, rc in best.items()))[:max_routes])
    best_value, best_route = (out[0][0], out[0][1]) if out else (0.0, ())
    return PriceResult(best_value, best_route, out, generated, dominated, waiting, wait_sum, window_out, same_time, aborted, tr)


# --- Prüfer und Aufzählung (anderer Rechenweg als das Label-Setting) -------------------------------------------------------------------------

@dataclass(frozen=True)
class Stop:
    customer: int
    leave: float         # Zeitpunkt der Abfahrt vom Vorgänger
    arrival: float       # Ankunft
    start: float         # Beginn der Bedienung (nach dem Warten)
    wait: float
    end: float           # Ende der Bedienung
    window: tuple


def schedule(inst: Inst, route):
    """Fahrplan einer Route als Liste von Halten, ohne das Label-Setting zu benutzen: Abfahrt, Ankunft, Warten, Bedienung, Fenster.
    Gibt (Halte, Rückkehrzeit) zurück; die Zulässigkeit prüft `check_feasible`."""
    stops, leave, here = [], 0.0, 0
    for j in route:
        arr = leave + inst.d[here][j]
        start = max(arr, inst.ready[j])
        end = start + inst.svc
        stops.append(Stop(j, leave, arr, start, start - arr, end, (inst.ready[j], inst.due[j])))
        leave, here = end, j
    back = leave + inst.d[here][0] if route else 0.0
    return stops, back


def reduced_cost(inst: Inst, pi, route) -> float:
    """Reduzierte Kosten einer Route: Fahrstrecke (Depot - Kunden - Depot) minus Dualpreise der besuchten Kunden. Warten kostet nichts."""
    seq = (0,) + tuple(route) + (0,)
    return sum(inst.d[a][b] for a, b in zip(seq, seq[1:])) - sum(pi[j] for j in route)


def _prefix_feasible(inst: Inst, route, elementary: bool = True) -> bool:
    """Kunden vorhanden (bei elementary = True auch verschieden, sonst nur nicht zweimal hintereinander), Last höchstens Q, jede Ankunft höchstens zum
    Fensterende (ohne die Rückkehr zum Depot)."""
    route = tuple(route)
    if any(not 1 <= j <= inst.n for j in route):
        return False
    if elementary and len(set(route)) != len(route):
        return False
    if any(a == b for a, b in zip(route, route[1:])):
        return False
    if sum(inst.dem[j] for j in route) > inst.Q:
        return False
    stops, _ = schedule(inst, route)
    return all(s.arrival <= s.window[1] + EPS for s in stops)


def check_feasible(inst: Inst, route, elementary: bool = True) -> bool:
    """Unabhängiger Prüfer: Last höchstens Q, jede Ankunft höchstens zum Fensterende, Rückkehr höchstens H; elementar: jeder Kunde höchstens einmal
    (nichtelementar, k < n: Kunden dürfen wiederkehren, aber nicht zweimal hintereinander)."""
    if not _prefix_feasible(inst, route, elementary):
        return False
    return schedule(inst, route)[1] <= inst.H + EPS


def enumerate_routes(inst: Inst, pi) -> list:
    """Alle zulässigen elementaren Routen mit ihren reduzierten Kosten (nur für kleine Instanzen, Tiefensuche über die Besuchsfolge): die
    Gegenprobe zum Label-Setting im Handbeispiel. Sortiert nach (Kosten, Route)."""
    routes = []

    def rec(route):
        if route:
            if not _prefix_feasible(inst, route):
                return                  # Last und Ankunftszeiten wachsen beim Verlängern nur: auch jede Verlängerung ist unzulässig
            if schedule(inst, route)[1] <= inst.H + EPS:
                routes.append((reduced_cost(inst, pi, route), tuple(route)))
        for j in range(1, inst.n + 1):
            if j not in route:
                rec(route + [j])

    rec([])
    return sorted(routes)
