"""Darstellung: Blick auf den Hof (Reihen mit Belegung, gassenseitig markiert), H-Kurve,
Kipppunkt-Kurve über sigma, Vergleichsbalken. Alle Achsen fixedrange (Touch-Scrolling), graue
Marker-Linien, jedes plotly_chart mit eindeutigem key= (siehe app.py)."""

import plotly.graph_objects as go

import hst_constants as C


def _lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def yard_figure(n_rows, depth, occupancy, title):
    """occupancy: Tupel je Reihe von Tupeln (item_idx, ...), stack[-1] = vorne (Gasse). Ein Rechteck
    je Stellplatz, freie Plätze hell, belegte dunkel; die Gassenseite (vorne) ist rechts markiert."""
    fig = go.Figure()
    for r in range(n_rows):
        occ = occupancy[r] if r < len(occupancy) else ()
        for slot in range(depth):
            filled = slot < len(occ)
            color = C.COLOR_LOOKAHEAD if filled else "#eef1f5"
            x0 = slot
            fig.add_shape(type="rect", x0=x0, x1=x0 + 0.92, y0=r, y1=r + 0.8, fillcolor=color, line=dict(color=C.MARKER_LINE_COLOR, width=1))
            if filled:
                fig.add_annotation(x=x0 + 0.46, y=r + 0.4, text=str(occ[slot]), showarrow=False, font=dict(size=9, color="white"))
        fig.add_annotation(x=depth + 0.15, y=r + 0.4, text=f"R{r}", showarrow=False, font=dict(size=10, color="#5b6b80"), xanchor="left")
    fig.add_annotation(x=depth - 0.04, y=n_rows + 0.15, text="Gasse (Zufahrt) →", showarrow=False, font=dict(size=10, color="#5b6b80"), xanchor="right")
    fig.update_layout(title=title, height=max(220, 40 * n_rows + 60), showlegend=False, margin=dict(l=10, r=10, t=40, b=10),
                       xaxis=dict(visible=False, range=[-0.3, depth + 1.4]), yaxis=dict(visible=False, range=[-0.3, n_rows + 0.6], autorange="reversed"))
    return _lock_axes(fig)


def h_curve_figure(points):
    """points: [(h, r, naiv_total, look_total), ...]"""
    xs = [f"H={h}" for h, *_ in points]
    fig = go.Figure()
    fig.add_bar(name="Nächster freier Platz", x=xs, y=[p[2] for p in points], marker_color=C.COLOR_NAIVE)
    fig.add_bar(name="Vorausschauend", x=xs, y=[p[3] for p in points], marker_color=C.COLOR_LOOKAHEAD)
    fig.update_layout(barmode="group", height=C.CHART_HEIGHT, yaxis_title="Gesamtstrecke je Auftrag (m)", legend=dict(orientation="h", y=-0.15),
                       margin=dict(l=10, r=10, t=20, b=10))
    return _lock_axes(fig)


def sigma_curve_figure(points):
    """points: [(sigma, naiv_total, look_total), ...]"""
    xs = [p[0] for p in points]
    fig = go.Figure()
    fig.add_scatter(x=xs, y=[p[1] for p in points], mode="lines+markers", name="Nächster freier Platz", line=dict(color=C.COLOR_NAIVE), marker=dict(line=dict(color=C.MARKER_LINE_COLOR, width=1)))
    fig.add_scatter(x=xs, y=[p[2] for p in points], mode="lines+markers", name="Vorausschauend", line=dict(color=C.COLOR_LOOKAHEAD), marker=dict(line=dict(color=C.MARKER_LINE_COLOR, width=1)))
    fig.update_layout(height=C.CHART_HEIGHT, xaxis_title="Schätzfehler der Abholzeit σ (%)", yaxis_title="Gesamtstrecke je Auftrag (m)", legend=dict(orientation="h", y=-0.2),
                       margin=dict(l=10, r=10, t=20, b=10))
    return _lock_axes(fig)


def comparison_figure(res_n, res_l):
    labels = ["Anfahrt je Abholung (m)", "Umsetzungen je Auftrag", "Umsetz-Mehrstrecke je Auftrag (m)", "Gesamtstrecke je Auftrag (m)"]
    naiv_vals = [res_n.mean_retrieval_dist, res_n.reloc_per_item, res_n.reloc_extra_dist_per_item, res_n.total_dist_per_item]
    look_vals = [res_l.mean_retrieval_dist, res_l.reloc_per_item, res_l.reloc_extra_dist_per_item, res_l.total_dist_per_item]
    fig = go.Figure()
    fig.add_bar(name="Nächster freier Platz", x=labels, y=naiv_vals, marker_color=C.COLOR_NAIVE)
    fig.add_bar(name="Vorausschauend", x=labels, y=look_vals, marker_color=C.COLOR_LOOKAHEAD)
    fig.update_layout(barmode="group", height=C.CHART_HEIGHT, legend=dict(orientation="h", y=-0.25), margin=dict(l=10, r=10, t=20, b=10))
    return _lock_axes(fig)
