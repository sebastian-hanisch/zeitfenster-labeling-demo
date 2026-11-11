"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Beschriftungen stehen als Text oder Annotation, nicht als Text-Spur; Werte werden auf wenige Stellen gerundet, damit die Figuren klein bleiben."""

import math

import plotly.graph_objects as go

import zfl_algorithm as A
import zfl_constants as C
import zfl_evaluation as ev


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.25) if legend else None)
    return lock_axes(fig)


def _log_range(values):
    """Fester Bereich einer logarithmischen Achse (Zehnerlogarithmen), mit etwas Rand um die Werte: so muss Plotly beim ersten Zeichnen nichts schätzen."""
    return [math.log10(min(values)) - 0.15, math.log10(max(values)) + 0.15]


# --- Experiment 1: Zeitstrahl eines Labels ---------------------------------------------------------------------------------------------------

def build_timeline(inst, groups, horizon=None):
    """Zeitstrahl: je Halt einer Route eine Zeile mit Fahrt (blau), Warten (grau schraffiert), Bedienung (grün) und dem Zeitfenster als dünnem Balken
    darunter. `groups`: Liste (Name, Route); der Horizont H steht als gestrichelte Linie."""
    horizon = inst.H if horizon is None else horizon
    travel = dict(x=[], base=[], y=[], hover=[])
    wait = dict(x=[], base=[], y=[], hover=[])
    service = dict(x=[], base=[], y=[], hover=[])
    labels, shapes, pos = [], [], 0
    for name, route in groups:
        stops, back = A.schedule(inst, route)
        for s in stops:
            labels.append(f"{name}: Kunde {s.customer}")
            if s.arrival > s.leave:
                travel["x"].append(s.arrival - s.leave)
                travel["base"].append(s.leave)
                travel["y"].append(pos)
                travel["hover"].append(f"Fahrt von {ev.num(s.leave)} bis {ev.num(s.arrival)}")
            if s.wait > 0:
                wait["x"].append(s.wait)
                wait["base"].append(s.arrival)
                wait["y"].append(pos)
                wait["hover"].append(f"Warten von {ev.num(s.arrival)} bis {ev.num(s.start)}")
            service["x"].append(s.end - s.start)
            service["base"].append(s.start)
            service["y"].append(pos)
            service["hover"].append(f"Bedienung von {ev.num(s.start)} bis {ev.num(s.end)}")
            e, l = s.window
            shapes.append(dict(type="rect", x0=e, x1=l, y0=pos + 0.33, y1=pos + 0.46, fillcolor=C.COLOR_WINDOW, line=dict(width=0), layer="below"))
            pos += 1
        if stops:
            labels.append(f"{name}: zurück zum Depot")
            travel["x"].append(back - stops[-1].end)
            travel["base"].append(stops[-1].end)
            travel["y"].append(pos)
            travel["hover"].append(f"Fahrt von {ev.num(stops[-1].end)} bis {ev.num(back)}")
            pos += 1
    fig = go.Figure()
    for data, name, color, pattern in ((travel, "Fahrt", C.COLOR_TRAVEL, None), (wait, "Warten", "#d9dbde", "/"), (service, "Bedienung", C.COLOR_SERVICE, None)):
        marker = dict(color=color, line=dict(color=C.COLOR_WAIT, width=1)) if pattern else dict(color=color)
        if pattern:
            marker["pattern"] = dict(shape=pattern, fgcolor=C.COLOR_WAIT)
        fig.add_trace(go.Bar(x=data["x"], base=data["base"], y=data["y"], orientation="h", width=0.55, name=name, marker=marker,
                             text=None, hovertext=data["hover"], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(symbol="square", size=10, color=C.COLOR_WINDOW), name="Zeitfenster [e, l]"))
    fig.add_vline(x=horizon, line_dash="dash", line_color="#777777")
    fig.add_annotation(x=horizon, y=0, yref="paper", yshift=-2, text="Horizont H", showarrow=False, xanchor="right", font=dict(size=11))
    fig.update_layout(barmode="overlay", shapes=shapes)
    fig.update_xaxes(title_text="Zeit", range=[0, horizon + 2], dtick=4 if horizon <= 40 else None)
    fig.update_yaxes(tickmode="array", tickvals=list(range(len(labels))), ticktext=labels, autorange="reversed")
    return _base(fig, height=max(240, 34 * len(labels) + 110))


