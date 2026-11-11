"""Zeitfenster und Warten im Label-Setting - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein Zeitfenster [e, l] je Kunde: wer zu früh kommt, wartet (kostenlos), wer zu spät kommt, scheidet aus. Handbeispiel Schritt für Schritt, Größenregler und
feste Messreihen zur Frage, wie stark die Fensterbreite die Zahl der erzeugten Labels steuert. Aufbau nach DEMO-PLAYBOOK §2.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import zfl_constants as C
import zfl_evaluation as ev
import zfl_texts as T
from zfl_layout import dunkles_design, kopf_css
from zfl_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from zfl_visualization import (
    build_band,
    build_best_value,
    build_labels_routes,
    build_map,
    build_timeline,
    build_v1,
    build_waiting_share,
    build_window_out,
    build_window_plan,
)

st.set_page_config(page_title="Zeitfenster und Warten im Label-Setting – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _live(settings):
    return ev.live_run(settings)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in zfl_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("⏱️ Zeitfenster und Warten im Label-Setting")
st.markdown(T.INTRO_MARKDOWN)

with st.expander("So funktioniert ein Zeitfenster im Label-Setting", expanded=True):
    st.markdown(T.HOW_MARKDOWN)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Handbeispiel (6 Kunden)**")
    hand_w = st.select_slider(
        "Fensterbreite w", options=list(C.HAND_WIDTHS), key="hand_w",
        help="Breite aller Zeitfenster im Handbeispiel (Experimente 1, 2 und 5). Das Fenster liegt um einen festen Mittelpunkt je Kunde.",
    )
    st.markdown("**Größenregler (Solomon-artige Instanz)**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help="Zahl der Kunden der Zufallsinstanz (Experiment 3).")
    breite = st.slider(
        "Fensterbreite", *bounds("breite_slider"), step=C.WIDTH_STEP, key="breite_slider",
        help="Breite der Zeitfenster auf der Zeitachse 0 bis 300. Live bis 150; Breite 200 gibt es nur als feste Messreihe (Experiment 4).",
    )
    typ = st.radio("Verteilung der Kunden", list(C.TYPES), key="typ_radio", horizontal=True, help="Zufällig im Quadrat oder in fünf Gruppen.")
    k = st.radio(
        "ng-Gedächtnis k", list(C.K_CHOICES), key="k_radio", horizontal=True, format_func=lambda x: f"k = {x}",
        help="Wie viele nächste Nachbarn ein Label sich merkt, um keinen Kunden zu wiederholen. k = 1: nur die sofortige Wiederholung ist verboten, Kunden dürfen "
             "wiederkehren. k = 5: ein besuchter Kunde bleibt gesperrt, solange er bei jedem weiteren Besuch unter den 5 nächsten Kunden des gerade besuchten Kunden liegt; sonst "
             "wird er vergessen und darf wiederkehren.",
    )
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"hand_w": int(hand_w), "n_slider": int(n), "breite_slider": int(breite), "typ_radio": typ, "k_radio": int(k), "seed_input": int(seed)})
settings = ev.Settings(int(hand_w), int(n), int(breite), typ, int(k), int(seed))

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie stark steuert die Fensterbreite die Zahl der Labels?")
band = {t: ev.band_p03_rows(t) for t in C.TYPES}
m = st.columns(4)
for col, typ_name in zip(m[:2], C.TYPES):
    rows = band[typ_name]
    col.metric(f"Median, Breite {rows[0]['breite']} ({typ_name})", ev.de_int(rows[0]["median"]))
    col2 = m[2 if typ_name == C.TYPES[0] else 3]
    col2.metric(f"Median, Breite {rows[-1]['breite']} ({typ_name})", ev.de_int(rows[-1]["median"]), delta=f"Faktor {ev.de(rows[-1]['median'] / rows[0]['median'])}", delta_color="off")
kind, text = ev.verdict_band(band)
getattr(st, kind)(text)
st.caption("Feste Messreihe, hier wird nichts gerechnet: Median der erzeugten Labels in einem Pricing-Aufruf, 30 Kunden, ng-Gedächtnis 5, 12 Instanzen je Zelle, "
           "Dualpreise der ersten Runde (Tabellen in Experiment 4).")

st.markdown("---")

# --- Experiment 1: Handbeispiel Schritt für Schritt ----------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Zeitfenster Schritt für Schritt (Handbeispiel)")
run = ev.hand_run(settings.hand_w)
overview = {r["w"]: r for r in ev.hand_overview()}
row = overview[settings.hand_w]
st.markdown(
    f"Depot und 6 Kunden auf einem Gitter (Manhattan-Abstand, Fahrzeit gleich Entfernung, Bedienzeit 2, Horizont 36, jeder Kunde höchstens einmal). "
    f"Die Fensterbreite w = **{settings.hand_w}** stellen Sie in der Seitenleiste ein. Das Fenster liegt um einen festen Mittelpunkt je Kunde und ist auf die "
    f"zulässige Zeitspanne beschnitten."
)
st.dataframe(ev.hand_customer_rows(run.inst), hide_index=True, width="stretch")
if not run.matches:
    st.error("Das Label-Setting findet einen anderen besten Wert als die Aufzählung aller zulässigen Routen.")
c = st.columns(5)
c[0].metric("Erzeugte Labels", ev.de_int(row["labels"]))
c[1].metric("Dominiert", ev.de_int(row["dominated"]))
c[2].metric("Warteten", ev.de_int(row["waiting"]), help="Labels, die vor dem Fensterbeginn ankamen und bis dahin warteten")
c[3].metric("Fenster-Aus", ev.de_int(row["window_out"]), help="Verlängerungen, die wegen des Fensterendes verworfen wurden")
c[4].metric("Bester Wert", ev.num(row["best"]), help="Beste reduzierte Kosten einer Route; kleiner ist besser")
kind, text = ev.verdict_hand(row)
getattr(st, kind)(text)

st.markdown("**Das Protokoll:** jedes erzeugte Label mit Ankunft, Fenster, Wartezeit und der Entscheidung der Dominanz.")
label_rows = ev.hand_label_rows(run)
st.dataframe(label_rows, hide_index=True, width="stretch", height=min(40 + 35 * len(label_rows), 420))
with st.expander(f"Verworfene Verlängerungen am Fensterende ({len(run.result.trace.window_out)})"):
    st.dataframe(ev.hand_window_out_rows(run), hide_index=True, width="stretch", height=min(40 + 35 * len(run.result.trace.window_out), 400))

records = run.result.trace.labels
options = [rec.serial for rec in records if rec.serial > 0]
default_label = next((rec.serial for rec in records if rec.status == "dominiert" and rec.same_time), None)
if default_label is None:
    default_label = next((rec.serial for rec in records if rec.path == run.result.best_route and rec.status == "bleibt" and rec.serial > 0), options[0])
st.markdown("**Zeitstrahl eines Labels:** Fahrt, Warten (schraffiert), Bedienung und das Zeitfenster. Ist das Label dominiert, steht sein Gegenstück darunter.")
chosen = st.selectbox(
    "Label wählen", options, index=options.index(default_label), key=f"hand_label_{settings.hand_w}",
    format_func=lambda s: f"L{s}: Weg {'-'.join(map(str, records[s].path))} ({ev.decision_text(records[s])})",
)
groups = [(f"L{chosen}", records[chosen].path)]
if records[chosen].by >= 0:
    groups.append((f"L{records[chosen].by}", records[records[chosen].by].path))
st.plotly_chart(build_timeline(run.inst, groups), width="stretch", key=f"timeline_{settings.hand_w}_{chosen}")

st.markdown("---")

# --- Experiment 2: Breite gegen Nutzen -----------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Breite gegen Nutzen (Handbeispiel)")
st.caption("Alle fünf Breiten des Handbeispiels nebeneinander. Die Aufzählung zählt die zulässigen Routen unabhängig vom Label-Setting.")
rows_all = ev.hand_overview()
st.dataframe(
    [{"Breite w": r["w"], "Zulässige Routen": r["routes"], "Bester Wert": ev.num(r["best"]), "Route": "-".join(map(str, r["best_route"])),
      "Erzeugte Labels": r["labels"], "Dominiert": r["dominated"], "Warteten": r["waiting"], "Fenster-Aus": r["window_out"]} for r in rows_all],
    hide_index=True, width="stretch",
)
c1, c2 = st.columns(2)
c1.plotly_chart(build_best_value(rows_all), width="stretch", key="best_value_chart")
c2.plotly_chart(build_labels_routes(rows_all), width="stretch", key="labels_routes_chart")
kind, text = ev.verdict_breite_nutzen(rows_all)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3: Größenregler ------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Größenregler – ein Pricing-Aufruf auf einer Solomon-artigen Instanz")
st.caption("Kunden, Fensterbreite, Verteilung, ng-Gedächtnis und Zufalls-Seed stellen Sie in der Seitenleiste ein. Gerechnet wird ein Pricing-Aufruf mit den Dualpreisen "
           "der ersten Runde (je Kunde das Doppelte der Entfernung zum Depot); die Rechnung kann bei breiten Fenstern einige Sekunden dauern.")
with st.spinner("Rechnet … bei Breite 150 und gruppierten Kunden bis zu einigen Sekunden"):
    live = _live(settings)
res = live.result
if not live.valid:
    st.error("Die beste Route besteht den unabhängigen Prüfer nicht: Das Label-Setting liefert hier ein falsches Ergebnis.")
c = st.columns(5)
c[0].metric("Erzeugte Labels", ev.de_int(res.generated))
c[1].metric("Dominiert", f"{ev.de(live.dominated_percent)} %")
c[2].metric("Warteten", f"{ev.de(live.waiting_percent)} %", help="Anteil der erzeugten Labels, die vor dem Fensterbeginn ankamen")
c[3].metric("Wartezeit je wartendem Label", ev.de(live.wait_mean))
c[4].metric("Fenster-Aus je Label", ev.de(live.window_out_per_label, 2), help="Am Fensterende gescheiterte Verlängerungen je erzeugtem Label")
kind, text = ev.verdict_live(live)
getattr(st, kind)(text)
ref = ev.band_reference(settings)
if ref is not None:
    st.caption(f"Zum Vergleich die feste Messreihe (30 Kunden, ng-Gedächtnis 5, Breite {ref['breite']}, {settings.typ}, 12 Instanzen mit den Zufalls-Seeds 0 bis 11): "
               f"Median {ev.de_int(ref['median'])} Labels, Maximum {ev.de_int(ref['max'])}. Diese Instanz (Zufalls-Seed {settings.seed}): {ev.de_int(res.generated)}.")
else:
    st.caption("Die feste Messreihe gilt nur für 30 Kunden, ng-Gedächtnis 5 und die Breiten 20, 40, 70, 100, 150 und 200; für diese Einstellung gibt es keinen Vergleichswert.")
c1, c2 = st.columns(2)
c1.plotly_chart(build_map(live.inst), width="stretch", key="map_chart")
c2.plotly_chart(build_window_plan(live.inst), width="stretch", key="window_plan_chart")
st.caption("Links: Kunden und Depot, nach Fensterbeginn gefärbt. Rechts: das Zeitfenster jedes Kunden auf der Zeitachse, nach Fensterbeginn sortiert.")

st.markdown("---")

# --- Experiment 4: Bänder ------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Feste Messreihen")
st.caption("Nichts davon wird hier gerechnet: Die Zeilen stammen aus den Messdateien der Vormessung (`data/`, jede Zeile mit Quelle). Alle Zahlen gelten für 30 Kunden und "
           "eigene Solomon-artige Instanzen.")
st.markdown("**Ein Pricing-Aufruf** (ng-Gedächtnis 5, Dualpreise der ersten Runde, 12 Instanzen je Zelle mit den Zufalls-Seeds 0 bis 11; erzeugte Labels)")
live_point = (ref["breite"], res.generated) if ref is not None and not res.aborted else None
st.plotly_chart(build_band(band, live_point), width="stretch", key="band_chart")
for typ_name in C.TYPES:
    st.markdown(f"*Kunden {typ_name}*")
    rows = band[typ_name]
    factors = {b: f for _, b, f in ev.band_factors(rows)}
    st.dataframe(
        [{"Breite": r["breite"], "Median": ev.de_int(r["median"]), "Mittel": ev.de(r["mittel"]), "Maximum": ev.de_int(r["max"]), "Faktor des Medians zur Stufe davor": ev.de(factors[r["breite"]], 2) if r["breite"] in factors else "",
          "Dominiert, Mittel (%)": ev.de(r["dominiert_mittel_prozent"]), "Quelle": r["quelle"]} for r in rows],
        hide_index=True, width="stretch",
    )
kind, text = ev.verdict_band(band)
getattr(st, kind)(text)
st.caption("Die Mediane sind auf ganze Zahlen gerundet; wo der Median das Mittel zweier Werte ist, weicht die Zahl um 0,5 ab.")

st.markdown("**Die ganze Spaltenerzeugung** (Summe aller Pricing-Aufrufe bis zur Konvergenz, 6 Instanzen je Zelle mit den Zufalls-Seeds 0 bis 5, zufällige Kunden; k = 30 heißt elementar)")
v1 = ev.v1_table()
st.plotly_chart(build_v1(v1), width="stretch", key="v1_chart")
st.dataframe(
    [{"Breite": r["breite"], "ng-Gedächtnis k": "elementar" if r["k"] == C.BAND_N else str(r["k"]), "Läufe": r["laeufe"], "Abgebrochen": r["abgebrochen"],
      "Median der Labels (fertige Läufe)": "–" if r["median_labels"] is None else ev.de_int(r["median_labels"]),
      "Dominiert, Mittel (%)": "–" if r["dominiert_prozent"] is None else ev.de(r["dominiert_prozent"]),
      "Median der Pricing-Sekunden (nur zur Information)": "–" if r["median_sekunden"] is None else ev.de(r["median_sekunden"], 2)} for r in v1],
    hide_index=True, width="stretch",
)
k1 = [ev.v1_median(w, 1) for w in C.V1_WIDTHS]
st.info(f"Im Median wachsen die Labels der ganzen Spaltenerzeugung bei k = 1 von Breite {C.V1_WIDTHS[0]} auf Breite {C.V1_WIDTHS[-1]} auf das {ev.de(k1[-1] / k1[0])}-Fache "
        f"({ev.de_int(k1[0])} auf {ev.de_int(k1[-1])}), bei k = 5 auf das {ev.de(ev.v1_median(200, 5) / ev.v1_median(40, 5))}-Fache. "
        f"Die elementare Rechnung wurde bei Breite 100 in {next(r['abgebrochen'] for r in v1 if r['breite'] == 100 and r['k'] == C.BAND_N)} von 6 und bei Breite 200 in "
        f"{next(r['abgebrochen'] for r in v1 if r['breite'] == 200 and r['k'] == C.BAND_N)} von 6 Läufen abgebrochen; diese Zellen zeigen nur die fertigen, schnelleren Läufe (die Zeile Breite 100, elementar beruht auf 3 Läufen).")

st.markdown("---")

# --- Experiment 5: Warten --------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Wie oft wird gewartet, und wie oft scheitert eine Verlängerung am Fensterende?")
st.caption("Aus derselben Messreihe wie in Experiment 4 (ein Pricing-Aufruf, 30 Kunden, ng-Gedächtnis 5, 12 Instanzen je Zelle). Warten kostet in diesem Modell nichts.")
c1, c2 = st.columns(2)
c1.plotly_chart(build_waiting_share(band), width="stretch", key="waiting_chart")
c2.plotly_chart(build_window_out(band), width="stretch", key="window_out_chart")
for typ_name in C.TYPES:
    st.markdown(f"*Kunden {typ_name}*")
    st.dataframe(
        [{"Breite": r["breite"], "Warten, Anteil der Labels (%)": ev.de(r["wartet_mittel_prozent"]), "Wartezeit je wartendem Label (Mittel)": ev.de(r["wartezeit_je_wartendem_label_mittel"]),
          "Fenster-Aus je erzeugtem Label (Mittel)": ev.de(r["fenster_aus_je_label_mittel"], 2)} for r in band[typ_name]],
        hide_index=True, width="stretch",
    )
kind, text = ev.verdict_waiting(band)
getattr(st, kind)(text)
hand6 = ev.hand_run(C.HAND_DETAIL_WIDTH)
same = [rec for rec in hand6.result.trace.labels if rec.same_time]
st.markdown(
    f"**Im Handbeispiel bei Breite {C.HAND_DETAIL_WIDTH}** fallen {hand6.result.same_time} von {hand6.result.dominated} Dominanzen mit gleicher Zeit nach dem Warten zusammen: "
    + ", ".join(f"L{r.serial} (Weg {'-'.join(map(str, r.path))}) gegen L{r.by} (Weg {'-'.join(map(str, hand6.result.trace.labels[r.by].path))})" for r in same)
    + ". In diesen Fällen warten beide Labels bis zum Fensterbeginn desselben Kunden."
)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Gemessen? |
|---|---|---|
| **Warten kostet nichts** | Die Dominanzregel „höchstens so spät“ gilt dann nicht mehr: Ein früheres Label könnte teurer sein als ein späteres. | nein, nicht gebaut |
| **Fenster um zufällige Mittelpunkte** | Legt man die Fenster um die Ankunftszeiten eines Bezugsplans (so macht es die Tourenbildung), steht die Fensterbreite in anderem Zusammenhang zur Entfernung; ob die Label-Zahl dann ebenso wächst, zeigt diese Demo nicht. | nein |
| **Ein Pricing-Aufruf mit den Dualpreisen der ersten Runde** | In späteren Runden ändern sich die Dualpreise und damit die Zahl der Labels; die ganze Spaltenerzeugung steht nur als feste Messreihe (Experiment 4). | teilweise (6 Instanzen je Zelle) |
| **30 Kunden, eigene Instanzen** | Mit mehr Kunden oder anderen Instanzen können die Zahlen abweichen. | nein |
| **Kapazität 70 aktiv** | Die Kapazität begrenzt die Routenlänge in den Messreihen mit; ihr Anteil an der Label-Zahl gegenüber den Fenstern ist nicht getrennt gemessen. | nein |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(T.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(T.MATH_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
