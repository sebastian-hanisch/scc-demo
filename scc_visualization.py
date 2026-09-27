"""Plotly-Figuren: gerichtete Karten (Kosaraju/Tarjan-Wiedergabe, starke Komponenten, Kondensations-DAG) und Kurven. Alle Achsen fest (fixedrange); Karten mit gleichem Maßstab nutzen `scaleanchor` mit
autorange und zwei unsichtbaren Eckpunkten."""

import numpy as np
import plotly.graph_objects as go

TEAL, ORANGE, BLUE, RED, PURPLE, GREY = "#2F6B65", "#f58518", "#4c78a8", "#e45756", "#7b3fbf", "#b7bec7"
PALETTE = (ORANGE, BLUE, PURPLE, "#54a24b", "#b279a2", "#9d755d", "#eeca3b", "#72b7b2", "#ff9da6")


def _arrow_lines(xy, pairs, shrink=0.14):
    """Linien, die kurz vor dem Zielknoten enden (Platz für eine Pfeilspitze als Annotation)."""
    xs, ys = [], []
    for u, v in pairs:
        x0, y0 = xy[u]
        x1, y1 = xy[v]
        xs += [x0, x0 + (x1 - x0) * (1 - shrink), None]
        ys += [y0, y0 + (y1 - y0) * (1 - shrink), None]
    return xs, ys


def _arrowheads(xy, pairs, at=0.62):
    """Ein Dreieckssymbol je Bogen an Position `at` entlang der Linie, gedreht in Fahrtrichtung (Plotly-Winkel: 0° zeigt nach oben, im Uhrzeigersinn)."""
    import math
    px, py, angles = [], [], []
    for u, v in pairs:
        x0, y0 = xy[u]
        x1, y1 = xy[v]
        px.append(x0 + (x1 - x0) * at)
        py.append(y0 + (y1 - y0) * at)
        angles.append((math.degrees(math.atan2(x1 - x0, y1 - y0))) % 360)
    return px, py, angles


def _add_arrows(fig, xy, pairs, color=GREY, size=8):
    if not pairs:
        return
    px, py, angles = _arrowheads(xy, pairs)
    fig.add_trace(go.Scatter(x=px, y=py, mode="markers", marker=dict(symbol="triangle-up", size=size, color=color, angle=angles), hoverinfo="skip", showlegend=False))


def _base_layout(fig, height=430, title=None):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=36 if title else 10, b=10), showlegend=False, title=dict(text=title, x=0.01, font=dict(size=14)) if title else None,
                      plot_bgcolor="white")
    fig.update_xaxes(visible=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, fixedrange=True)
    return fig


def _corners(fig, xy):
    pad = 0.4
    fig.add_trace(go.Scatter(x=[xy[:, 0].min() - pad, xy[:, 0].max() + pad], y=[xy[:, 1].min() - pad, xy[:, 1].max() + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip"))


def _name(inst, v):
    return inst.labels[v] if inst.labels else str(v)


def build_network(inst, node_colors=None, height=430):
    fig = go.Figure()
    xy = inst.xy
    pairs = [(u, v) for u, v, _ in inst.arcs]
    ex, ey = _arrow_lines(xy, pairs)
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=GREY, width=1.6), hoverinfo="skip"))
    _add_arrows(fig, xy, pairs, GREY, size=7 if inst.labels else 5)
    fig.add_trace(go.Scatter(x=xy[:, 0], y=xy[:, 1], mode="markers+text" if inst.labels else "markers", text=[_name(inst, v) for v in range(inst.n)] if inst.labels else None, textposition="top center",
                             marker=dict(size=13 if inst.labels else 6, color=node_colors if node_colors is not None else TEAL, line=dict(color="white", width=1))))
    _corners(fig, xy)
    return _base_layout(fig, height)


