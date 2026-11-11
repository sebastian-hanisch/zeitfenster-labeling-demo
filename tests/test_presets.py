"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink (Begrenzen und Einrasten), und jede Aussage der Preset-Hilfetexte."""

import pytest

import zfl_constants as C
import zfl_evaluation as ev
import zfl_presets as P


def _settings(name):
    p = C.PRESETS[name]
    return ev.Settings(p["hand_w"], p["n"], p["breite"], p["typ"], p["k"], p["seed"])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds_and_choices():
    for name, preset in C.PRESETS.items():
        assert preset["hand_w"] in C.HAND_WIDTHS and preset["typ"] in C.TYPES and preset["k"] in C.K_CHOICES, name
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX, name
        assert C.WIDTH_MIN <= preset["breite"] <= C.WIDTH_MAX and (preset["breite"] - C.WIDTH_MIN) % C.WIDTH_STEP == 0, name


def test_default_preset_equals_the_default_settings():
    assert _settings(next(iter(C.PRESETS))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_presets_are_pairwise_different():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


@pytest.mark.parametrize("key,raw,expected", [
    ("n_slider", "999", 30), ("n_slider", "-4", 10), ("n_slider", "abc", None), ("n_slider", "17", 17),
    ("breite_slider", "47", 50), ("breite_slider", "1000", 150), ("breite_slider", "0", 20), ("breite_slider", "44", 40),
    ("hand_w", "10", 12), ("hand_w", "1", 2), ("hand_w", "500", 60), ("hand_w", "24", 24),
    ("k_radio", "3", 1), ("k_radio", "4", 5), ("k_radio", "5", 5),
    ("typ_radio", "gruppiert", "gruppiert"), ("typ_radio", "kreis", None),
    ("seed_input", "9999999", C.SEED_MAX), ("seed_input", "-5", 0),
])
def test_permalink_values_are_clamped_and_snapped(key, raw, expected):
    assert P.clean_value(P.SETTING_SPECS[key], raw) == expected


# --- Jede Aussage der Preset-Hilfetexte ------------------------------------------------------------------------------------------------------

def test_help_mittlere_fenster_says_waiting_is_frequent():
    kind, text = ev.verdict_live(ev.live_run(_settings("Mittlere Fenster (Voreinstellung)")))
    assert "Warten ist häufig" in text and "Warten ist häufig" in C.PRESET_HELP["Mittlere Fenster (Voreinstellung)"]


def test_help_schmale_fenster_says_more_than_five_extensions_fail_per_label():
    live = ev.live_run(_settings("Schmale Fenster"))
    assert live.window_out_per_label > 5 and "mehr als fünf Verlängerungen" in C.PRESET_HELP["Schmale Fenster"]


def test_help_breite_fenster_says_waiting_is_rare():
    live = ev.live_run(_settings("Breite Fenster"))
    assert live.waiting_percent < 10 and "Warten ist selten" in ev.verdict_live(live)[1]
    assert "weniger als 10 % der Labels" in C.PRESET_HELP["Breite Fenster"]


def test_help_gruppierte_kunden_says_clustered_has_more_labels_at_every_width():
    z, g = ev.band_p03_rows("zufällig"), ev.band_p03_rows("gruppiert")
    assert [r["breite"] for r in z] == [r["breite"] for r in g] == list(C.BAND_WIDTHS)
    assert all(b["median"] > a["median"] for a, b in zip(z, g))
    assert "bei jeder der sechs Breiten im Median mehr Labels" in C.PRESET_HELP["Gruppierte Kunden, breite Fenster"]
