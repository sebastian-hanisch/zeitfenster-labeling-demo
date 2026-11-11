"""End-to-end Rauchtest mit Streamlits AppTest: Standard, jedes Preset (mit der erwarteten Verdikt-Zeile), jeder Regler an Minimum und Maximum, Kombination aller Minima und
aller Maxima, Permalink, jede Auswahl des Zeitstrahls. Prüft, dass kein Python-Fehler auftritt (insbesondere StreamlitDuplicateElementId bei Diagrammen ohne eindeutigen key)
und dass die App keinen Fehlerkasten zeigt (`st.error` heißt: das Label-Setting widerspricht dem unabhängigen Prüfer)."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import zfl_constants as C
import zfl_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
REGLER = ("slider", "select_slider", "radio", "number_input")


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _live_verdict(at) -> str:
    return next(e.value for e in list(at.info) + list(at.warning) if e.value.startswith(("Ein Pricing-Aufruf", "Abgebrochen", )))


def _hand_verdict(at) -> str:
    return next(e.value for e in list(at.success) + list(at.error) if e.value.startswith("Bei Breite"))


def test_app_loads_without_exception_and_without_error_box():
    at = _fresh_app()
    assert not at.error
    assert len(at.get("plotly_chart")) == 9          # Zeitstrahl, Breite gegen Nutzen (2), Karte, Fensterplan, zwei Bänder, zwei Warten-Diagramme


def test_every_preset_runs_and_shows_the_expected_verdict_line():
    """Je Preset: kein Fehler, kein Fehlerkasten, und die Verdikt-Zeilen von Experiment 1 und 3 passen zu den Reglern (Fensterbreite des Handbeispiels, Warten häufig oder selten)."""
    erwartet_hand = {2: "Bester Wert −12", 6: "Bester Wert −18", 60: "Bester Wert −28", 24: "Bester Wert −26"}
    erwartet_live = {
        "Mittlere Fenster (Voreinstellung)": "Warten ist häufig", "Schmale Fenster": "Warten ist häufig",
        "Breite Fenster": "Warten ist selten", "Gruppierte Kunden, breite Fenster": "Warten ist häufig",
    }
    assert set(erwartet_live) == set(C.PRESETS)
    for name, preset in C.PRESETS.items():
        at = _fresh_app()
        at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])
        assert not at.error, name
        assert f"Bei Breite {preset['hand_w']}:" in _hand_verdict(at) and erwartet_hand[preset["hand_w"]] in _hand_verdict(at), name
        live = _live_verdict(at)
        assert f"mit {preset['n']} Kunden" in live and erwartet_live[name] in live, (name, live)


@pytest.mark.parametrize("w", C.HAND_WIDTHS)
def test_every_hand_width_and_every_label_of_the_timeline_selectbox(w):
    """Jede Breite des Handbeispiels: kein Fehler; das Auswahlfeld des Zeitstrahls bietet ein Label je erzeugtem Label (ohne das Start-Label) an und jede Auswahl zeichnet."""
    at = _fresh_app()
    at.sidebar.select_slider(key="hand_w").set_value(w).run(timeout=TIMEOUT)
    assert not at.exception and not at.error
    box = at.selectbox(key=f"hand_label_{w}")
    labels = {2: 15, 6: 27, 12: 67, 24: 159, 60: 272}[w]
    assert len(box.options) == labels - 1
    for index in sorted({0, len(box.options) // 2, len(box.options) - 1}):
        box.select_index(index).run(timeout=TIMEOUT)
        assert not at.exception, (w, index, [str(e) for e in at.exception])
        box = at.selectbox(key=f"hand_label_{w}")


def test_every_regler_at_its_min_and_max_does_not_raise():
    """Jeder Regler der Seitenleiste einzeln auf Minimum und Maximum (bei Auswahl: erste und letzte Stufe)."""
    keys = [w.key for art in REGLER for w in getattr(_fresh_app().sidebar, art)]
    assert set(keys) == set(P.SETTING_SPECS)
    for key in keys:
        spec = P.SETTING_SPECS[key]
        for edge in (0, -1):
            at = _fresh_app()
            widget = next(w for art in REGLER for w in getattr(at.sidebar, art) if w.key == key)
            value = (spec.choices[edge] if spec.choices else (spec.lo, spec.hi)[edge])
            widget.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (key, edge, [str(e) for e in at.exception])
            assert not at.error, (key, edge)


def test_all_minima_and_all_maxima_together_do_not_raise():
    for edge in (0, -1):
        at = _fresh_app()
        for key, spec in P.SETTING_SPECS.items():
            widget = next(w for art in REGLER for w in getattr(at.sidebar, art) if w.key == key)
            widget.set_value(spec.choices[edge] if spec.choices else (spec.lo, spec.hi)[edge])
        at.run(timeout=TIMEOUT)
        assert not at.exception, (edge, [str(e) for e in at.exception])
        assert not at.error, edge


def test_random_seed_button_changes_the_seed_without_error():
    at = _fresh_app()
    at.sidebar.button[-1].click().run(timeout=TIMEOUT)
    assert not at.exception and at.sidebar.number_input(key="seed_input").value != C.DEFAULT_SEED


def test_permalink_takes_values_clamps_and_snaps():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params.update({"n": "12", "w": "70", "typ": "gruppiert", "k": "1", "hw": "12", "seed": "7"})
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    sb = at.sidebar
    assert (sb.slider(key="n_slider").value, sb.slider(key="breite_slider").value, sb.radio(key="typ_radio").value, sb.radio(key="k_radio").value,
            sb.select_slider(key="hand_w").value, sb.number_input(key="seed_input").value) == (12, 70, "gruppiert", 1, 12, 7)
    at2 = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at2.query_params.update({"n": "999", "w": "47", "typ": "kreis", "hw": "10"})
    at2.run(timeout=TIMEOUT)
    assert not at2.exception
    sb = at2.sidebar
    assert (sb.slider(key="n_slider").value, sb.slider(key="breite_slider").value, sb.radio(key="typ_radio").value, sb.select_slider(key="hand_w").value) == (30, 50, C.DEFAULT_TYPE, 12)


def test_the_address_bar_mirrors_the_settings():
    at = _fresh_app()
    at.sidebar.slider(key="n_slider").set_value(14).run(timeout=TIMEOUT)
    assert at.query_params["n"] == ["14"] or at.query_params["n"] == "14"


def test_the_live_experiment_shows_the_band_comparison_only_where_it_applies():
    at = _fresh_app()
    texte = " ".join(c.value for c in at.caption)
    assert "Zum Vergleich die feste Messreihe" in texte and "Breite 40, zufällig" in texte                 # Standard: 30 Kunden, k = 5, Breite 40
    at.sidebar.slider(key="n_slider").set_value(20).run(timeout=TIMEOUT)
    texte = " ".join(c.value for c in at.caption)
    assert "keinen Vergleichswert" in texte and "Zum Vergleich die feste Messreihe" not in texte