def replay(kos_or_tar, k, method):
    """Zustand nach den ersten k Ereignissen: entdeckte Knoten (mit ihrer Phase bei Kosaraju), Baumkanten, fertige SCCs."""
    found1, found2, tree1, tree2, finished_sccs = [], [], [], [], []
    phase = 1
    cur = None
    if method == "kosaraju":
        for ev in kos_or_tar.events[:k]:
            if ev[0] == "discover1":
                found1.append(ev[1])
                if ev[2] is not None:
                    tree1.append((ev[2], ev[1]))
                cur = ev[1]
            elif ev[0] == "discover2":
                phase = 2
                found2.append(ev[1])
                if ev[2] is not None:
                    tree2.append((ev[2], ev[1]))
                cur = ev[1]
            elif ev[0] == "finish2":
                finished_sccs.append((ev[2], ev[3]))
    else:
        for ev in kos_or_tar.events[:k]:
            if ev[0] in ("root", "discover"):
                found1.append(ev[1])
                if ev[0] == "discover" and ev[2] is not None:
                    tree1.append((ev[2], ev[1]))
                cur = ev[1]
            elif ev[0] == "finish" and ev[2]:
                finished_sccs.append((ev[1], ev[2]))
    return found1, found2, tree1, tree2, finished_sccs, phase, cur


def build_replay_map(inst, result, k, method):
    xy = inst.xy
    found1, found2, tree1, tree2, finished, phase, cur = replay(result, k, method)
    fig = go.Figure()
    pairs = [(u, v) for u, v, _ in inst.arcs]
    ex, ey = _arrow_lines(xy, pairs)
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#dfe3e8", width=1.2), hoverinfo="skip"))
    _add_arrows(fig, xy, pairs, "#c7ccd2", size=6 if inst.labels else 4)
    finished_nodes = set()
    for i, (_, comp) in enumerate(finished):
        finished_nodes |= set(comp)
        col = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(x=xy[comp, 0], y=xy[comp, 1], mode="markers", marker=dict(size=17 if inst.labels else 10, color=col, opacity=0.35), hoverinfo="skip"))
    if tree1:
        tx, ty = _arrow_lines(xy, tree1)
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color=TEAL, width=3), hoverinfo="skip"))
        _add_arrows(fig, xy, tree1, TEAL, size=9 if inst.labels else 6)
    if tree2:
        tx, ty = _arrow_lines(xy, tree2)
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color=RED, width=3), hoverinfo="skip"))
        _add_arrows(fig, xy, tree2, RED, size=9 if inst.labels else 6)
    all_found = list(found1) + list(found2)
    rest = [v for v in range(inst.n) if v not in set(all_found)]
    if rest:
        fig.add_trace(go.Scatter(x=xy[rest, 0], y=xy[rest, 1], mode="markers", marker=dict(size=9 if inst.labels else 5, color="#cfd4da"), hoverinfo="skip"))
    if found1:
        fig.add_trace(go.Scatter(x=xy[found1, 0], y=xy[found1, 1], mode="markers+text" if inst.labels else "markers", text=[_name(inst, v) for v in found1] if inst.labels else None, textposition="top center",
                                 marker=dict(size=14 if inst.labels else 8, color=TEAL, line=dict(color="white", width=1))))
    if found2:
        fig.add_trace(go.Scatter(x=xy[found2, 0], y=xy[found2, 1], mode="markers+text" if inst.labels else "markers", text=[_name(inst, v) for v in found2] if inst.labels else None, textposition="top center",
                                 marker=dict(size=14 if inst.labels else 8, color=RED, line=dict(color="white", width=1))))
    if cur is not None:
        fig.add_trace(go.Scatter(x=[xy[cur, 0]], y=[xy[cur, 1]], mode="markers", marker=dict(size=20 if inst.labels else 14, color="rgba(0,0,0,0)", line=dict(color=ORANGE, width=3)), hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 400)


def build_components_map(inst, label, count):
    order = sorted(range(count), key=lambda c: (-sum(1 for x in label if x == c), c))
    sizes = [sum(1 for x in label if x == c) for c in range(count)]
    color_of = {}
    i = 0
    for c in order:
        if c == order[0]:
            color_of[c] = TEAL
        elif sizes[c] == 1:
            color_of[c] = "#9aa3ad"
        else:
            color_of[c] = PALETTE[i % len(PALETTE)]
            i += 1
    colors = [color_of[label[v]] for v in range(inst.n)]
    return build_network(inst, colors)


def build_size_hist(label, count, top=12):
    sizes = sorted((sum(1 for x in label if x == c) for c in range(count)), reverse=True)[:top]
    fig = go.Figure(go.Bar(x=[f"K{i + 1}" for i in range(len(sizes))], y=sizes, marker_color=[TEAL] + [ORANGE] * (len(sizes) - 1), text=sizes, textposition="outside"))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title="Knoten je SCC", fixedrange=True, rangemode="tozero")
    return fig


