"""Presets: gültige Werte und jede Zahl der Hilfetexte gegen die echten Auswertungsfunktionen."""

import scc_constants as C
import scc_evaluation as ev
from scc_evaluation import Settings
from scc_presets import PRESET_KEYS, SETTING_SPECS


def _settings(name):
    p = C.PRESETS[name]
    return Settings(p["kind"], p.get("side", C.DEFAULT_SIDE), p.get("oneway", 0.0), p.get("nettype", "grid"), p.get("seed", C.DEFAULT_SEED), p.get("order", "fixed"))


def _has(name, *values):
    for v in values:
        assert v in C.PRESET_HELP[name], (name, v)


def test_every_preset_has_valid_values_and_a_help_text():
    assert list(C.PRESETS) == list(C.PRESET_HELP) and len(C.PRESETS) == 8
    for name, p in C.PRESETS.items():
        assert set(p) <= set(PRESET_KEYS) and {"kind", "step"} <= set(p) and p["step"] in C.STEPS
        for key, state_key in PRESET_KEYS.items():
            if key in p and state_key in SETTING_SPECS:
                spec = SETTING_SPECS[state_key]
                assert spec.caster(p[key]) == p[key], (name, key)
                if spec.lo is not None:
                    assert spec.lo <= p[key] <= spec.hi, (name, key)
        assert C.PRESET_HELP[name].strip()


def test_help_textbook_and_standard():
    a = ev.analyse(_settings("Kreisverkehrsviertel (Lehrbuch)"))
    assert (a.n, a.count, a.cond_edges) == (10, 4, 3)
    _has("Kreisverkehrsviertel (Lehrbuch)", "10 Kreuzungen", "4 starke Zusammenhangskomponenten", "3 Kanten")
    a = ev.analyse(_settings("Standardfall (Voreinstellung)"))
    assert (a.n, a.m, a.count, a.largest, a.trivial, a.kosaraju.steps, a.tarjan.steps) == (144, 343, 11, 133, 9, 974, 487)
    _has("Standardfall (Voreinstellung)", "343 Bögen", "11 starke Zusammenhangskomponenten", "133 von 144", "92.4 %", "974", "487")


def test_help_extreme_and_random_presets():
    a = ev.analyse(_settings("Kaum Einbahn (eine große Komponente)"))
    assert (a.m, a.count, a.largest) == (502, 1, 144)
    _has("Kaum Einbahn (eine große Komponente)", "502 Bögen", "einzige starke Zusammenhangskomponente")
    a = ev.analyse(_settings("Viel Einbahn (viele kleine SCCs)"))
    assert (a.m, a.count, a.trivial, a.largest, a.cond_nodes, a.cond_edges) == (264, 93, 87, 33, 93, 178)
    _has("Viel Einbahn (viele kleine SCCs)", "264 Bögen", "93 starke Zusammenhangskomponenten", "87 davon trivial", "33 Knoten (22.9 %)", "178 Kanten")
    a = ev.analyse(_settings("Zufallsgraph"), naive=True)
    assert (a.m, a.count, a.largest, a.trivial, a.naive_steps) == (343, 34, 111, 33, 13390)
    _has("Zufallsgraph", "343", "34 starke Zusammenhangskomponenten", "111 Knoten (77.1 %)", "13390 Schritte gegen 487")


def test_help_condensation_cost_and_large_presets():
    a = ev.analyse(_settings("Kondensation sichtbar"))
    assert (a.count, a.cond_nodes, a.cond_edges) == (13, 13, 19)
    _has("Kondensation sichtbar", "13 Komponenten", "13 Knoten, 19 Kanten")
    a = ev.analyse(_settings("Aufwand: Kosaraju, Tarjan, naiv"), naive=True)
    assert (a.n, a.count, a.kosaraju.steps, a.tarjan.steps, a.naive_steps) == (196, 19, 1338, 669, 12478)
    _has("Aufwand: Kosaraju, Tarjan, naiv", "1338", "669", "12478")
    a = ev.analyse(_settings("Große Instanz (20 × 20)"))
    assert (a.n, a.count, a.largest, a.kosaraju.steps, a.tarjan.steps) == (400, 19, 377, 2928, 1464)
    _has("Große Instanz (20 × 20)", "19 Komponenten", "377 Knoten (94.2 %)", "2928", "1464")
