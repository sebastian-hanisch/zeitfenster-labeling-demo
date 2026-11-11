"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Die Mini-Instanz ist das Handbeispiel: Depot (5, 5) und 6 Kunden auf einem Gitter, Manhattan-Abstand, Fahrzeit = Entfernung, Bedienzeit 2, Horizont 36, Kapazität 99
(wirkt nicht), ganzzahlige Dualpreise. Das Fenster der Breite w liegt um den Mittelpunkt c des Kunden, [c - w/2, c + w/2], beschnitten auf [Entfernung zum Depot,
34 - Entfernung zum Depot]. Die erwarteten Werte stammen aus einem eigenen Handrechen-Skript der Planung (Aufzählung aller Routen, unabhängig vom Label-Setting)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import zfl_scenario as S  # noqa: E402

# Werte aus dem Handrechen-Skript der Planung (Aufzählung und Label-Setting in je einer eigenen Fassung), je Breite 2 / 6 / 12 / 24 / 60
HAND_WIDTHS = (2, 6, 12, 24, 60)
HAND_ROUTES = (16, 38, 119, 292, 686)
HAND_BEST = (-12, -18, -21, -26, -28)
HAND_LABELS = (15, 27, 67, 159, 272)
HAND_DOMINATED = (4, 6, 13, 51, 164)
HAND_WAITING = (9, 9, 9, 5, 0)
HAND_WAIT_SUM = (118, 106, 88, 48, 0)
HAND_WINDOW_OUT = (38, 62, 124, 167, 43)
HAND_SAME_TIME = (3, 3, 6, 14, 37)


@pytest.fixture
def hand():
    """Fabrik: das Handbeispiel bei einer Fensterbreite."""
    return S.hand_instance


@pytest.fixture
def duals():
    return tuple(S.hand_duals())