def build_condensation(cadj, edges, sizes, order=None):
    """Der Kondensations-DAG als eigener kleiner Graph, Kreispunkte in einer Zeile nach der topologischen Reihenfolge angeordnet (falls gegeben), sonst nach Knotennummer."""
    n = len(cadj)
    pos = order if order else list(range(n))
    xy = {v: (float(i), 0.0) for i, v in enumerate(pos)}
    coords = np.array([xy[v] for v in range(n)])
    fig = go.Figure()
    ex, ey = [], []
    for u, v in edges:
        x0, y0 = xy[u]
        x1, y1 = xy[v]
        bend = 0.3 * (1 if (x1 - x0) > 0 else -1) * (abs(x1 - x0) > 1)
        ex += [x0, (x0 + x1) / 2, x1, None]
        ey += [y0, y0 + bend + 0.15, y1, None]
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=GREY, width=1.4, shape="spline"), hoverinfo="skip"))
    if edges:
        import math
        mx, my, ang = [], [], []
        for u, v in edges:
            x0, y0 = xy[u]
            x1, y1 = xy[v]
            mx.append((x0 + x1) / 2)
            my.append((y0 + y1) / 2 + 0.05)
            ang.append((math.degrees(math.atan2(x1 - x0, y1 - y0))) % 360)
        fig.add_trace(go.Scatter(x=mx, y=my, mode="markers", marker=dict(symbol="triangle-up", size=8, color=GREY, angle=ang), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=coords[:, 0], y=coords[:, 1], mode="markers+text", text=[str(sizes[v]) for v in range(n)], textposition="middle center",
                             marker=dict(size=[16 + 3 * min(sizes[v], 10) for v in range(n)], color=TEAL, line=dict(color="white", width=1)),
                             hovertext=[f"SCC {v}: {sizes[v]} Knoten" for v in range(n)], hoverinfo="text"))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, range=[-1, 1])
    return fig


def build_cost(rows):
    ns = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[r["naive"] for r in rows], mode="lines+markers", line=dict(color=RED, width=2.6), name="naiver Test (Vorwärts- und Rückwärtserreichbarkeit)"))
    fig.add_trace(go.Scatter(x=ns, y=[r["kosaraju"] for r in rows], mode="lines+markers", line=dict(color=ORANGE, width=2.4), name="Kosaraju (zwei Tiefensuchen)"))
    fig.add_trace(go.Scatter(x=ns, y=[r["tarjan"] for r in rows], mode="lines+markers", line=dict(color=TEAL, width=2.6), name="Tarjan (eine Tiefensuche)"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.16), plot_bgcolor="white")
    fig.update_xaxes(title="Knotenzahl n", fixedrange=True)
    fig.update_yaxes(title="Elementarschritte", type="log", fixedrange=True)
    return fig


def build_oneway_sweep(rows, nettype, key, title, fmt=".0%"):
    xs = [r["oneway"] for r in rows]
    fig = go.Figure()
    med = [r[(nettype, key)][0] for r in rows]
    lo = [r[(nettype, key)][1] for r in rows]
    hi = [r[(nettype, key)][2] for r in rows]
    fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], fill="toself", fillcolor=TEAL, opacity=0.15, line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=xs, y=med, mode="lines+markers", line=dict(color=TEAL, width=2.6), marker=dict(size=5)))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white", showlegend=False, title=dict(text=title, x=0.01, font=dict(size=13)))
    fig.update_xaxes(title="Einbahn-Anteil", tickformat=".0%", fixedrange=True)
    fig.update_yaxes(tickformat=fmt, fixedrange=True, rangemode="tozero")
    return fig


def build_condensation_sweep(rows):
    xs = [r["oneway"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["nodes"] for r in rows], mode="lines+markers", line=dict(color=TEAL, width=2.6), name="Kondensationsknoten (= SCCs)"))
    fig.add_trace(go.Scatter(x=xs, y=[r["edges"] for r in rows], mode="lines+markers", line=dict(color=ORANGE, width=2.6), name="Kondensationskanten"))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.16), plot_bgcolor="white")
    fig.update_xaxes(title="Einbahn-Anteil", tickformat=".0%", fixedrange=True)
    fig.update_yaxes(fixedrange=True, rangemode="tozero")
    return fig
