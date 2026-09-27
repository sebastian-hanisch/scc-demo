"""Jede Zahl aus README und Konstanten-Kommentar, nachgerechnet über die echten Auswertungsfunktionen (Median über 5 feste Instanzen, Seeds 100000-100004)."""

from functools import lru_cache

import scc_constants as C
import scc_evaluation as ev
from scc_evaluation import Settings


@lru_cache(maxsize=None)
def _oneway():
    return {r["oneway"]: r for r in ev.oneway_sweep(C.ONEWAY_SIDE)}


def _pct(rows, nt, key, sh):
    return round(rows[sh][(nt, key)][0] * 100)


def test_oneway_shares_over_the_share():
    rows = _oneway()
    assert [_pct(rows, "grid", "largest", sh) for sh in (0.3, 0.4, 0.5, 0.7, 0.8, 0.9, 1.0)] == [100, 99, 97, 91, 82, 46, 26]
    assert [_pct(rows, "random", "largest", sh) for sh in (0.0, 0.5, 0.7, 1.0)] == [96, 87, 80, 57]


def test_giant_scc_survives_low_oneway_shares_on_the_grid():
    rows = _oneway()
    assert all(rows[sh][("grid", "largest")][0] == 1.0 for sh in (0.0, 0.1, 0.2))
    assert rows[0.3][("grid", "largest")][0] >= 0.99


def test_cost_ratio_kosaraju_tarjan_is_exactly_two():
    for oneway in (0.0, 0.3, 0.6, 1.0):
        rows = ev.cost_sweep(Settings(oneway=oneway), C.COST_SIDES, seeds=range(100000, 100003))
        assert all(r["kosaraju"] == 2 * r["tarjan"] for r in rows)


def test_naive_ratio_grows_with_the_number_of_sccs():
    for oneway, want in ((0.0, 2), (0.7, 18), (0.9, 37)):
        rows = ev.cost_sweep(Settings(oneway=oneway), (14,))
        ratio = round(rows[0]["naive"] / rows[0]["tarjan"])
        assert ratio == want


def test_condensation_over_the_share():
    rows = {r["oneway"]: r for r in ev.condensation_sweep(C.ONEWAY_SIDE, (0.1, 0.3, 0.5, 0.7, 0.9))}
    assert [rows[sh]["nodes"] for sh in (0.1, 0.3, 0.5, 0.7, 0.9)] == [1.0, 2.0, 11.0, 33.0, 111.0]
    assert [rows[sh]["edges"] for sh in (0.1, 0.3, 0.5, 0.7, 0.9)] == [0.0, 1.0, 12.0, 53.0, 228.0]
    assert rows[0.1]["nodes"] == 1.0 and rows[0.1]["edges"] == 0.0


def test_zero_oneway_grid_is_one_scc():
    a = ev.analyse(Settings("city", 20, 0.0, "grid", 100000))
    assert a.count == 1 and a.largest == a.n
