"""Längere Texte der App. `ASSUMPTIONS_MARKDOWN` steht wortgleich in der README (tests/test_claims.py vergleicht beide)."""

INTRO_MARKDOWN = """
Beim **Label-Setting** im Pricing sucht man eine Route vom Depot über Kunden zurück zum Depot, die möglichst günstig ist. Hat jeder Kunde ein **Zeitfenster**
[e, l], gilt: Wer vor e ankommt, **wartet** bis e (das kostet nichts), wer nach l ankommt, scheidet aus. Diese Demo zeigt an einem Handbeispiel mit 6 Kunden,
was das mit jedem einzelnen Label macht, und misst an Solomon-artigen Instanzen mit 30 Kunden, **wie stark die Fensterbreite die Zahl der erzeugten Labels
steuert**. Gezählt werden Labels, nicht Sekunden.

Unten folgen fünf Experimente (🔬), die Grenzen der Annahmen (🚧) und die Formeln (📐). Der Schnellstart in der Seitenleiste lädt Beispielszenarien.
"""

HOW_MARKDOWN = """
1. **Ein Label ist ein Teilweg** vom Depot bis zu einem Kunden: mit der Zeit t, den Kosten c (Fahrstrecke minus die **Dualpreise** der besuchten Kunden; das sind
   die Preise, die das übergeordnete Planungsproblem für das Bedienen eines Kunden bietet), der Last und einem Gedächtnis der Kunden, die nicht noch einmal
   besucht werden dürfen. Das Verfahren verlängert Labels in der Reihenfolge ihrer Zeit.
2. **Ankunft und Fensterende:** Bei der Verlängerung zu Kunde j ergibt sich die Ankunft aus Zeit, Bedienzeit und Entfernung. Liegt sie **nach dem Fensterende l**,
   scheidet die Verlängerung aus („Fenster-Aus“).
3. **Warten:** Liegt die Ankunft **vor dem Fensterbeginn e**, wartet das Label bis e. Die Zeit des Labels ist dann e, die Kosten ändern sich nicht: Warten ist
   erlaubt und kostet nichts.
4. **Dominanz:** Ein Label macht ein anderes am selben Kunden überflüssig, wenn es höchstens so teuer, höchstens so spät und höchstens so beladen ist und höchstens
   dieselben Kunden sperrt. Weil Warten nichts kostet, genügt „höchstens so spät“. Warten zwei Labels bis zum Fensterbeginn, haben beide danach **dieselbe Zeit**; dann
   entscheiden Kosten, Last und Gedächtnis.
5. **Je breiter die Fenster, desto mehr Verlängerungen sind zulässig.** Ob und wie stark dadurch mehr Labels entstehen, messen die Experimente.
"""

ASSUMPTIONS_MARKDOWN = """
**Annahmen**
- Warten bis zum Fensterbeginn ist erlaubt und kostet nichts. Genau deshalb darf ein Label, das früher ankommt, ein späteres mit höchstens gleichen Kosten dominieren.
- Kosten und Fahrzeit sind die Entfernung (Quadrat 100 × 100, euklidisch; im Handbeispiel Manhattan-Abstand auf einem Gitter). Bedienzeit 10 (Handbeispiel 2), Horizont 300 (Handbeispiel 36), Kapazität 70 (Handbeispiel 99, wirkt dort nicht).
- Das Fenster der Breite w liegt um einen zufälligen Mittelpunkt, beschnitten auf die zulässige Zeitspanne zwischen Entfernung zum Depot und Horizont minus Bedienzeit minus Entfernung.
- Die Dualpreise sind die der ersten Runde (je Kunde das Doppelte der Entfernung zum Depot); der Größenregler rechnet einen Pricing-Aufruf, nicht die ganze Spaltenerzeugung.

**Grenzen**
- Die Instanzen sind selbst erzeugt und Solomon-artig, nicht die Originalinstanzen. Die Messreihen haben 30 Kunden: 12 Instanzen je Zelle bei einem Pricing-Aufruf, 6 Instanzen je Zelle bei der ganzen Spaltenerzeugung.
- Nicht gemessen sind Wartekosten größer null, Fenster um die Ankunftszeiten eines Bezugsplans (so legt die Tourenbildung sie), die Rechenzeit statt der Label-Zahl und mehr als 30 Kunden mit der Fensterbreite als Variable.
- Der Größenregler rechnet live bis Breite 150; Breite 200 gibt es nur als feste Messreihe.
- Elementare Rechnung (jeder Kunde höchstens einmal) wurde in der ganzen Spaltenerzeugung bei Breite 100 in 3 von 6 und bei Breite 200 in 6 von 6 Läufen abgebrochen; diese Zellen zeigen nur die fertigen Läufe.

**Bekannte Probleme und Unsicherheiten**
- Die Label-Zahl wächst nicht allgemein mit der Breite: Ein zusätzliches Label kann andere dominieren. Sie wird gezählt und nicht vorausgesagt; die Zeile „wächst“ gilt für die gemessenen Reihen.
- Einzelne Instanzen weichen vom Median ab; Median, Mittel und Maximum stehen deshalb nebeneinander. Gründe für das Wachstum, etwa dass mehr Wege in die Fenster passen, sind Deutungen und nicht gemessen.
- Sekunden stehen nur zur Information, sie hängen vom Rechner ab; getestet werden Zählungen.
- Der Zeitstrahl und die Karten sind im Browser geprüft, nicht mit Mausklicks automatisiert.
"""

