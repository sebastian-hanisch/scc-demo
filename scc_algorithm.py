"""Starke Zusammenhangskomponenten (SCC) eines gerichteten Graphen - naiv (Vorwärts- und Rückwärtserreichbarkeit je Knoten schneiden), mit Kosaraju (zwei Tiefensuchen, einmal auf dem transponierten
Graphen) und mit Tarjan (eine Tiefensuche mit Low-Link und einem SCC-Stapel); dazu die Kondensation (jede SCC zu einem Punkt geschrumpft, immer azyklisch) und ihre topologische Sortierung.

**Elementarschritte** (das Aufwandsmaß dieser Reihe, keine Laufzeit): jeder abgearbeitete Knoten und jeder von einem Ende angesehene Bogen zählt 1. Anders als in den ungerichteten Geschwister-Demos wird
ein Bogen u -> v nur EINMAL angesehen (nicht von beiden Enden): eine Tiefensuche über einen gerichteten Graphen zählt also n + m, nicht n + 2m.

Begriffe: Zwei Knoten sind **stark zusammenhängend**, wenn jeder den anderen über gerichtete Bögen erreicht. Eine **starke Zusammenhangskomponente (SCC)** ist eine maximale Menge davon. Schrumpft man jede
SCC zu einem Punkt, entsteht die **Kondensation** - ein Graph, der IMMER azyklisch ist (ein Kreis zwischen zwei Kondensationsknoten würde ihre SCCs zu einer verschmelzen). Eine **topologische Sortierung**
eines azyklischen Graphen ist eine Knotenreihenfolge, in der jeder Bogen von einem früheren zu einem späteren Knoten zeigt."""

import random
from collections import deque
from dataclasses import dataclass, field


def adjacency(n, arcs, order="fixed", seed=0):
    """Adjazenzliste aus gerichteten Bögen (u, v, ...): adj[u] enthält jedes v mit einem Bogen u -> v. "fixed" = aufsteigend, "shuffled" = je Knoten gemischt (Seed fest, Python-`random`)."""
    adj = [[] for _ in range(n)]
    for a in arcs:
        u, v = int(a[0]), int(a[1])
        adj[u].append(v)
    for lst in adj:
        lst.sort()
    if order == "shuffled":
        rng = random.Random(int(seed) * 1_000_003 + 5150)
        for lst in adj:
            rng.shuffle(lst)
    elif order != "fixed":
        raise ValueError(f"unbekannte Reihenfolge {order}")
    return adj


def transpose(n, adj):
    """Der Graph mit jedem Bogen umgedreht: radj[v] enthält u genau dann, wenn adj[u] v enthält."""
    radj = [[] for _ in range(n)]
    for u in range(n):
        for v in adj[u]:
            radj[v].append(u)
    for lst in radj:
        lst.sort()
    return radj


@dataclass
class SCCResult:
    label: list                                  # SCC-Nummer je Knoten (0, 1, ... in Fundreihenfolge)
    count: int
    steps: int
    order: list = field(default_factory=list)     # Kosaraju: Abschlussreihenfolge der ersten Tiefensuche
    events: list = field(default_factory=list)
    method: str = ""

    def sizes(self):
        sizes = [0] * self.count
        for c in self.label:
            sizes[c] += 1
        return sizes


# --- Kosaraju --------------------------------------------------------------------------------------------------------------------------------------


def kosaraju(adj):
    """Erste Tiefensuche auf G sammelt die Abschlussreihenfolge; zweite Tiefensuche auf dem transponierten Graphen, in absteigender Abschlusszeit gestartet, findet je Baum eine SCC."""
    n = len(adj)
    visited = [False] * n
    pos = [0] * n
    finish_order = []
    steps = 0
    events = []
    for s in range(n):
        if visited[s]:
            continue
        visited[s] = True
        steps += 1
        events.append(("discover1", s, None))
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                steps += 1
                if not visited[v]:
                    visited[v] = True
                    steps += 1
                    events.append(("discover1", v, u))
                    stack.append(v)
            else:
                stack.pop()
                finish_order.append(u)
                events.append(("finish1", u))
    radj = transpose(n, adj)
    label = [-1] * n
    pos2 = [0] * n
    count = 0
    for u in reversed(finish_order):
        if label[u] >= 0:
            continue
        label[u] = count
        steps += 1
        events.append(("discover2", u, None, count))
        comp = [u]
        stack = [u]
        while stack:
            x = stack[-1]
            if pos2[x] < len(radj[x]):
                y = radj[x][pos2[x]]
                pos2[x] += 1
                steps += 1
                if label[y] < 0:
                    label[y] = count
                    steps += 1
                    events.append(("discover2", y, x, count))
                    comp.append(y)
                    stack.append(y)
            else:
                stack.pop()
        events.append(("finish2", u, count, comp))
        count += 1
    return SCCResult(label, count, steps, finish_order, events, "kosaraju")


# --- Tarjan ------------------------------------------------------------------------------------------------------------------------------------------


