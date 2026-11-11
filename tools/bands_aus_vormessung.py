"""Erzeugt die festen Messreihen in data/ aus den Rohausgaben der Vormessung (nur Standardbibliothek, ändert nichts an der Vormessung).

Aufruf (im Demo-Ordner):  python tools/bands_aus_vormessung.py <Ordner der Vormessung>

Liest
  run_p03.log        ein Pricing-Aufruf, n = 30, ng-Gedächtnis k = 5, 12 Instanzen je Zelle, Breiten 20 bis 200, zufällige und gruppierte Kunden
  out_v1_n30.txt     ganze Spaltenerzeugung, n = 30, Breiten 40 / 100 / 200, 6 Instanzen je Zelle, ng-Gedächtnis k = 1, 3, 5, 8, 12 und elementar (k = 30)
und schreibt data/band_p03.json und data/band_v1.json. Jede Zeile trägt ihre Quelle (Datei und Zeilennummer). Es wird nichts gerundet oder umgerechnet:
die Zahlen stehen so da, wie die Rohausgabe sie nennt.
"""

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def parse_p03(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows, typ = [], None
    for number, line in enumerate(lines, start=1):
        m = re.match(r"Typ (\S+)", line)
        if m:
            typ = m.group(1)
            continue
        parts = line.split()
        if typ and len(parts) == 8 and re.fullmatch(r"\d+", parts[0]):
            w, med, mean, mx, dom, wait, wavg, fo = parts
            rows.append({
                "typ": typ, "breite": int(w), "median": int(med), "mittel": float(mean), "max": int(mx),
                "dominiert_mittel_prozent": float(dom), "wartet_mittel_prozent": float(wait),
                "wartezeit_je_wartendem_label_mittel": float(wavg), "fenster_aus_je_label_mittel": float(fo),
                "quelle": f"{path.name}, Zeile {number}",
            })
    return {
        "quelle": f"vormessung/{path.name} (erzeugt von v_p03_breite_warten.py)",
        "bedingungen": {
            "kunden": 30, "ng_gedaechtnis_k": 5, "kapazitaet": 70, "horizont": 300, "bedienzeit": 10,
            "instanzen_je_zelle": 12, "zufalls_seeds": "0 bis 11", "dualpreise": "erste Runde: 2 mal Entfernung zum Depot",
            "messgroesse": "erzeugte Labels in einem Pricing-Aufruf",
        },
        "zeilen": rows,
    }


def parse_v1(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for number, line in enumerate(lines, start=1):
        parts = line.split()
        if len(parts) == 11 and parts[0].isdigit():
            n, w, seed, k, bound, it, cols, t, lab, dom, ab = parts
            rows.append({
                "kunden": int(n), "breite": int(w), "seed": int(seed), "k": int(k), "schranke": None if bound == "NA" else float(bound),
                "iterationen": int(it), "spalten": int(cols), "pricing_sekunden": float(t), "labels": int(lab), "dominiert_anteil": float(dom),
                "abgebrochen": int(ab), "quelle": f"{path.name}, Zeile {number}",
            })
    return {
        "quelle": f"vormessung/{path.name} (erzeugt von v1_messreihe.py)",
        "bedingungen": {
            "kunden": 30, "kapazitaet": 70, "horizont": 300, "bedienzeit": 10, "instanzen_je_zelle": 6, "zufalls_seeds": "0 bis 5",
            "messgroesse": "Summe der erzeugten Labels über alle Pricing-Aufrufe der Spaltenerzeugung bis zur Konvergenz",
            "k_30": "elementar (jeder Kunde höchstens einmal); abgebrochen = Rechnung nach der Zeitgrenze der Vormessung beendet",
            "sekunden": "nur zur Information, Rechner der Vormessung",
        },
        "zeilen": rows,
    }


def main(folder: str) -> None:
    src = Path(folder)
    DATA.mkdir(exist_ok=True)
    for name, data in (("band_p03.json", parse_p03(src / "run_p03.log")), ("band_v1.json", parse_v1(src / "out_v1_n30.txt"))):
        (DATA / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(name, len(data["zeilen"]), "Zeilen")


if __name__ == "__main__":
    main(sys.argv[1])
