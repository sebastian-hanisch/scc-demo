"""Korrektheits-Kette: SCC gegen networkx (Kosaraju, Tarjan, naiv); Kondensation azyklisch; topologische Sortierung gültig; Sonderfall Einbahn-Anteil 0; Buchführung; Kreisverkehrsviertel von Hand."""

import networkx as nx
import pytest

import scc_algorithm as A
import scc_scenario as S


def _digraph(inst_or_pair):
    if isinstance(inst_or_pair, tuple):
        n, arcs = inst_or_pair
    else:
        n, arcs = inst_or_pair.n, [(u, v) for u, v, _ in inst_or_pair.arcs]
    g = nx.DiGraph()
    g.add_nodes_from(range(n))
    g.add_edges_from(arcs)
    return g


def _instances():
    out = [S.textbook_instance()]
    for side in (2, 3, 5, 8):
        for nettype in S.C.NETTYPES:
            for oneway in (0.0, 0.2, 0.45, 0.5, 0.6, 0.9, 1.0):
                for seed in (1, 2, 3):
                    out.append(S.generate(side, oneway, nettype, seed))
    return out


INSTANCES = _instances()          # 169


def _special():
    return [(1, []), (2, []), (2, [(0, 1)]), (2, [(0, 1), (1, 0)]), (3, [(0, 1), (1, 2), (2, 0)]), (3, [(0, 1), (1, 2)]), (4, [(0, 1), (1, 2), (2, 3)]),
            (5, [(i, j) for i in range(5) for j in range(5) if i != j]), (6, [(0, 1), (1, 0), (2, 3), (3, 2), (1, 2)]), (5, [])]


def _canonical(label):
    groups = {}
    for v, c in enumerate(label):
        groups.setdefault(c, set()).add(v)
    return {frozenset(g) for g in groups.values()}


def _nx_partition(g):
    return {frozenset(c) for c in nx.strongly_connected_components(g)}


# --- 1. SCC == networkx; Kosaraju == Tarjan == naiv --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("order", ["fixed", "shuffled"])
def test_scc_matches_networkx_for_every_algorithm_and_instance(order):
    assert len(INSTANCES) == 169
    for inst in INSTANCES:
        g = _digraph(inst)
        want = _nx_partition(g)
        adj = A.adjacency(inst.n, inst.arcs, order, seed=inst.seed)
        for algo in (A.kosaraju, A.tarjan_scc):
            r = algo(adj)
            assert _canonical(r.label) == want, (inst.kind, inst.nettype, inst.oneway, inst.seed, algo.__name__)
            assert sorted(r.sizes()) == sorted(len(c) for c in want) and r.count == len(want)


def test_naive_matches_networkx_on_small_instances():
    for inst in [i for i in INSTANCES if i.n <= 25][::2]:
        adj = A.adjacency(inst.n, inst.arcs)
        want = _nx_partition(_digraph(inst))
        assert _canonical(A.naive_scc(adj).label) == want


def test_special_cases_match_networkx():
    for n, arcs in _special():
        g = _digraph((n, arcs))
        want = _nx_partition(g)
        adj = A.adjacency(n, [(u, v, 1.0) for u, v in arcs])
        for algo in (A.kosaraju, A.tarjan_scc, A.naive_scc):
            assert _canonical(algo(adj).label) == want


def test_result_sets_do_not_depend_on_the_neighbour_order():
    for inst in INSTANCES[::5]:
        a = A.tarjan_scc(A.adjacency(inst.n, inst.arcs, "fixed"))
        b = A.tarjan_scc(A.adjacency(inst.n, inst.arcs, "shuffled", seed=7))
        assert _canonical(a.label) == _canonical(b.label)
        k = A.kosaraju(A.adjacency(inst.n, inst.arcs, "shuffled", seed=3))
        assert _canonical(k.label) == _canonical(a.label)


# --- 2. Kondensation ist azyklisch ---------------------------------------------------------------------------------------------------------------


def test_condensation_is_acyclic_and_covers_every_arc():
    for inst in INSTANCES:
        adj = A.adjacency(inst.n, inst.arcs)
        r = A.tarjan_scc(adj)
        cadj, edges = A.condensation(adj, r.label, r.count)
        g = nx.DiGraph()
        g.add_nodes_from(range(r.count))
        g.add_edges_from(edges)
        assert nx.is_directed_acyclic_graph(g)
        assert not A.has_cycle(cadj)
        # jeder Originalbogen zwischen verschiedenen SCCs ist eine Kondensationskante, keine Schleifen
        want_edges = {(r.label[u], r.label[v]) for u, v, _ in inst.arcs if r.label[u] != r.label[v]}
        assert set(edges) == want_edges
        assert g.number_of_nodes() == r.count


def test_condensation_edge_count_is_bounded():
    inst = S.generate(8, 0.5, "grid", 5)
    adj = A.adjacency(inst.n, inst.arcs)
    r = A.tarjan_scc(adj)
    _, edges = A.condensation(adj, r.label, r.count)
    assert len(edges) <= r.count * (r.count - 1)


