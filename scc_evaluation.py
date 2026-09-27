"""Kennzahlen und Sweeps: Aufwand (Kosaraju/Tarjan/naiv), SCC-Größen über den Einbahn-Anteil, Kondensation."""

from dataclasses import dataclass

import numpy as np

import scc_algorithm as A
import scc_constants as C
import scc_scenario as S


@dataclass(frozen=True)
class Settings:
    kind: str = "city"
    side: int = C.DEFAULT_SIDE
    oneway: float = C.DEFAULT_ONEWAY
    nettype: str = "grid"
    seed: int = C.DEFAULT_SEED
    order: str = "fixed"


def build(s):
    if s.kind == "textbook":
        return S.textbook_instance()
    return S.generate(s.side, s.oneway, s.nettype, s.seed)


@dataclass
class Analysis:
    inst: object
    adj: list
    kosaraju: object
    tarjan: object
    naive_steps: int
    n: int
    m: int
    count: int
    largest: int
    trivial: int              # Zahl der SCCs der Größe 1
    trivial_share: float      # Anteil der Knoten in Trivial-SCCs
    largest_share: float
    cond_nodes: int
    cond_edges: int
    topo_kahn: list
    topo_dfs: list
    topo_kahn_steps: int
    topo_dfs_steps: int


def analyse(s, naive=False):
    inst = build(s)
    adj = A.adjacency(inst.n, inst.arcs, s.order, seed=s.seed)
    k = A.kosaraju(adj)
    t = A.tarjan_scc(adj)
    nv = A.naive_scc(adj).steps if naive else 0
    sizes = t.sizes()
    trivial = sum(1 for sz in sizes if sz == 1)
    cadj, edges = A.condensation(adj, t.label, t.count)
    order_k, steps_k = A.topo_sort_kahn(cadj)
    order_d, steps_d = A.topo_sort_dfs(cadj)
    return Analysis(inst, adj, k, t, nv, inst.n, inst.m, t.count, max(sizes) if sizes else 0, trivial, trivial / inst.n if inst.n else 0.0,
                    (max(sizes) if sizes else 0) / inst.n if inst.n else 0.0, len(cadj), len(edges), order_k, order_d, steps_k, steps_d)


def median_over_seeds(func, seeds=C.SWEEP_SEEDS):
    vals = [func(sd) for sd in seeds]
    return float(np.median(vals)), float(np.percentile(vals, 10)), float(np.percentile(vals, 90))


# --- Aufwand: Kosaraju gegen Tarjan gegen naiv ---------------------------------------------------------------------------------------------------


def cost_sweep(base=Settings(), sides=(4, 6, 8, 10, 12), seeds=C.SWEEP_SEEDS):
    rows = []
    for side in sides:
        ks, ts, nv = [], [], []
        for sd in seeds:
            a = analyse(Settings("city", side, base.oneway, base.nettype, sd, base.order), naive=True)
            ks.append(a.kosaraju.steps)
            ts.append(a.tarjan.steps)
            nv.append(a.naive_steps)
        rows.append({"side": side, "n": side * side, "kosaraju": float(np.median(ks)), "tarjan": float(np.median(ts)), "naive": float(np.median(nv)),
                    "ratio_kt": float(np.median([k / tt for k, tt in zip(ks, ts)]))})
    return rows


# --- SCC-Größen über den Einbahn-Anteil ------------------------------------------------------------------------------------------------------------


ONEWAY_SHARES = tuple(round(x * 0.05, 2) for x in range(0, 21))     # 0, 0.05, ..., 1.0


def oneway_sweep(side=20, shares=None, seeds=C.SWEEP_SEEDS):
    """Größte SCC (Anteil der Knoten), Anteil trivialer SCCs (Größe 1) und Zahl der SCCs je Einbahn-Anteil und Netztyp (Median, 10./90. Perzentil)."""
    shares = tuple(shares) if shares is not None else ONEWAY_SHARES
    rows = []
    for sh in shares:
        row = {"oneway": sh}
        for nt in C.NETTYPES:
            for key, fn in (("largest", lambda a: a.largest_share), ("trivial", lambda a: a.trivial_share), ("count", lambda a: a.count)):
                row[(nt, key)] = median_over_seeds(lambda sd, nt=nt, sh=sh, fn=fn: fn(analyse(Settings("city", side, sh, nt, sd))), seeds)
        rows.append(row)
    return rows


def condensation_sweep(side=20, shares=(0.1, 0.3, 0.5, 0.7, 0.9), nettype="grid", seeds=C.SWEEP_SEEDS):
    rows = []
    for sh in shares:
        nodes, edges = [], []
        for sd in seeds:
            a = analyse(Settings("city", side, sh, nettype, sd))
            nodes.append(a.cond_nodes)
            edges.append(a.cond_edges)
        rows.append({"oneway": sh, "nodes": float(np.median(nodes)), "edges": float(np.median(edges))})
    return rows
