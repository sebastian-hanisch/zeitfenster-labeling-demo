"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Komplexität am Regler-Maximum (n = 30, Breite 150, ng-Gedächtnis k = 5): Die Zahl der Labels wächst mit der Breite etwa auf das Doppelte je
Stufe (Messreihe in `data/band_p03.json`); gemessen wurden bei Breite 150 im Median 22 870 Labels (zufällige Kunden) und 42 178 (gruppiert),
höchstens 92 845 in den 12 Instanzen der Messreihe. Eine Instanz mit anderem Zufalls-Seed kann mehr brauchen: `LABEL_LIMIT` bricht deshalb jede
Rechnung ab, die mehr Labels erzeugt, und die App sagt es.
"""

# --- Instanzen (Solomon-artig, selbst erzeugt) ---------------------------------------------------------------------------------------------
DEPOT = (50.0, 50.0)
HORIZON = 300.0          # spätester Zeitpunkt der Rückkehr zum Depot
CAPACITY = 70            # Kapazität
SERVICE = 10.0           # Bedienzeit je Kunde
DEMAND_LOW, DEMAND_HIGH = 5, 25
N_GROUPS = 5             # Gruppen bei gruppierten Kunden
GROUP_SPREAD = 6.0       # Streuung der Kunden um ihre Gruppenmitte
TYPES = ("zufällig", "gruppiert")

# --- Regler ---------------------------------------------------------------------------------------------------------------------------------
N_MIN, N_MAX, DEFAULT_N = 10, 30, 30
WIDTH_MIN, WIDTH_MAX, DEFAULT_WIDTH, WIDTH_STEP = 20, 150, 40, 10      # live bis 150; Breite 200 nur als feste Messreihe (noch nicht auf Rechenzeit gemessen)
K_CHOICES, DEFAULT_K = (1, 5), 5
HAND_WIDTHS, DEFAULT_HAND_WIDTH = (2, 6, 12, 24, 60), 6
SEED_MAX, DEFAULT_SEED = 999999, 0
DEFAULT_TYPE = "zufällig"
LABEL_LIMIT = 600_000    # Schutz gegen Hänger: so viele Labels darf eine Rechnung in der App höchstens erzeugen

# --- Messreihen (fest, Quelle: Messdateien der Vormessung, siehe data/) --------------------------------------------------------------------
BAND_N = 30
BAND_K = 5
BAND_SEEDS = tuple(range(12))
BAND_WIDTHS = (20, 40, 70, 100, 150, 200)
V1_WIDTHS = (40, 100, 200)
V1_KS = (1, 3, 5, 8, 12, 30)
V1_SEEDS = tuple(range(6))
WAIT_RARE_PERCENT = 10.0       # Verdikt: Warten gilt als selten, wenn weniger als dieser Anteil der Labels wartet
GROWTH_FACTOR = 1.5            # Verdikt: die Label-Zahl wächst, wenn der Median von Stufe zu Stufe mindestens um diesen Faktor steigt

# --- Handbeispiel (Depot + 6 Kunden, Manhattan-Abstand, ganze Zahlen) ----------------------------------------------------------------------
HAND_POINTS = ((5, 5), (6, 6), (0, 4), (8, 7), (6, 4), (7, 5), (9, 3))
HAND_DEMAND = (0, 6, 3, 4, 3, 2, 6)
HAND_CENTRES = (0, 27, 14, 22, 24, 27, 25)
HAND_DUALS = (0, 8, 10, 7, 7, 11, 13)
HAND_SERVICE, HAND_HORIZON, HAND_CAPACITY = 2, 36, 99
HAND_DETAIL_WIDTH = 6

# --- Farben ---------------------------------------------------------------------------------------------------------------------------------
COLOR_TRAVEL = "#4c78a8"
COLOR_WAIT = "#9aa0a6"
COLOR_SERVICE = "#2F6B65"
COLOR_WINDOW = "#d98c2b"
COLOR_RANDOM = "#4c78a8"
COLOR_CLUSTER = "#c8553d"
COLOR_DEPOT = "#222222"

PRESET_KEYS_ORDER = ("hand_w", "n", "breite", "typ", "k", "seed")
PRESETS = {
    "Mittlere Fenster (Voreinstellung)": {"hand_w": 6, "n": 30, "breite": 40, "typ": "zufällig", "k": 5, "seed": 0},
    "Schmale Fenster": {"hand_w": 2, "n": 30, "breite": 20, "typ": "zufällig", "k": 5, "seed": 0},
    "Breite Fenster": {"hand_w": 60, "n": 30, "breite": 150, "typ": "zufällig", "k": 5, "seed": 0},
    "Gruppierte Kunden, breite Fenster": {"hand_w": 24, "n": 30, "breite": 100, "typ": "gruppiert", "k": 5, "seed": 0},
}
PRESET_HELP = {
    "Mittlere Fenster (Voreinstellung)": "Handbeispiel mit Fensterbreite 6; 30 zufällig verteilte Kunden mit Fensterbreite 40, ng-Gedächtnis 5 und Zufalls-Seed 0 (wie die erste Instanz der Messreihe). Das Verdikt von Experiment 3 meldet: Warten ist häufig.",
    "Schmale Fenster": "Handbeispiel mit Fensterbreite 2; 30 zufällig verteilte Kunden mit Fensterbreite 20, der engsten Breite des Reglers. Je erzeugtem Label scheitern mehr als fünf Verlängerungen am Fensterende.",
    "Breite Fenster": "Handbeispiel mit Fensterbreite 60; 30 zufällig verteilte Kunden mit Fensterbreite 150, der breitesten live gerechneten Breite. Warten ist hier selten: weniger als 10 % der Labels warten.",
    "Gruppierte Kunden, breite Fenster": "Handbeispiel mit Fensterbreite 24; 30 Kunden in fünf Gruppen mit Fensterbreite 100. In der Messreihe erzeugen gruppierte Kunden bei jeder der sechs Breiten im Median mehr Labels als zufällig verteilte.",
}
