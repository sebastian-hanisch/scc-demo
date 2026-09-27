"""Auswertung: Analyse, Sweeps, Feldbelegung."""

import networkx as nx

import scc_constants as C
import scc_evaluation as ev
from scc_evaluation import Settings


def test_analysis_fields_are_consistent_with_networkx():
    for s in (Settings(), Settings("city", 9, 0.5, "grid", 4), Settings("city", 9, 0.5, "random", 4), Settings("textbook")):
        a = ev.analyse(s, naive=True)
        g = nx.DiGraph()
        g.add_nodes_from(range(a.n))
        g.add_edges_from((u, v) for u, v, _ in a.inst.arcs)
        comps = sorted(nx.strongly_connected_components(g), key=len, reverse=True)
        assert a.count == len(comps) and a.largest == len(comps[0])
        assert a.tarjan.steps == a.n + a.m and a.kosaraju.steps == 2 * (a.n + a.m)
        assert a.naive_steps > 0
        assert a.cond_nodes == a.count
        assert len(a.topo_kahn) == a.count and len(a.topo_dfs) == a.count


def test_naive_is_skipped_by_default():
    a = ev.analyse(Settings("city", 6, 0.3, "grid", 1))
    assert a.naive_steps == 0 and a.tarjan.steps == a.n + a.m


def test_sweeps_have_the_expected_shape_and_monotone_parts():
    rows = ev.oneway_sweep(10, shares=(0.0, 0.5, 1.0))
    assert [r["oneway"] for r in rows] == [0.0, 0.5, 1.0]
    for nt in C.NETTYPES:
        for key in ("largest", "trivial", "count"):
            for r in rows:
                med, lo, hi = r[(nt, key)]
                assert lo <= med <= hi
    assert rows[0][("grid", "largest")][0] >= rows[2][("grid", "largest")][0]           # weniger Einbahn: größere SCC
    cost = ev.cost_sweep(Settings(oneway=0.3), sides=(4, 6), seeds=range(100000, 100003))
    assert all(r["kosaraju"] == 2 * r["tarjan"] for r in cost)
    cond = ev.condensation_sweep(10, (0.3, 0.7), seeds=range(100000, 100003))
    assert all(r["nodes"] >= 1 and r["edges"] >= 0 for r in cond)


def test_median_over_seeds():
    med, lo, hi = ev.median_over_seeds(lambda sd: float(sd - 100000), seeds=range(100000, 100005))
    assert med == 2.0 and abs(lo - 0.4) < 1e-9 and abs(hi - 3.6) < 1e-9
