# Zeitfenster und Warten im Label-Setting – Streamlit-Demo

<!-- Live-Link nach dem Deploy direkt hierher setzen (Leerzeile davor und danach): **[→ Demo live ausprobieren](https://sebastianhanisch-zeitfenster-labeling-demo.streamlit.app/)** -->

Baustein der Linie **„Ressourcenwege und Spaltenerzeugung“** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Vorausgesetzt werden der Ressourcenweg mit einer Zeitgrenze ([weg-mit-grenzen-demo](https://github.com/sebastian-hanisch/weg-mit-grenzen-demo)) und die Dominanz von Labels
([dominanz-labels-demo](https://github.com/sebastian-hanisch/dominanz-labels-demo)). Hier bekommt jeder Kunde ein **Zeitfenster** [e, l], und die Demo fragt, was das mit den Labels macht.

In der Spaltenerzeugung für Tourenprobleme sucht das **Pricing** eine Route mit möglichst kleinen **reduzierten Kosten**: Fahrstrecke minus die **Dualpreise**, die das übergeordnete
Planungsproblem (der Master) für das Bedienen jedes Kunden bietet. Das Verfahren dafür heißt **Label-Setting**: Es verlängert **Labels** (Teilwege mit Zeit, Kosten, Last und einem Gedächtnis
der besuchten Kunden) in der Reihenfolge ihrer Zeit und streicht überflüssige Labels durch **Dominanz**. Eine Anwendung mit Ressourcen für Dienstspanne, Lenkzeit und Ruhezeit (aber ohne
Kundenfenster) ist [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo).

## Kernfrage

Was ändert ein Zeitfenster [e, l] an jedem Kunden, und **wie stark steuert seine Breite die Zahl der erzeugten Labels?**

Ein Zeitfenster macht aus der Zeitgrenze eine Zeit, die bei jedem Kunden zwischen Fensterbeginn und Fensterende liegen muss: Wer zu früh kommt, wartet (ohne Kosten) bis zum Fensterbeginn,
wer zu spät kommt, scheidet aus. **Je breiter die Fenster, desto mehr Labels (in den gemessenen Reihen):** In diesen Reihen wächst die Zahl mit jeder Stufe. In einem Pricing-Aufruf (30 Kunden, ng-Gedächtnis 5, Dualpreise der ersten Runde, 12 Instanzen je Zelle) wächst der
Median der erzeugten Labels von Breite 20 auf Breite 200 bei zufällig verteilten Kunden von 1.413 auf 42.510 (Faktor 30,1) und bei gruppierten Kunden von 2.870 auf 68.216 (Faktor 23,8), also um das
24- bis 30-Fache. In der ganzen Spaltenerzeugung (30 zufällige Kunden, 6 Instanzen je Zelle) wächst der Median der Labels von Breite 40 auf Breite 200 bei k = 1 um das 9,5-Fache (16.938 auf 160.456)
und bei k = 5 um das 16,7-Fache (20.904 auf 348.904).

Alle Zahlen gelten für **eigene Solomon-artige Instanzen** (Quadrat 100 × 100, Zeit = Entfernung, Bedienzeit 10, Horizont 300, Kapazität 70; Fenster der Breite w um einen zufälligen Mittelpunkt,
auf die zulässige Zeitspanne beschnitten), nicht für die Originalinstanzen. Gezählt werden **erzeugte Labels**, nicht Sekunden.

## Modell

- **Label:** Zeit t (nach dem Warten), Kosten c, Last q, Gedächtnis M (gesperrte Kunden), Knoten i.
- **Verlängerung** zu Kunde j: Ankunft a = t + Bedienzeit (nicht beim Depot) + Entfernung. Ist a größer als das Fensterende l_j, scheidet die Verlängerung aus („Fenster-Aus“). Ist a kleiner als der
  Fensterbeginn e_j, **wartet** das Label bis e_j; die Kosten ändern sich dabei nicht.
- **Dominanz:** Ein Label dominiert ein anderes am selben Knoten, wenn es höchstens so teuer, höchstens so spät und höchstens so beladen ist und höchstens dieselben Kunden sperrt. Weil Warten nichts
  kostet, genügt „höchstens so spät“; warten zwei Labels bis zum Fensterbeginn, haben beide danach dieselbe Zeit.
- **ng-Gedächtnis k:** k = 1 verbietet nur die sofortige Wiederholung (Kunden dürfen wiederkehren, nichtelementar); im Handbeispiel gilt k = Zahl der Kunden (elementar).
- Formeln, Symboltabelle und Literatur stehen im Ausklapper „📐 Mathematische Formulierung“ der App.

## Methodik: fünf Experimente

1. **Zeitfenster Schritt für Schritt (Handbeispiel):** Depot und 6 Kunden auf einem Gitter, Fensterbreite w = 2, 6, 12, 24 oder 60. Protokoll jedes erzeugten Labels mit Ankunft, Fenster, Wartezeit und
   Entscheidung der Dominanz („dominiert von L1, nach dem Warten gleiche Zeit“), verworfene Verlängerungen („Ankunft 32 > Fensterende 17“) und ein Zeitstrahl je Label (Fahrt, Warten schraffiert, Bedienung, Fenster).
   Das Ergebnis wird gegen die Aufzählung aller zulässigen Routen geprüft.
2. **Breite gegen Nutzen (Handbeispiel):** bester Wert, Labels und zulässige Routen bei allen fünf Breiten nebeneinander.
3. **Größenregler:** ein Pricing-Aufruf auf einer Solomon-artigen Instanz (10 bis 30 Kunden, Breite 20 bis 150, zufällig oder gruppiert, k = 1 oder 5) mit Karte, Fensterplan, Anteil dominierter und wartender Labels.
   Die Rechnung läuft live und ist auf 600.000 erzeugte Labels begrenzt (die App meldet einen Abbruch).
4. **Feste Messreihen:** die Tabellen unten (ein Pricing-Aufruf; ganze Spaltenerzeugung), jede Zeile mit Quelle in `data/`.
5. **Warten:** Anteil wartender Labels, Wartezeit und Fenster-Aus gegen die Breite; im Handbeispiel die Dominanzen bei gleicher Zeit nach dem Warten.

## Befunde (gemessen, keine Behauptungen)

Alle Zeilen unten stehen so in `data/` (Quelle: Rohausgaben der Vormessung); wie jede Zahl geprüft ist, zeigt die Tabelle „Zahl → Test“ weiter unten.

**Ein Pricing-Aufruf, zufällig verteilte Kunden** (30 Kunden, ng-Gedächtnis 5, Dualpreise der ersten Runde, 12 Instanzen je Zelle mit den Zufalls-Seeds 0 bis 11; Labels = erzeugte Labels; Mittel über die 12 Instanzen):

| Breite | Median | Mittel | Maximum | dominiert (%) | wartet (%) | Wartezeit je wartendem Label | Fenster-Aus je Label |
|---|---|---|---|---|---|---|---|
| 20 | 1.413 | 1.384,3 | 1.831 | 71,4 | 71,4 | 41,2 | 5,60 |
| 40 | 2.638 | 2.610,8 | 3.589 | 76,5 | 51,7 | 38,6 | 4,02 |
| 70 | 5.425 | 5.658,8 | 7.585 | 80,5 | 32,0 | 34,1 | 2,83 |
| 100 | 10.911 | 10.555,6 | 13.654 | 83,1 | 19,2 | 30,4 | 2,14 |
| 150 | 22.870 | 23.600,9 | 32.602 | 86,4 | 7,5 | 25,5 | 1,37 |
| 200 | 42.510 | 40.760,4 | 58.879 | 88,5 | 2,8 | 21,5 | 0,91 |

**Ein Pricing-Aufruf, gruppierte Kunden** (fünf Gruppen, sonst dieselben Voraussetzungen):

| Breite | Median | Mittel | Maximum | dominiert (%) | wartet (%) | Wartezeit je wartendem Label | Fenster-Aus je Label |
|---|---|---|---|---|---|---|---|
| 20 | 2.870 | 3.123,0 | 5.359 | 81,1 | 75,6 | 53,1 | 2,87 |
| 40 | 5.274 | 6.141,3 | 13.559 | 84,1 | 61,9 | 51,1 | 2,05 |
| 70 | 11.377 | 13.592,6 | 33.327 | 86,1 | 45,1 | 46,9 | 1,36 |
| 100 | 20.414 | 23.505,8 | 61.378 | 87,3 | 32,7 | 42,5 | 1,00 |
| 150 | 42.178 | 43.328,6 | 92.845 | 89,0 | 18,2 | 35,0 | 0,62 |
| 200 | 68.216 | 68.357,8 | 121.135 | 90,2 | 9,2 | 28,1 | 0,38 |

Die Mediane beider Tabellen sind auf ganze Zahlen gerundet; wo der Median das Mittel zweier Werte ist, weicht die Zahl um 0,5 ab (z. B. 2.870 statt 2.869,5 und 5.274 statt 5.274,5 bei gruppierten, 22.870 statt 22.869,5 bei zufällig verteilten Kunden).

- **In den gemessenen Reihen wächst die Label-Zahl mit der Breite:** Der Median steigt in allen 10 Stufen (5 je Typ) um den Faktor 1,6 bis 2,2 (kleinster Faktor 1,62, größter 2,16), jeweils von Breite zu Breite der Tabellen. Bei jeder der sechs Breiten
  liegt der Median der gruppierten Kunden über dem der zufällig verteilten.
- **Der Anteil dominierter Labels steigt** in beiden Tabellen von Breite zu Breite (zufällig von 71,4 auf 88,5 %, gruppiert von 81,1 auf 90,2 %).
- **Schmale Fenster erzeugen weniger Labels, aber ein großer Teil davon wartet, und viele Verlängerungen scheitern am Fensterende:** Bei Breite 20 warten 71,4 % (zufällig) bzw. 75,6 % (gruppiert) der Labels, und je erzeugtem Label
  scheitern im Mittel 5,60 bzw. 2,87 Verlängerungen am Fensterende (bei Breite 200: 0,91 bzw. 0,38). Der Anteil wartender Labels, die mittlere Wartezeit je wartendem Label und die Fenster-Aus je Label sinken in beiden Tabellen
  von Breite zu Breite. Weniger als 10 % der Labels warten bei zufällig verteilten Kunden ab Breite 150 (7,5 %), bei gruppierten ab Breite 200 (9,2 %).
- **Einzelne Instanzen weichen stark ab:** bei gruppierten Kunden und Breite 100 liegt das Maximum (61.378) beim 3,0-Fachen des Medians (20.414).

**Ganze Spaltenerzeugung** (30 zufällige Kunden, 6 Instanzen je Zelle mit den Zufalls-Seeds 0 bis 5, Summe aller Pricing-Aufrufe bis zur Konvergenz, Überdeckungs-Master; k = ng-Gedächtnis; Median und Mittel nur über die fertigen Läufe):

| Breite | k | Läufe | abgebrochen | Median der Labels (fertige Läufe) | dominiert, Mittel (%) |
|---|---|---|---|---|---|
| 40 | 1 | 6 | 0 | 16.938 | 82,3 |
| 40 | 3 | 6 | 0 | 20.525 | 80,0 |
| 40 | 5 | 6 | 0 | 20.904 | 78,2 |
| 40 | 8 | 6 | 0 | 24.998 | 74,7 |
| 40 | 12 | 6 | 0 | 25.650 | 71,1 |
| 40 | elementar | 6 | 0 | 40.175 | 49,5 |
| 100 | 1 | 6 | 0 | 57.330 | 87,2 |
| 100 | 3 | 6 | 0 | 71.951 | 86,0 |
| 100 | 5 | 6 | 0 | 92.038 | 84,4 |
| 100 | 8 | 6 | 0 | 108.188 | 82,0 |
| 100 | 12 | 6 | 0 | 127.900 | 79,1 |
| 100 | elementar | 6 | 3 | 140.285 | 54,0 |
| 200 | 1 | 6 | 0 | 160.456 | 91,4 |
| 200 | 3 | 6 | 0 | 282.955 | 90,4 |
| 200 | 5 | 6 | 0 | 348.904 | 89,5 |
| 200 | 8 | 6 | 0 | 424.689 | 87,8 |
| 200 | 12 | 6 | 0 | 548.908 | 85,5 |
| 200 | elementar | 6 | 6 | – | – |

Die elementare Rechnung wurde bei Breite 100 in 3 von 6 und bei Breite 200 in 6 von 6 Läufen abgebrochen (Zeitgrenze der Vormessung); diese Zellen zeigen nur die fertigen Läufe. Die Zeile „Breite 100, elementar“ (Median 140.285, dominiert 54,0 %) beruht daher nur auf den 3 fertigen, schnelleren Läufen und ist keine Messung der ganzen Zelle. Bei gerader Zahl fertiger Läufe ist der Median das Mittel der beiden mittleren Werte, auf ganze Zahlen gerundet.

**Handbeispiel** (Depot (5, 5) und 6 Kunden, Manhattan-Abstand, Bedienzeit 2, Horizont 36, jeder Kunde höchstens einmal; „wartend“ zählt erzeugte Labels, die vor dem Fensterbeginn ankamen; „Fenster-Aus“ die
am Fensterende verworfenen Verlängerungen; die Zahl der zulässigen Routen liefert eine Aufzählung ohne Label-Setting):

| Breite w | zulässige Routen | bester Wert | Route | Labels | dominiert | wartend | Wartezeit insgesamt | Fenster-Aus | Dominanzen bei gleicher Zeit |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 16 | −12 | 4-5 | 15 | 4 | 9 | 118 | 38 | 3 |
| 6 | 38 | −18 | 4-1-5 | 27 | 6 | 9 | 106 | 62 | 3 |
| 12 | 119 | −21 | 4-1-3-5 | 67 | 13 | 9 | 88 | 124 | 6 |
| 24 | 292 | −26 | 3-1-4-6-5 | 159 | 51 | 5 | 48 | 167 | 14 |
| 60 | 686 | −28 | 1-5-3-6-4 | 272 | 164 | 0 | 0 | 43 | 37 |

- Das Label-Setting trifft den besten Wert der Aufzählung bei allen fünf Breiten. Mit breiteren Fenstern wird der beste Wert in diesem Beispiel nie schlechter (−12 ≥ −18 ≥ −21 ≥ −26 ≥ −28), und die Label-Zahl wächst
  hier mit (15, 27, 67, 159, 272). Das gilt für dieses Beispiel; die Label-Zahl wächst nicht allgemein monoton mit der Breite.
- Bei Breite 6 fallen 3 von 6 Dominanzen mit gleicher Zeit nach dem Warten zusammen (L7 gegen L1, L9 gegen L4, L10 gegen L5), in allen drei Fällen, weil beide Labels bis zum Fensterbeginn desselben Kunden warten.
  Das erste Label L1 (Weg 1) kommt bei 2 an, das Fenster beginnt bei 24, es wartet 22; die Verlängerung von L3 zu Kunde 2 scheitert (Ankunft 32 > Fensterende 17).

## Zahl → Test

| Zahl in dieser README | Test (Datei `tests/test_claims.py`, wenn nicht anders genannt) | Art |
|---|---|---|
| Tabellen „Ein Pricing-Aufruf“ (beide Typen, alle Spalten) | `test_readme_has_the_band_table_verbatim`: die Tabelle wird aus `data/band_p03.json` erzeugt und wortgleich gesucht | Messreihe |
| dieselben Zeilen bei Breite 20, 40, 70, 100 (beide Typen) und zufällig 150 | `test_band_row_is_reproduced_at_the_fixed_seeds`: neu gerechnet an den Zufalls-Seeds 0 bis 11, jede Spalte | exakt |
| größte Instanz gruppiert, Breite 150: 92.845 Labels | `test_the_largest_instance_of_the_band_at_width_150_clustered` und `test_worst_case_at_the_slider_maximum_finishes` (`tests/test_algorithm.py`) | exakt |
| gruppiert bei Breite 150 und 200, zufällig bei Breite 200 | nur in `data/band_p03.json` (Messung der Vormessung, im Test nicht neu gerechnet; die Rohausgabe wird lokal verglichen: `test_band_files_equal_the_raw_output_of_the_pre_measurement_if_it_is_there`) | Messreihe |
| Faktoren 30,1 / 23,8 / 24- bis 30-Fache / 1,6 bis 2,2 / 1,62 / 2,16 | `test_growth_numbers_of_the_readme` | Messreihe |
| „steigt“ und „fällt“ von Breite zu Breite (Median, dominiert, wartet, Wartezeit, Fenster-Aus) | `test_every_trend_sentence_of_the_readme_holds_in_all_five_steps` (je Typ alle 5 Stufen) | Messreihe |
| gruppiert über zufällig bei jeder Breite; 61.378 gegen 20.414 (3,0-fach) | `test_clustered_median_is_larger_than_random_at_every_width_and_maximum_to_median` | Messreihe |
| Warten unter 10 % ab Breite 150 (7,5 %) bzw. 200 (9,2 %) | `test_waiting_becomes_rare_from_these_widths_on` | Messreihe |
| Tabelle „Ganze Spaltenerzeugung“, 9,5-Fache und 16,7-Fache, 3 von 6 und 6 von 6 abgebrochen | `test_readme_has_the_v1_table_verbatim`, `test_v1_numbers_of_the_readme_equal_the_aggregate_of_the_raw_rows` (Median je Zelle gegen die Zusammenfassung der Vormessung) | Messreihe |
| Stichprobe der Spaltenerzeugung (6 Zeilen) | `test_v1_sample_is_reproduced_as_a_band`: Schranke auf 4 Stellen, Iterationen, Spalten und Labels im Band ±25 % | Band |
| Handbeispiel: Tabelle, 15 / 27 / 67 / 159 / 272, −12 bis −28, 16 bis 686 Routen | `test_readme_has_the_hand_table_verbatim`, `test_hand_example_numbers_of_the_readme`, `tests/test_algorithm.py::test_hand_values_per_width` (Handwerte aus dem unabhängigen Handrechen-Skript) | exakt |
| 3 von 6 Dominanzen bei gleicher Zeit, L1 wartet 22, Ankunft 32 > 17 | `test_three_of_six_dominations_at_width_6_have_the_same_time_because_both_labels_wait`, `test_first_label_waits_22_and_the_extension_to_customer_2_fails`, `tests/test_algorithm.py` (Rechnung von Hand) | exakt |
| Annahmen, Grenzen und bekannte Probleme (App und README gleich) | `test_readme_has_the_assumptions_text_of_the_app_verbatim` | Text |
| Hilfetexte des Schnellstarts | `tests/test_presets.py` (je Aussage ein Test) und `tests/test_app.py::test_every_preset_runs_and_shows_the_expected_verdict_line` | exakt |
| „600.000 Labels“ als Grenze | `tests/test_verdicts.py` (Text des Abbruchs), `tests/test_algorithm.py::test_max_labels_aborts_and_says_so` | exakt |
| Laufzeit „rund 1 Sekunde, höchstens 2,3 Sekunden“ (Abschnitt „Bewusst nicht umgesetzt“) | Messung dieser README, nicht im Test | Messung |
| 700 Zufallsinstanzen ohne Abweichung (Abschnitt „Tests“) | Messung dieser README (einmaliger Lauf, nicht im Repo); im Repo läuft die kleine Fassung | Messung |

## Annahmen, Grenzen und bekannte Probleme

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

## Abgrenzung

- **[hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo)** (Kürzeste-Wege-Linie) ist etwas anderes: Dort bekommt jeder Knoten eine Liste von Hubs, damit Abfragen ohne Suche im Graphen gehen. Hier sind Labels
  Teilwege einer Suche, die Ressourcen mitführt.
- **Zeitfenster in der Tourenbildung:** [zeitfenster-split-demo](https://github.com/sebastian-hanisch/zeitfenster-split-demo) legt Fenster um die Ankunftszeiten eines Bezugsplans; hier liegen sie um zufällige Mittelpunkte,
  und die Label-Zahl ist die Messgröße. Zahlen aus der anderen Demo werden hier nicht verwendet.
- **[crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo)** zeigt das Pricing mit Regeln (Dienstspanne, Lenkzeit, Ruhezeit) in einer Anwendung, nicht Kundenfenster.

## Tests

171 Tests (`pytest --collect-only -q tests`); die Suite lief lokal in rund 22 Sekunden (Messung dieser README, nicht im Test; `-n 4`, Rechner durch andere Arbeiten ausgelastet). Zusammensetzung:

- **Kern** (`tests/test_algorithm.py`): Handbeispiel von Hand gerechnet (Ankunft, Wartezeit, Kosten, Dominanz bei gleicher Zeit, gescheiterte Verlängerung), alle Zählungen bei den fünf Breiten, jede Regel einzeln, jede
  Regel mit Wirkung abgeschaltet (Fensterende, Warten, Dominanz, Gedächtnis, Kapazität verändern das Ergebnis), Abbruch bei zu vielen Labels, Hängertest am Regler-Maximum (30 Kunden, Breite 150).
- **Orakel** (`tests/test_oracle_zeitfenster_labeling.py`): Aufzählung aller Routen mit einer Fahrplan-Uhr, die weder das Label-Setting noch dessen Regelfunktionen benutzt: Handbeispiel, 90 Zufallsinstanzen (elementar,
  Manhattan und euklidisch, mit Punktfenstern), 100 Instanzen für nichtelementar (k = 1) und ng-Gedächtnis (k = 2, 3) und 30 kleine Solomon-artige Instanzen. Ein einmaliger Lauf außerhalb des Repos mit 700 Zufallsinstanzen
  (400 elementar, 300 nichtelementar oder ng) fand keine Abweichung (Messung dieser README, nicht im Test).
- **Eigenschaften** (`tests/test_eigenschaften_zeitfenster_labeling.py`): breitere, ineinandergelegte Fenster machen den besten Wert nie schlechter; Fenster [0, H] geben das Ergebnis der reinen Zeitgrenze; Warten ändert die Kosten eines
  Labels nicht; jedes Label liegt im Fenster seines Knotens; dieselben Zählungen in zwei Prozessen mit verschiedenem Hash-Seed. Ausdrücklich keine Eigenschaft „die Label-Zahl wächst nie“: Sie gilt nicht allgemein.
- **Randfälle** (`tests/test_edge_cases.py`): Punktfenster, Ankunft genau am Fensterende und genau am Fensterbeginn, unerreichbarer Kunde, Rückkehr genau bei H, Fenster nach H, n = 1, n = 2, Gleichstand.
- **Verdikte** (`tests/test_verdicts.py`): jede Schwelle und jede Zahl im Text an handgesetzten Werten (Warten selten unter 10 %, Wachstum ab Faktor 1,5, Abbruch, keine verbessernde Route).
- **Oberfläche** (`tests/test_app.py`, `tests/test_layout.py`, `tests/test_presets.py`, `tests/test_footer.py`): Standard, jedes Schnellstart-Szenario mit der erwarteten Verdikt-Zeile, jeder Regler am Minimum und Maximum, alle Minima und alle
  Maxima zusammen, Permalink (Begrenzen und Einrasten), jede Auswahl des Zeitstrahls, Hervorhebung des aktiven Szenarios.
- **Laufzeit-Importe** (`tests/test_runtime_imports.py`) und **Zahlen** (`tests/test_claims.py`).

## Ehrliche Grenzen

Die Grenzen stehen im Abschnitt „Annahmen, Grenzen und bekannte Probleme“ oben, wortgleich mit dem Ausklapper der App. Zusätzlich: Der Größenregler endet bei Breite 150; Breite 200 gibt es nur als feste Messreihe (siehe „Bewusst nicht umgesetzt“).

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App: Kernfrage, fünf Experimente, Grenzen, Formeln |
| `zfl_algorithm.py` | Kern: Label-Setting mit Zeitfenstern, je Regel eine Funktion; Fahrplan-Prüfer und Aufzählung |
| `zfl_scenario.py` | Instanzen: Solomon-artige Zufallsinstanz und Handbeispiel |
| `zfl_evaluation.py` | Kennzahlen, feste Messreihen laden, Verdikte (reine Funktionen), Tabellen für die README |
| `zfl_constants.py` | Regler-Grenzen, feste Annahmen, Schnellstart-Szenarien und ihre Hilfetexte |
| `zfl_presets.py` | Permalink (Begrenzen, Einrasten), Schnellstart in der Seitenleiste, Zufalls-Seed-Button |
| `zfl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `zfl_layout.py` | Fester Kopf (Stylesheet) |
| `zfl_texts.py` | Einleitung, Erklärtext, Annahmen und Formeln der App |
| `data/band_p03.json`, `data/band_v1.json` | Feste Messreihen, jede Zeile mit Quelle |
| `tools/bands_aus_vormessung.py` | Erzeugt die beiden Dateien aus den Rohausgaben der Vormessung |
| `tests/` | Kern, Orakel, Eigenschaften, Randfälle, Verdikte, Zahlen, Oberfläche, Layout, Schnellstart, Footer, Laufzeit-Importe |
| `.github/workflows/tests.yml`, `.gitignore`, `.streamlit/config.toml`, `requirements*.txt` | CI, Ausnahmen, Streamlit-Einstellungen, Bibliotheken |

## Bewusst nicht umgesetzt

- **Wartekosten größer null** und Fenster um Ankunftszeiten eines Bezugsplans: nicht gemessen, daher nicht gebaut (Schalter ohne Messung wären Behauptungen).
- **Der Größenregler über Breite 150 hinaus:** Eine einmalige Messung auf dem Entwicklungsrechner (30 gruppierte Kunden, Breite 200, ng-Gedächtnis 5, 12 Instanzen) ergab im Mittel rund 1 Sekunde und höchstens 2,3 Sekunden je Pricing-Aufruf
  (Messung dieser README, nicht im Test); ob die Grenze angehoben wird, ist offen.
- **Dualpreise späterer Runden, Zeit statt Labels, mehr als 30 Kunden mit der Fensterbreite als Variable:** nicht gemessen.
- **PDF-Export:** keiner; die Demo zeigt Zählungen und Tabellen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Getestet wurde lokal mit Python 3.14; die CI läuft mit Python 3.12. Die in Streamlit Cloud eingestellte Python-Version ist beim Deploy hier einzutragen.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit und Plotly; die Tests nutzen zusätzlich NumPy und SciPy für die Stichprobe der Spaltenerzeugung.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