MATH_MARKDOWN = r"""
**Lesehilfe.** *Gegeben:* ein Depot 0, Kunden $1, \dots, n$, Entfernungen, Zeitfenster, Lasten und Dualpreise. *Gesucht:* eine Route Depot → Kunden → Depot mit möglichst kleinen
reduzierten Kosten, die alle Fenster, die Kapazität und den Horizont einhält. Das Label-Setting erzeugt dazu Teilwege (Labels) und streicht überflüssige.

| Symbol | Bedeutung |
|---|---|
| $d_{ij}$ | Entfernung von $i$ nach $j$; zugleich die Fahrzeit |
| $s$ | Bedienzeit je Kunde |
| $[e_j, l_j]$ | Zeitfenster von Kunde $j$: frühester Beginn der Bedienung, späteste Ankunft |
| $q_j$, $Q$ | Last von Kunde $j$, Kapazität |
| $H$ | Horizont: späteste Rückkehr zum Depot |
| $\pi_j$ | Dualpreis von Kunde $j$ ($\pi_0 = 0$) |
| $(t, c, q, M, i)$ | Label: Zeit nach dem Warten, Kosten, Last, Gedächtnis (gesperrte Kunden), aktueller Knoten |
| $NG(j)$ | Gedächtnis-Nachbarschaft: die $k$ nächsten Kunden von $j$ einschließlich $j$ |

**Verlängerung** eines Labels $(t, c, q, M, i)$ zu Kunde $j$: Ankunft

$$a = t + s\,[i \neq 0] + d_{ij}$$

zulässig, wenn

$$a \le l_j, \qquad q + q_j \le Q, \qquad j \notin M .$$

Das neue Label entsteht mit Warten bis zum Fensterbeginn:

$$t' = \max(a, e_j), \qquad c' = c + d_{ij} - \pi_j, \qquad q' = q + q_j, \qquad M' = (M \cap NG(j)) \cup \{j\} .$$

**Dominanz** (zwei Labels am selben Knoten): $L_1$ dominiert $L_2$, wenn

$$c_1 \le c_2, \qquad t_1 \le t_2, \qquad q_1 \le q_2, \qquad M_1 \subseteq M_2 .$$

Jede Verlängerung von $L_2$ ist dann auch für $L_1$ zulässig und höchstens so teuer: $L_1$ kommt nicht später an, ein früheres Eintreffen wird durch Warten ausgeglichen,
und die Kosten hängen nicht von der Zeit ab. Das gilt nur, weil Warten nichts kostet.

**Rückkehr:** ein Label am Kunden $i$ schließt die Route ab, wenn

$$t + s + d_{i0} \le H, \qquad \text{reduzierte Kosten der Route} = c + d_{i0} .$$

**Literatur und Prüfstand.**
- Desrochers, Soumis (1988): verallgemeinertes Permanent-Labeling für kürzeste Wege mit Zeitfenstern, INFOR 26(3). Nur die bibliografische Angabe ist geprüft (Seitenzahlen in den Quellen uneinheitlich), das Abstract nicht erhalten.
- Irnich, Desaulniers (2005): Kapitel „Shortest Path Problems with Resource Constraints“ in *Column Generation*, Springer. Als Standardreferenz für Erweiterungsfunktionen mit Maximum bei Zeitfenstern in Sekundärquellen zitiert; der Inhalt ist hier nicht geprüft (Volltext nicht erhalten).
- Pessoa, Sadykov, Uchoa, Vanderbeck (2020): *A generic exact solver for vehicle routing and related problems*, Mathematical Programming 183. Nach der früheren Lektüre von Einleitung und Anfang der Abschnitte 2 und 3 schreiben sie, reines Branch-and-Price sei früher nur bei eng beschränkten Touren gut gelaufen; das deckt sich in der Richtung mit dem Befund hier, die Zahlen dieser Demo sind eigene und keine aus der Literatur.
"""