def tarjan_scc(adj):
    """Eine Tiefensuche mit Entdeckungszeit disc, low-Wert und einem Stapel der noch keiner fertigen SCC zugeordneten Knoten. Ein Knoten u schließt eine SCC ab, wenn low[u] == disc[u]: dann werden
    vom Stapel bis einschließlich u alle Knoten zu einer neuen SCC."""
    n = len(adj)
    disc = [0] * n
    low = [0] * n
    on_stack = [False] * n
    scc_stack = []
    label = [-1] * n
    pos = [0] * n
    clock = 0
    count = 0
    steps = 0
    events = []
    for s in range(n):
        if disc[s]:
            continue
        clock += 1
        disc[s] = low[s] = clock
        steps += 1
        on_stack[s] = True
        scc_stack.append(s)
        events.append(("root", s))
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                steps += 1
                if not disc[v]:
                    clock += 1
                    disc[v] = low[v] = clock
                    steps += 1
                    on_stack[v] = True
                    scc_stack.append(v)
                    stack.append(v)
                    events.append(("discover", v, u))
                elif on_stack[v]:
                    if disc[v] < low[u]:
                        low[u] = disc[v]
                    events.append(("back", u, v))
            else:
                stack.pop()
                if stack:
                    p = stack[-1]
                    if low[u] < low[p]:
                        low[p] = low[u]
                comp = None
                if low[u] == disc[u]:
                    comp = []
                    while True:
                        w = scc_stack.pop()
                        on_stack[w] = False
                        label[w] = count
                        comp.append(w)
                        if w == u:
                            break
                    count += 1
                events.append(("finish", u, comp))
    return SCCResult(label, count, steps, [], events, "tarjan")


# --- Naiver Test (Referenz) ----------------------------------------------------------------------------------------------------------------------


def naive_scc(adj):
    """Für jeden noch nicht zugeordneten Knoten: Vorwärts- und Rückwärtserreichbarkeit je per Breitensuche, ihr Schnitt ist die SCC. Deutlich teurer als Kosaraju/Tarjan (je SCC zwei volle Suchen)."""
    n = len(adj)
    radj = transpose(n, adj)
    label = [-1] * n
    count = 0
    steps = 0
    for s in range(n):
        if label[s] >= 0:
            continue
        for direction_adj, seen_name in ((adj, "f"), (radj, "b")):
            seen = [False] * n
            seen[s] = True
            queue = deque([s])
            while queue:
                u = queue.popleft()
                steps += 1
                for v in direction_adj[u]:
                    steps += 1
                    if not seen[v]:
                        seen[v] = True
                        queue.append(v)
            if seen_name == "f":
                seen_f = seen
            else:
                seen_b = seen
        for v in range(n):
            if seen_f[v] and seen_b[v]:
                label[v] = count
        count += 1
    return SCCResult(label, count, steps, [], [], "naive")


# --- Kondensation und topologische Sortierung ---------------------------------------------------------------------------------------------------


def condensation(adj, label, count):
    """Kondensations-Adjazenzliste (Knoten = SCC-Nummern) und die sortierte Kantenliste, ohne Duplikate und ohne Schleifen (Bögen innerhalb derselben SCC)."""
    edge_set = set()
    for u in range(len(adj)):
        for v in adj[u]:
            if label[u] != label[v]:
                edge_set.add((label[u], label[v]))
    edges = sorted(edge_set)
    cadj = [[] for _ in range(count)]
    for a, b in edges:
        cadj[a].append(b)
    return cadj, edges


def topo_sort_kahn(cadj):
    """Ein-Grad-Abbau (Kahn 1962): Warteschlange der Knoten ohne eingehende Kante, entnehmen und die Kanten ihrer Nachfolger abbauen. Gibt (Reihenfolge, Schritte) zurück, oder (None, Schritte) bei
    einem Zyklus (dann bleiben Knoten mit positivem Eingangsgrad übrig)."""
    n = len(cadj)
    indeg = [0] * n
    for u in range(n):
        for v in cadj[u]:
            indeg[v] += 1
    queue = deque(sorted(v for v in range(n) if indeg[v] == 0))
    order = []
    steps = 0            # der Eingangsgrad-Aufbau sieht jede Kante einmal an
    for u in range(n):
        for v in cadj[u]:
            steps += 1
    while queue:
        u = queue.popleft()
        steps += 1
        order.append(u)
        for v in cadj[u]:
            steps += 1
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    if len(order) != n:
        return None, steps
    return order, steps


def topo_sort_dfs(cadj):
    """Tiefensuche, absteigende Abschlusszeit umgekehrt: eine gültige topologische Sortierung. Erkennt einen Zyklus über eine Rückwärtskante zu einem Knoten, der noch auf dem aktuellen Suchpfad liegt
    (Zustand 1), und gibt dann (None, Schritte) zurück."""
    n = len(cadj)
    state = [0] * n           # 0 unbesucht, 1 auf dem Pfad, 2 abgeschlossen
    pos = [0] * n
    order = []
    steps = 0
    for s in range(n):
        if state[s] != 0:
            continue
        state[s] = 1
        steps += 1
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(cadj[u]):
                v = cadj[u][pos[u]]
                pos[u] += 1
                steps += 1
                if state[v] == 0:
                    state[v] = 1
                    steps += 1
                    stack.append(v)
                elif state[v] == 1:
                    return None, steps
            else:
                stack.pop()
                state[u] = 2
                order.append(u)
    order.reverse()
    return order, steps


def is_valid_topo_order(cadj, order):
    """Prüfung: jede Kante zeigt von einer früheren zu einer späteren Position in `order`."""
    if sorted(order) != list(range(len(cadj))):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[u] < pos[v] for u in range(len(cadj)) for v in cadj[u])


def has_cycle(cadj):
    """True, wenn der Graph mindestens einen gerichteten Kreis enthält (über die DFS-Zustände von `topo_sort_dfs`)."""
    return topo_sort_dfs(cadj)[0] is None