# --- 3. Topologische Sortierung -------------------------------------------------------------------------------------------------------------------


def test_topo_sort_is_valid_on_every_condensation():
    for inst in INSTANCES[::2]:
        adj = A.adjacency(inst.n, inst.arcs)
        r = A.tarjan_scc(adj)
        cadj, _ = A.condensation(adj, r.label, r.count)
        order_k, _ = A.topo_sort_kahn(cadj)
        order_d, _ = A.topo_sort_dfs(cadj)
        assert order_k is not None and order_d is not None
        assert A.is_valid_topo_order(cadj, order_k) and A.is_valid_topo_order(cadj, order_d)


def test_topo_sort_detects_a_cycle_and_never_returns_an_invalid_order():
    cyclic = [[1], [2], [0]]
    assert A.topo_sort_kahn(cyclic)[0] is None and A.topo_sort_dfs(cyclic)[0] is None and A.has_cycle(cyclic)
    dag = [[1, 2], [3], [3], []]
    ok, _ = A.topo_sort_kahn(dag)
    assert ok is not None and A.is_valid_topo_order(dag, ok) and not A.has_cycle(dag)


def test_is_valid_topo_order_rejects_bad_orders():
    dag = [[1], [2], []]
    assert A.is_valid_topo_order(dag, [0, 1, 2])
    assert not A.is_valid_topo_order(dag, [1, 0, 2])
    assert not A.is_valid_topo_order(dag, [0, 1])


# --- 4. Sonderfall Einbahn-Anteil 0: eine SCC pro ungerichteter Komponente (nicht lauter Trivial-SCCs) ----------------------------------------------


def test_oneway_zero_makes_the_whole_undirected_component_one_scc():
    for side in (4, 6, 9):
        inst = S.generate(side, 0.0, "grid", 3)
        adj = A.adjacency(inst.n, inst.arcs)
        r = A.tarjan_scc(adj)
        assert r.count == 1 and r.sizes() == [inst.n]           # jede ungerichtete Kante ist hier ein Bogenpaar hin und zurück: ein Kreis der Länge 2 -> starker Zusammenhang
    inst = S.generate(4, 0.0, "random", 3)
    r = A.tarjan_scc(A.adjacency(inst.n, inst.arcs))
    g = _digraph(inst)
    assert _canonical(r.label) == _nx_partition(g)


def test_oneway_one_can_create_trivial_sccs():
    inst = S.generate(6, 1.0, "grid", 3)
    r = A.tarjan_scc(A.adjacency(inst.n, inst.arcs))
    assert r.count > 1                                          # mit lauter Einbahnstraßen entstehen (meistens) mehrere, oft triviale SCCs


# --- 5. Buchführung ------------------------------------------------------------------------------------------------------------------------------


def test_step_counts_are_n_plus_m_per_pass():
    for inst in INSTANCES[::5]:
        adj = A.adjacency(inst.n, inst.arcs, "shuffled", seed=3)
        r = A.tarjan_scc(adj)
        assert r.steps == inst.n + inst.m
        rk = A.kosaraju(adj)
        assert rk.steps == 2 * (inst.n + inst.m)


def test_kosaraju_finish_order_has_every_node_once():
    inst = S.generate(7, 0.4, "grid", 2)
    r = A.kosaraju(A.adjacency(inst.n, inst.arcs))
    assert sorted(r.order) == list(range(inst.n))


def test_determinism_and_invalid_order_raises():
    inst = S.generate(6, 0.3, "grid", 4)
    a = A.adjacency(inst.n, inst.arcs, "shuffled", seed=5)
    b = A.adjacency(inst.n, inst.arcs, "shuffled", seed=5)
    assert a == b
    with pytest.raises(ValueError):
        A.adjacency(3, [], "sorted")


def test_bridge_city_by_hand():
    inst = S.textbook_instance()
    adj = A.adjacency(inst.n, inst.arcs)
    r = A.tarjan_scc(adj)
    assert inst.n == 10 and inst.m == 12 and r.count == 4
    L = S.TEXTBOOK_LABELS
    groups = _canonical(r.label)
    assert groups == {frozenset(L.index(x) for x in ("A", "B", "C")), frozenset(L.index(x) for x in ("D", "E", "F")), frozenset(L.index(x) for x in ("G", "H", "I")), frozenset([L.index("J")])}
    cadj, edges = A.condensation(adj, r.label, r.count)
    assert len(edges) == 3        # ABC->DEF, ABC->J, DEF->GHI
    order, _ = A.topo_sort_kahn(cadj)
    assert A.is_valid_topo_order(cadj, order)
    pos = {v: i for i, v in enumerate(order)}
    assert pos[r.label[L.index("A")]] < pos[r.label[L.index("D")]] < pos[r.label[L.index("G")]]
    assert pos[r.label[L.index("A")]] < pos[r.label[L.index("J")]]
