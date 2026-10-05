"""Unabhängiges Orakel für die SCC-Kerne: Erreichbarkeit per Floyd-Warshall-Abschluss (ganz anderer Rechenweg als Kosaraju/Tarjan/naive Breitensuche), Kondensation gegen networkx,
Aufwandszähler gegen eine geschlossene Formel (Zahl der Knoten und Bögen in Vorwärts-/Rückwärtserreichbarkeit)."""

import random

import networkx as nx
import numpy as np

import scc_algorithm as A
import scc_evaluation as ev
import scc_scenario as S


def _closure(n, arcs):
    r = np.eye(n, dtype=bool)
    for u, v in arcs:
        r[u, v] = True
    for k in range(n):
        r |= np.outer(r[:, k], r[k, :])
    return r


def _partition(r):
    return {frozenset(np.nonzero(r[i] & r[:, i])[0].tolist()) for i in range(len(r))}


def _canon(label):
    groups = {}
    for v, c in enumerate(label):
        groups.setdefault(c, set()).add(v)
    return {frozenset(g) for g in groups.values()}


def _naive_steps(n, arcs, r):
    outdeg, indeg = [0] * n, [0] * n
    for u, v in arcs:
        outdeg[u] += 1
        indeg[v] += 1
    done = np.zeros(n, bool)
    steps = 0
    for s in range(n):
        if done[s]:
            continue
        f, b = np.nonzero(r[s])[0], np.nonzero(r[:, s])[0]
        steps += len(f) + sum(outdeg[x] for x in f) + len(b) + sum(indeg[x] for x in b)
        done[r[s] & r[:, s]] = True
    return steps


def _cases():
    rng = random.Random(11)
    out = []
    for _ in range(120):
        n = rng.randint(1, 12)
        p = rng.choice([0, 0.08, 0.15, 0.3, 0.7, 1.0])
        out.append((n, [(u, v) for u in range(n) for v in range(n) if u != v and rng.random() < p]))
    for side in (2, 3, 4):
        for nt in ("grid", "random"):
            for ow in (0.0, 0.3, 0.6, 1.0):
                for sd in (1, 2):
                    inst = S.generate(side, ow, nt, sd)
                    out.append((inst.n, [(u, v) for u, v, _ in inst.arcs]))
    return out


def test_scc_condensation_and_step_counts_against_independent_oracle():
    for n, arcs in _cases():
        r = _closure(n, arcs)
        want = _partition(r)
        g = nx.DiGraph()
        g.add_nodes_from(range(n))
        g.add_edges_from(arcs)
        cond = nx.condensation(g)
        for order in ("fixed", "shuffled"):
            adj = A.adjacency(n, [(u, v, 1.0) for u, v in arcs], order, seed=3)
            k, t, nv = A.kosaraju(adj), A.tarjan_scc(adj), A.naive_scc(adj)
            for res in (k, t, nv):
                assert _canon(res.label) == want and res.count == len(want)
            assert t.steps == n + len(arcs) and k.steps == 2 * (n + len(arcs))
            assert nv.steps == _naive_steps(n, arcs, r)
            cadj, edges = A.condensation(adj, t.label, t.count)
            assert len(edges) == cond.number_of_edges() and t.count == cond.number_of_nodes()
            ok, steps_k = A.topo_sort_kahn(cadj)
            od, steps_d = A.topo_sort_dfs(cadj)
            assert A.is_valid_topo_order(cadj, ok) and A.is_valid_topo_order(cadj, od)
            assert steps_k == 2 * len(edges) + t.count and steps_d == t.count + len(edges)


def test_analysis_fields_against_networkx():
    for side, ow, nt, sd in ((3, 0.5, "grid", 1), (5, 0.8, "random", 2), (4, 1.0, "grid", 3), (6, 0.2, "grid", 4)):
        a = ev.analyse(ev.Settings("city", side, ow, nt, sd))
        pairs = 2 * side * (side - 1)
        assert a.m == 2 * pairs - int(round(ow * pairs))
        g = nx.DiGraph()
        g.add_nodes_from(range(a.n))
        g.add_edges_from((u, v) for u, v, _ in a.inst.arcs)
        comps = list(nx.strongly_connected_components(g))
        c = nx.condensation(g)
        assert a.count == len(comps) and a.largest == max(map(len, comps)) and a.trivial == sum(1 for x in comps if len(x) == 1)
        assert a.cond_nodes == c.number_of_nodes() and a.cond_edges == c.number_of_edges()