# --- Experiment 2: Breite gegen Nutzen -------------------------------------------------------------------------------------------------------

def build_best_value(rows):
    xs = [r["w"] for r in rows]
    fig = go.Figure(go.Scatter(x=xs, y=[r["best"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_SERVICE, width=3),
                               hovertemplate="Breite %{x}: bester Wert %{y}<extra></extra>", name="bester Wert"))
    fig.update_xaxes(title_text="Fensterbreite w", type="category")
    fig.update_yaxes(title_text="bester Wert (kleiner ist besser)")
    return _base(fig, height=320, legend=False)


def build_labels_routes(rows):
    xs = [str(r["w"]) for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["labels"] for r in rows], name="erzeugte Labels", marker_color=C.COLOR_TRAVEL, hovertemplate="Breite %{x}: %{y} Labels<extra></extra>"))
    fig.add_trace(go.Bar(x=xs, y=[r["routes"] for r in rows], name="zulässige Routen", marker_color=C.COLOR_WINDOW, hovertemplate="Breite %{x}: %{y} Routen<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Fensterbreite w", type="category")
    fig.update_yaxes(title_text="Anzahl")
    return _base(fig, height=320)


# --- Experiment 3: Größenregler --------------------------------------------------------------------------------------------------------------

def build_map(inst):
    """Karte: Kunden nach Fensterbeginn gefärbt, Depot als Quadrat. Gleicher Maßstab in x und y (scaleanchor mit autorange, Rand über zwei unsichtbare Punkte)."""
    xs = [p[0] for p in inst.pts[1:]]
    ys = [p[1] for p in inst.pts[1:]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[-4, 104], y=[-4, 104], mode="markers", marker=dict(opacity=0, size=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[round(x, 2) for x in xs], y=[round(y, 2) for y in ys], mode="markers", name="Kunden",
        marker=dict(size=10, color=[round(e, 1) for e in inst.ready[1:]], colorscale="Viridis", cmin=0, cmax=inst.H, showscale=True,
                    colorbar=dict(title=dict(text="Fensterbeginn", side="top"), thickness=12, tickvals=[0, 100, 200, 300], len=0.8)),
        customdata=[[i, round(inst.ready[i], 1), round(inst.due[i], 1)] for i in range(1, inst.n + 1)],
        hovertemplate="Kunde %{customdata[0]}<br>Fenster [%{customdata[1]}, %{customdata[2]}]<extra></extra>"))
    fig.add_trace(go.Scatter(x=[inst.pts[0][0]], y=[inst.pts[0][1]], mode="markers", name="Depot", marker=dict(symbol="square", size=14, color=C.COLOR_DEPOT),
                             hovertemplate="Depot<extra></extra>"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x")
    return _base(fig, height=380)


def build_window_plan(inst):
    """Fensterplan: je Kunde der Balken [e, l] auf der Zeitachse, nach Fensterbeginn sortiert; der Horizont H begrenzt die Achse."""
    order = sorted(range(1, inst.n + 1), key=lambda i: (inst.ready[i], i))
    fig = go.Figure(go.Bar(
        x=[round(inst.due[i] - inst.ready[i], 1) for i in order], base=[round(inst.ready[i], 1) for i in order], y=[f"{i}" for i in order], orientation="h",
        marker_color=C.COLOR_WINDOW, hovertemplate="Kunde %{y}: Fenster ab %{base}, Breite %{x}<extra></extra>", width=0.8))
    fig.update_xaxes(title_text="Zeit (Horizont H = 300)", range=[0, inst.H])
    fig.update_yaxes(title_text="Kunde", type="category", categoryorder="array", categoryarray=[f"{i}" for i in order], autorange="reversed",
                     tickfont=dict(size=9))
    return _base(fig, height=380, legend=False)


# --- Experiment 4: Bänder --------------------------------------------------------------------------------------------------------------------

def build_band(rows_by_type, live=None):
    """Median (Linie) und Maximum (gepunktet) der erzeugten Labels je Breite, beide Typen, logarithmische Achse; optional der Wert des Größenreglers."""
    colors = {"zufällig": C.COLOR_RANDOM, "gruppiert": C.COLOR_CLUSTER}
    fig = go.Figure()
    for typ, rows in rows_by_type.items():
        xs = [r["breite"] for r in rows]
        fig.add_trace(go.Scatter(x=xs, y=[r["median"] for r in rows], mode="lines+markers", name=f"Median, {typ}", line=dict(color=colors[typ], width=3),
                                 hovertemplate=f"{typ}, Breite %{{x}}: Median %{{y}} Labels<extra></extra>"))
        fig.add_trace(go.Scatter(x=xs, y=[r["max"] for r in rows], mode="lines", name=f"Maximum, {typ}", line=dict(color=colors[typ], width=1.5, dash="dot"),
                                 hovertemplate=f"{typ}, Breite %{{x}}: Maximum %{{y}} Labels<extra></extra>"))
    if live is not None:
        fig.add_trace(go.Scatter(x=[live[0]], y=[live[1]], mode="markers", name="Größenregler (diese Instanz)", marker=dict(symbol="star", size=15, color="#111111"),
                                 hovertemplate="Größenregler: Breite %{x}, %{y} Labels<extra></extra>"))
    fig.update_xaxes(title_text="Fensterbreite", tickvals=list(C.BAND_WIDTHS))
    values = [r[key] for rows in rows_by_type.values() for r in rows for key in ("median", "max")]
    fig.update_yaxes(title_text="erzeugte Labels (logarithmisch)", type="log", range=_log_range(values))
    return _base(fig, height=380)


def build_v1(table):
    """Ganze Spaltenerzeugung: Median der Labels je Breite, eine Linie je ng-Gedächtnis k (30 = elementar; bei Breite 200 6 von 6 abgebrochen)."""
    fig = go.Figure()
    for k in C.V1_KS:
        pts = [(r["breite"], r["median_labels"]) for r in table if r["k"] == k and r["median_labels"] is not None]
        name = "elementar" if k == C.BAND_N else f"k = {k}"
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", name=name,
                                 hovertemplate=f"{name}, Breite %{{x}}: Median %{{y}} Labels<extra></extra>"))
    fig.update_xaxes(title_text="Fensterbreite", tickvals=list(C.V1_WIDTHS))
    values = [r["median_labels"] for r in table if r["median_labels"] is not None]
    fig.update_yaxes(title_text="Labels der ganzen Spaltenerzeugung (logarithmisch)", type="log", range=_log_range(values))
    return _base(fig, height=380)


# --- Experiment 5: Warten --------------------------------------------------------------------------------------------------------------------

def build_waiting_share(rows_by_type):
    colors = {"zufällig": C.COLOR_RANDOM, "gruppiert": C.COLOR_CLUSTER}
    fig = go.Figure()
    for typ, rows in rows_by_type.items():
        fig.add_trace(go.Scatter(x=[r["breite"] for r in rows], y=[r["wartet_mittel_prozent"] for r in rows], mode="lines+markers", name=typ,
                                 line=dict(color=colors[typ], width=3), hovertemplate=f"{typ}, Breite %{{x}}: %{{y}} % warten<extra></extra>"))
    fig.add_hline(y=C.WAIT_RARE_PERCENT, line_dash="dash", line_color="#777777")
    fig.update_xaxes(title_text="Fensterbreite", tickvals=list(C.BAND_WIDTHS))
    fig.update_yaxes(title_text="Anteil der Labels, die warten (%)", range=[0, 82])
    return _base(fig, height=320)


def build_window_out(rows_by_type):
    colors = {"zufällig": C.COLOR_RANDOM, "gruppiert": C.COLOR_CLUSTER}
    fig = go.Figure()
    for typ, rows in rows_by_type.items():
        fig.add_trace(go.Scatter(x=[r["breite"] for r in rows], y=[r["fenster_aus_je_label_mittel"] for r in rows], mode="lines+markers", name=typ,
                                 line=dict(color=colors[typ], width=3), hovertemplate=f"{typ}, Breite %{{x}}: %{{y}} je Label<extra></extra>"))
    fig.update_xaxes(title_text="Fensterbreite", tickvals=list(C.BAND_WIDTHS))
    fig.update_yaxes(title_text="am Fensterende gescheiterte Verlängerungen je Label", range=[0, 6.5])
    return _base(fig, height=320)
