"""Die Instanz dieser Demo: das Straßennetz eines Distributionsraums als gestörtes Raster (wie in der BFS-und-DFS- und der Brücken-Demo), aber jetzt **gerichtet**: ein Anteil der Straßen wird zur
Einbahnstraße in zufälliger Richtung, der Rest bleibt in beiden Richtungen befahrbar (zwei Bögen). Als zweiter Netztyp gibt es einen gerichteten Zufallsgraphen mit derselben Knoten- und Bogenzahl.

Knoten sind von 0 bis n - 1 durchnummeriert (Zeile für Zeile, Knoten 0 liegt unten links); Bögen sind Tripel (u, v, w) mit u -> v (KEINE u < v-Konvention mehr - die Richtung zählt), sortiert nach (u, v)."""

import random
from dataclasses import dataclass

import numpy as np

import scc_constants as C


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (n, 2)
    arcs: tuple                     # ((u, v, w), ...) sortiert nach (u, v); u -> v
    side: int
    kind: str = "city"
    nettype: str = "grid"
    oneway: float = 0.0
    seed: int = 0
    labels: tuple = ()             # Knotennamen (nur Lehrbuchbeispiel)

    @property
    def n(self):
        return len(self.xy)

    @property
    def m(self):
        return len(self.arcs)


def make_rng(seed, salt):
    """Zufallsquelle mit fester, plattformunabhängiger Zahlenfolge (Python-`random`)."""
    return random.Random(int(seed) * 1_000_003 + int(salt))


def grid_edges(side):
    out = []
    for r in range(side):
        for c in range(side):
            v = r * side + c
            if c + 1 < side:
                out.append((v, v + 1))
            if r + 1 < side:
                out.append((v, v + side))
    return out


def orient(pairs, oneway, rng):
    """Genau `round(oneway * Zahl der Straßen)` der Kandidatenpaare (u, v) mit u < v werden zu Einbahnstraßen (ein einziger Bogen in zufälliger Richtung, zufällig ausgewählt), die übrigen bleiben in
    beiden Richtungen befahrbar (zwei Bögen). Gibt eine sortierte Bogenliste (u, v) zurück (ohne Gewicht)."""
    target = int(round(oneway * len(pairs)))
    order = list(range(len(pairs)))
    rng.shuffle(order)
    oneway_idx = set(order[:target])
    out = []
    for i, (u, v) in enumerate(pairs):
        if i in oneway_idx:
            out.append((u, v) if rng.random() < 0.5 else (v, u))
        else:
            out.append((u, v))
            out.append((v, u))
    return sorted(out)


def random_digraph(n, m, rng):
    """`m` verschiedene gerichtete Bögen zwischen zufälligen verschiedenen Knotenpaaren (u != v, u -> v und v -> u sind verschiedene Bögen)."""
    max_m = n * (n - 1)
    m = min(m, max_m)
    chosen = set()
    while len(chosen) < m:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v:
            continue
        chosen.add((u, v))
    return sorted(chosen)


def generate(side=C.DEFAULT_SIDE, oneway=C.DEFAULT_ONEWAY, nettype="grid", seed=C.DEFAULT_SEED, jitter=C.JITTER):
    if nettype not in C.NETTYPES:
        raise ValueError(f"unbekannter Netztyp {nettype}")
    side = int(side)
    if side < 2:
        raise ValueError("Seitenlänge mindestens 2")
    n = side * side
    rng = make_rng(seed, 4711)
    xy = np.array([[c * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING, r * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING] for r in range(side) for c in range(side)], dtype=float)
    pairs = grid_edges(side)
    arcs_uv = orient(pairs, float(oneway), rng)
    if nettype == "random":
        rng2 = make_rng(seed, 9173)
        arcs_uv = random_digraph(n, len(arcs_uv), rng2)
    arcs = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in arcs_uv)
    return Instance(xy, arcs, side, "city", nettype, float(oneway), int(seed))


# --- Handgebautes Lehrbuchbeispiel: Kreisverkehrsviertel -----------------------------------------------------------------------------------------


TEXTBOOK_LABELS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")


def textbook_instance():
    """Das **Kreisverkehrsviertel**, 10 Kreuzungen A bis J, alle Straßen Einbahnstraßen: drei Ringe A-B-C, D-E-F, G-H-I (je im Kreis befahrbar), zwei Verbindungsstraßen C->D und F->G (nur in dieser
    Richtung: das erste Viertel erreicht das zweite, das zweite das dritte, nie umgekehrt), und eine Sackgasse C->J (J hat keine ausgehende Straße). Von Hand: **4 starke Zusammenhangskomponenten**
    ({A,B,C}, {D,E,F}, {G,H,I}, {J}); der Kondensations-DAG hat von {A,B,C} zwei ausgehende Kanten (zu {D,E,F} und zu {J}) und von {D,E,F} eine zu {G,H,I} - eine gültige, nicht eindeutige
    topologische Reihenfolge ist {A,B,C}, {D,E,F}, {G,H,I}, {J} oder {A,B,C}, {J}, {D,E,F}, {G,H,I}; exakt in `tests/test_algorithm.py` geprüft."""
    xy = np.array([[0, 0], [1, 0.6], [0.4, 1.6], [2.5, 0], [3.5, 0.6], [2.9, 1.6], [5, 0], [6, 0.6], [5.4, 1.6], [1.2, -1.2]], dtype=float)
    arcs_uv = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3), (5, 6), (6, 7), (7, 8), (8, 6), (2, 9)]
    arcs = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in arcs_uv)
    return Instance(xy, arcs, 3, "textbook", "grid", 1.0, 0, TEXTBOOK_LABELS)
