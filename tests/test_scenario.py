"""Instanzen: Größen, Einbahn-Anteil, Netztypen, Determinismus, Kreisverkehrsviertel."""

import numpy as np
import pytest

import scc_constants as C
import scc_scenario as S


def test_grid_arc_count_matches_oneway_share():
    for side in (2, 5, 12):
        pairs = S.grid_edges(side)
        for oneway in (0.0, 0.3, 0.5, 1.0):
            inst = S.generate(side, oneway, "grid", 7)
            n_oneway = round(oneway * len(pairs))
            assert inst.m == 2 * (len(pairs) - n_oneway) + n_oneway
            keys = {(u, v) for u, v, _ in inst.arcs}
            assert len(keys) == inst.m and list(inst.arcs) == sorted(inst.arcs)


def test_zero_and_full_oneway_are_the_extremes():
    inst0 = S.generate(6, 0.0, "grid", 3)
    pairs = {(min(u, v), max(u, v)) for u, v, _ in inst0.arcs}
    assert len(pairs) == len(S.grid_edges(6)) and inst0.m == 2 * len(pairs)          # jede Straße in beiden Richtungen
    inst1 = S.generate(6, 1.0, "grid", 3)
    assert inst1.m == len(S.grid_edges(6))                                          # jede Straße genau eine Richtung


def test_random_digraph_has_the_requested_arc_count_and_is_simple():
    for oneway in (0.0, 0.4, 0.8):
        g, r = S.generate(9, oneway, "grid", 3), S.generate(9, oneway, "random", 3)
        assert r.m == g.m and r.n == g.n
        keys = {(u, v) for u, v, _ in r.arcs}
        assert len(keys) == r.m and all(u != v for u, v in keys)


def test_determinism_and_platform_independent_stream():
    a, b = S.generate(8, 0.3, "grid", 5), S.generate(8, 0.3, "grid", 5)
    assert a.arcs == b.arcs and np.array_equal(a.xy, b.xy) and S.generate(8, 0.3, "grid", 6).arcs != a.arcs


def test_bridge_city_shape():
    inst = S.textbook_instance()
    assert inst.n == 10 and inst.m == 12 and inst.kind == "textbook" and inst.labels == S.TEXTBOOK_LABELS
    assert {(u, v) for u, v, _ in inst.arcs} == {(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3), (5, 6), (6, 7), (7, 8), (8, 6), (2, 9)}


def test_errors():
    with pytest.raises(ValueError):
        S.generate(4, 0.1, "wheel", 1)
    with pytest.raises(ValueError):
        S.generate(1, 0.1, "grid", 1)
    assert C.SIDE_MIN >= 2
