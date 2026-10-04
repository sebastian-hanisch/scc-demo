"""Starke Zusammenhangskomponenten und topologische Sortierung – Einbahnstraßen im Netz - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Graphen-und-Netzwerke-Reihe der "Konzepte"-Reihe. Kind der Durchmusterung (BFS und DFS): sobald Straßen nur in eine Richtung befahrbar sind, ist "erreichbar von X" nicht mehr symmetrisch
zu "erreicht X". Zwei Algorithmen finden die starken Zusammenhangskomponenten (Kosaraju, Tarjan), die Kondensation ist immer azyklisch und lässt sich topologisch sortieren.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import scc_algorithm as A
import scc_constants as C
import scc_evaluation as ev
from scc_evaluation import Settings, analyse
from scc_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    store_from_widget,
    sync_query_params,
)
from scc_visualization import (
    build_components_map,
    build_condensation,
    build_condensation_sweep,
    build_cost,
    build_oneway_sweep,
    build_replay_map,
    build_size_hist,
)

st.set_page_config(page_title="Starke Zusammenhangskomponenten – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings, naive):
    return analyse(settings, naive=naive)


@st.cache_data(show_spinner=False)
def _cost(settings):
    return ev.cost_sweep(settings, C.COST_SIDES)


@st.cache_data(show_spinner=False)
def _oneway():
    return ev.oneway_sweep(C.ONEWAY_SIDE)


@st.cache_data(show_spinner=False)
def _condensation_sweep(nettype):
    return ev.condensation_sweep(C.ONEWAY_SIDE, C.CONDENSATION_SHARES, nettype)


def _german(x):
    return f"{x:,}".replace(",", ".")


st.title("🔁 Starke Zusammenhangskomponenten – Einbahnstraßen im Netz")
st.markdown(
    """
**Drittes Stück der Graphen-und-Netzwerke-Reihe.** Sind Straßen nur in einer Richtung befahrbar, reicht "von X aus erreichbar" nicht mehr - man muss auch zurückkommen. Zwei Kreuzungen sind **stark
zusammenhängend**, wenn jede die andere erreicht; die **starken Zusammenhangskomponenten (SCC)** zerlegen das Netz eindeutig. Schrumpft man jede SCC zu einem Punkt, bleibt die **Kondensation** übrig -
und die ist **immer kreisfrei**, lässt sich also **topologisch sortieren** (eine gültige Abhängigkeitsreihenfolge).

Zwei klassische Verfahren finden die SCCs: **Kosaraju** (zwei Tiefensuchen, einmal auf dem umgedrehten Netz) und **Tarjan** (eine einzige Tiefensuche mit Low-Link, wie in der Brücken-Demo). Gemessen wird,
was das kostet, wie schnell eine große Komponente beim Einbahn-Anteil zerfällt und wie die Kondensation aussieht.
"""
)
st.caption(
    "Kind der BFS-und-DFS-Demo (drittes Stück der Graphen-und-Netzwerke-Reihe); weitere Stücke der Reihe (alle gebaut): Euler-Touren, Graphfärbung, Zentralität, Robustheit, Kaskaden, kritische Knoten härten, Bandbreite. "
    "Die gerichtete Spannbaum-Demo (Spannbaum-Reihe) streift Einbahn-Trassen und Kreise nur am Rand, ohne Kondensation oder topologische Sortierung selbst zu zeigen."
)

with st.expander("So funktionieren Kosaraju und Tarjan", expanded=True):
    st.markdown(
        """
1. **Kosaraju:** erste Tiefensuche auf dem Netz merkt sich, wann jeder Knoten *fertig* ist (Abschlusszeit). Zweite Tiefensuche auf dem **umgedrehten** Netz (jede Straße rückwärts), gestartet in
   absteigender Abschlusszeit: jeder Suchbaum dieser zweiten Suche ist genau eine SCC.
2. **Tarjan:** eine einzige Tiefensuche mit einer Entdeckungszeit disc und einem low-Wert (wie bei Brücken), dazu ein Stapel der noch keiner fertigen SCC zugeordneten Knoten. Ein Knoten u schließt eine
   SCC ab, wenn low[u] == disc[u]: dann werden vom Stapel bis u alle Knoten zu einer neuen SCC.
3. **Kondensation:** jede SCC wird zu einem Punkt geschrumpft; eine Kante bleibt zwischen zwei verschiedenen SCCs, wenn eine Originalstraße sie verbindet. Ein Kreis zwischen zwei Kondensationsknoten
   würde ihre SCCs verschmelzen - die Kondensation ist deshalb **immer kreisfrei**.
4. **Topologische Sortierung:** eine Reihenfolge der Kondensationsknoten, in der jede Kante von früher nach später zeigt (Kahns Ein-Grad-Abbau oder die umgekehrte DFS-Abschlussreihenfolge).
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:5], preset_names[5:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                    help="Das Kreisverkehrsviertel hat 10 Kreuzungen (A bis J) in drei Ringen und einer Sackgasse, von Hand nachvollziehbar; das Betriebsnetz ist ein Raster mit Einbahnstraßen oder ein gerichteter Zufallsgraph.")
    if kind == "city":
        side = st.slider("Kreuzungen je Seite", C.SIDE_MIN, C.SIDE_MAX, value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                         help="Seitenlänge des Rasters; n = Seitenlänge zum Quadrat Knoten (16 bis 900).")
        oneway = st.select_slider("Einbahn-Anteil der Straßen", options=list(C.ONEWAY_OPTIONS), value=float(ss["oneway_select"]), format_func=lambda v: f"{v * 100:.0f} %", key="oneway_widget",
                                  on_change=store_from_widget, args=("oneway_select",),
                                  help="Anteil der Straßen, die zu Einbahnstraßen in zufälliger Richtung werden; der Rest bleibt in beiden Richtungen befahrbar. 0 % = wie in der BFS-und-DFS-Demo (ungerichtet).")
        nettype = st.radio("Netztyp", options=list(C.NETTYPES), format_func=lambda v: C.NETTYPE_LABELS[v], index=list(C.NETTYPES).index(ss["nettype_select"]), key="nettype_widget",
                           on_change=store_from_widget, args=("nettype_select",), help="Raster: Straßen nur zwischen Nachbarn. Zufallsgraph: dieselbe Bogenzahl, aber beliebige Paare.")
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        side, oneway, nettype, seed = C.DEFAULT_SIDE, 1.0, "grid", 0
    order = st.radio("Nachbarreihenfolge", options=list(C.ORDERS), format_func=lambda v: C.ORDER_LABELS[v], key="order_select",
                     help="Ändert die Wiedergabe (Entdeckungsreihenfolge), nie die gefundenen starken Zusammenhangskomponenten.")

sync_query_params({"kind_select": kind, "side_slider": int(side), "oneway_select": float(oneway), "nettype_select": nettype, "order_select": order, "seed_input": int(seed), "scc_step": int(ss["scc_step"])})

settings = Settings(kind, int(side), float(oneway), nettype, int(seed), order)
with st.spinner("Rechne..."):
    a = _analysis(settings, False)
inst, k, t = a.inst, a.kosaraju, a.tarjan
names = (lambda v: inst.labels[v]) if inst.labels else (lambda v: str(v))
naive_ok = inst.n <= C.NAIVE_MAX_N
if naive_ok:
    a_naive = _analysis(settings, True)

st.markdown("## 🎯 Das Netz und seine starken Komponenten")
st.markdown(f"**{a.n} Kreuzungen, {_german(a.m)} Bögen** ({'Raster' if inst.nettype == 'grid' and kind == 'city' else ('Zufallsgraph' if kind == 'city' else 'Kreisverkehrsviertel')}), "
            f"**{a.count} starke Zusammenhangskomponenten**; die größte hat {a.largest} Knoten.")
step = st.select_slider("Schritt", options=list(C.STEPS), key="scc_step", format_func=lambda s: C.STEPS[s])

if step == 1:
    algo = st.radio("Verfahren", options=["kosaraju", "tarjan"], format_func=lambda v: "Kosaraju (zwei Tiefensuchen)" if v == "kosaraju" else "Tarjan (eine Tiefensuche)", horizontal=True, key="algo_select")
    result = k if algo == "kosaraju" else t
    n_events = len(result.events)
    ss["search_k"] = n_events if "search_k" not in ss else min(max(1, int(ss["search_k"])), n_events)
    ev_k = st.slider("Ereignis der Suche", 1, n_events, key="search_k", help="Bei Kosaraju: erst die erste Tiefensuche (teal), dann die zweite auf dem umgedrehten Netz (rot, je fertiger Baum eine SCC). "
                     "Bei Tarjan: eine Suche, fertige SCCs werden farbig markiert, sobald sie vom Stapel genommen werden.")
    st.plotly_chart(build_replay_map(inst, result, ev_k, algo), width="stretch", key=f"s1_map_{algo}_{ev_k}")
    e = result.events[ev_k - 1]
    if algo == "kosaraju":
        if e[0] == "discover1":
            st.markdown(f"**Ereignis {ev_k} von {n_events}** (1. Suche): Knoten {names(e[1])} entdeckt" + (f" von {names(e[2])} aus" if e[2] is not None else "") + ".")
        elif e[0] == "finish1":
            st.markdown(f"**Ereignis {ev_k} von {n_events}** (1. Suche): Knoten {names(e[1])} ist fertig.")
        elif e[0] == "discover2":
            st.markdown(f"**Ereignis {ev_k} von {n_events}** (2. Suche, umgedrehtes Netz, SCC {e[3]}): Knoten {names(e[1])} entdeckt.")
        else:
            st.markdown(f"**Ereignis {ev_k} von {n_events}** (2. Suche): SCC {e[2]} ist mit Knoten {names(e[1])} abgeschlossen.")
    else:
        if e[0] == "root":
            st.markdown(f"**Ereignis {ev_k} von {n_events}:** die Suche beginnt bei Knoten {names(e[1])}.")
        elif e[0] == "discover":
            st.markdown(f"**Ereignis {ev_k} von {n_events}:** von {names(e[2])} aus wird {names(e[1])} entdeckt.")
        elif e[0] == "back":
            st.markdown(f"**Ereignis {ev_k} von {n_events}:** Rückwärtskante von {names(e[1])} zu {names(e[2])} (noch auf dem Stapel).")
        else:
            _, u, comp = e
            if comp:
                st.markdown(f"**Ereignis {ev_k} von {n_events}: low[{names(u)}] == disc[{names(u)}] - eine neue SCC ist fertig:** {{{', '.join(names(x) for x in sorted(comp))}}}.")
            else:
                st.markdown(f"**Ereignis {ev_k} von {n_events}:** Knoten {names(u)} ist abgeschlossen, gehört zur SCC eines Vorfahren.")
elif step == 2:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Komponenten", a.count, delta="starke Zusammenhangskomponenten", delta_color="off")
    c2.metric("Größte SCC", f"{a.largest} / {a.n}", delta=f"{a.largest_share * 100:.1f} %", delta_color="off")
    c3.metric("Triviale SCCs", a.trivial, delta=f"{a.trivial_share * 100:.1f} % der Knoten", delta_color="off")
    c4.metric("Kondensation", f"{a.cond_nodes} / {a.cond_edges}", delta="Knoten / Kanten", delta_color="off")
    cc1, cc2 = st.columns([3, 2])
    with cc1:
        st.plotly_chart(build_components_map(inst, t.label, t.count), width="stretch", key="s2_map")
        st.caption("Jede starke Zusammenhangskomponente hat eine eigene Farbe (größte teal, einzelne Knoten grau); Kosaraju und Tarjan liefern dieselbe Einteilung.")
    with cc2:
        st.plotly_chart(build_size_hist(t.label, t.count), width="stretch", key="s2_hist")
        st.caption("Größen der zwölf größten Komponenten.")
    st.markdown("#### 🔬 Wie schnell zerfällt die große Komponente?")
    if st.button("Über den Einbahn-Anteil berechnen (kann einen Moment dauern)", key="oneway_start"):
        ss["oneway_done"] = True
    if ss.get("oneway_done"):
        with st.spinner("Rechne..."):
            rows_o = _oneway()
        tabs = st.tabs([C.NETTYPE_LABELS[nt] for nt in C.NETTYPES])
        for tab, nt in zip(tabs, C.NETTYPES):
            with tab:
                cA, cB = st.columns(2)
                with cA:
                    st.plotly_chart(build_oneway_sweep(rows_o, nt, "largest", "Größte SCC (Anteil der Knoten)"), width="stretch", key=f"s2_largest_{nt}")
                with cB:
                    st.plotly_chart(build_oneway_sweep(rows_o, nt, "trivial", "Triviale SCCs (Anteil der Knoten)"), width="stretch", key=f"s2_trivial_{nt}")
        st.caption(f"Median über 5 feste Instanzen mit {C.ONEWAY_SIDE} × {C.ONEWAY_SIDE} Knoten, Band = 10. bis 90. Perzentil.")
elif step == 3:
    cadj, edges = A.condensation(a.adj, t.label, t.count)
    order_k, steps_k = A.topo_sort_kahn(cadj)
    order_d, steps_d = A.topo_sort_dfs(cadj)
    d1, d2, d3 = st.columns(3)
    d1.metric("Kondensationsknoten", a.cond_nodes, delta="= Zahl der SCCs", delta_color="off")
    d2.metric("Kondensationskanten", a.cond_edges, delta="zwischen verschiedenen SCCs", delta_color="off")
    d3.metric("Gültige Sortierung", "ja" if order_k else "nein", delta="immer möglich (kreisfrei)", delta_color="off")
    if a.cond_nodes <= 80:
        sizes = t.sizes()
        st.plotly_chart(build_condensation(cadj, edges, sizes, order_k), width="stretch", key="s3_cond")
        st.caption("Jeder Punkt ist eine SCC (Zahl = ihre Größe), in einer gültigen topologischen Reihenfolge angeordnet; Kanten zeigen von links nach rechts.")
    else:
        st.info(f"Mit {a.cond_nodes} Kondensationsknoten wird der Graph unübersichtlich; er wird nur bis 80 Knoten gezeichnet.")
    st.markdown("**Topologische Sortierung (Kahn, Ein-Grad-Abbau)**")
    label_of = {c: [] for c in range(t.count)}
    for v, c in enumerate(t.label):
        label_of[c].append(v)
    rows = [{"Reihenfolge": i + 1, "SCC": c, "Knoten": ", ".join(names(v) for v in sorted(label_of[c])[:6]) + (" ..." if len(label_of[c]) > 6 else "")} for i, c in enumerate(order_k)]
    if a.cond_nodes <= 40:
        st.dataframe(rows, hide_index=True, width="stretch")
    st.caption(f"Kahn braucht {steps_k} Elementarschritte, die DFS-Variante {steps_d}; beide Reihenfolgen sind gültig, aber nicht notwendig gleich.")
elif not naive_ok:
    st.info(f"Der naive Test wird für diese Instanz nicht mitgerechnet (n = {a.n} > {C.NAIVE_MAX_N}).")
else:
    w1, w2, w3, w4 = st.columns(4)
    w1.metric("Kosaraju", _german(k.steps), delta="zwei Tiefensuchen", delta_color="off")
    w2.metric("Tarjan", _german(t.steps), delta="eine Tiefensuche", delta_color="off")
    w3.metric("Verhältnis", f"{k.steps / t.steps:.0f}", delta="Kosaraju / Tarjan (immer 2)", delta_color="off")
    w4.metric("Naiv", _german(a_naive.naive_steps), delta=f"{a_naive.naive_steps / t.steps:.0f}-fach Tarjan", delta_color="off")
    if kind == "city":
        if st.button("Aufwand über die Größe messen (kann einen Moment dauern)", key="cost_start"):
            ss["cost_done"] = ss.get("cost_done", set()) | {(settings.oneway, settings.nettype, settings.order)}
        if (settings.oneway, settings.nettype, settings.order) in ss.get("cost_done", set()):
            with st.spinner("Rechne..."):
                rows_cost = _cost(Settings("city", C.DEFAULT_SIDE, settings.oneway, settings.nettype, 0, settings.order))
            st.plotly_chart(build_cost(rows_cost), width="stretch", key="s4_cost")
            st.caption(f"Median über 5 feste Instanzen je Größe. Kosaraju kostet immer genau das Doppelte von Tarjan (zwei volle Tiefensuchen gegen eine); der naive Test wächst mit der Zahl der "
                       f"Komponenten und kostet beim größten Netz (n = {rows_cost[-1]['n']}) das {rows_cost[-1]['naive'] / rows_cost[-1]['tarjan']:.0f}-Fache von Tarjan.")
        if st.button("Kondensation über den Einbahn-Anteil berechnen", key="cond_start"):
            ss["cond_done"] = ss.get("cond_done", set()) | {settings.nettype}
        if settings.nettype in ss.get("cond_done", set()):
            st.plotly_chart(build_condensation_sweep(_condensation_sweep(settings.nettype)), width="stretch", key="s4_cond_sweep")
            st.caption(f"Median über 5 feste Instanzen mit {C.ONEWAY_SIDE} × {C.ONEWAY_SIDE} Knoten ({C.NETTYPE_LABELS[settings.nettype]}). Solange es nur eine SCC gibt, ist die Kondensation ein einzelner Punkt ohne Kante.")

st.markdown("---")

st.markdown("## 🎯 Was das Netz verrät")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Starke Komponenten", a.count, delta_color="off")
r2.metric("Größte Komponente", f"{a.largest_share * 100:.0f} %", delta="der Knoten", delta_color="off")
r3.metric("Kondensationsknoten", a.cond_nodes, delta_color="off")
r4.metric("Aufwand Tarjan", _german(t.steps), delta="Elementarschritte", delta_color="off")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Kosaraju und Tarjan sind gleich teuer** | Kosaraju braucht genau doppelt so viele Elementarschritte wie Tarjan (zwei Tiefensuchen gegen eine) - das ist eine Eigenschaft des Zählmaßes, kein überraschender Befund. | - |
| **Der naive Test ist eine brauchbare Referenz** | Er wächst mit der Zahl der Komponenten und kostet bei vielen kleinen SCCs ein Vielfaches von Tarjan; für echte Anwendungen ungeeignet, hier nur zur Einordnung. | - |
| **Die Kondensation ist immer klein** | Bei sehr vielen Einbahnstraßen hat sie fast so viele Knoten wie das Original (fast jede Kreuzung ihre eigene SCC) - dann bringt die Kondensation wenig. | - |
| **Einbahnstraßen sind zufällig verteilt** | Hier ein Münzwurf je Straße; eine echte Verkehrsführung plant Einbahnstraßen gezielt (Durchgangsverkehr, Sackgassen). | - |
| **Elementarschritte zeigen den Aufwand** | Sie zählen Knoten- und Bogenbesuche, keine Rechenzeit. | - |
| **Synthetische, gerichtete Netze** | Ein gestörtes Raster und ein Zufallsgraph, keine echten Einbahnstraßensysteme. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Graph.** $G=(V,A)$ gerichtet, $n=|V|$, $m=|A|$. Zwei Knoten $u,v$ sind **stark zusammenhängend**, wenn ein Weg $u\to v$ und ein Weg $v\to u$ existiert; das ist eine Äquivalenzrelation, ihre Klassen sind
die **starken Zusammenhangskomponenten (SCC)**.

**Kosaraju.** Sei $f(v)$ die Abschlusszeit einer Tiefensuche auf $G$. Eine zweite Tiefensuche auf $G^T$ (jede Kante umgedreht), in absteigender Reihenfolge von $f$ gestartet, liefert je Baum genau eine SCC.
Aufwand $O(n+m)$ für beide Suchen zusammen.

**Tarjan.** Mit Entdeckungszeit $\mathrm{disc}(v)$ und $\mathrm{low}(v)=\min$ aus $\mathrm{disc}$ über Rückwärtskanten zu Knoten auf dem aktuellen SCC-Stapel und $\mathrm{low}$ der Kinder: $u$ ist Wurzel
seiner SCC genau dann, wenn $\mathrm{low}(u)=\mathrm{disc}(u)$; die SCC besteht aus allen bis dahin auf dem Stapel liegenden Knoten. Aufwand $O(n+m)$, eine einzige Tiefensuche.

**Kondensation.** $G/\text{SCC}$ hat als Knoten die SCCs, als Kanten die Original-Kanten zwischen verschiedenen SCCs; sie ist immer ein DAG (gerichteter azyklischer Graph).

**Topologische Sortierung.** Eine Reihenfolge $\pi$ der Knoten eines DAG mit $\pi(u)<\pi(v)$ für jede Kante $u\to v$. Kahns Verfahren baut wiederholt Knoten ohne eingehende Kante ab; die umgekehrte
DFS-Abschlussreihenfolge ist ebenfalls gültig.

**Literatur.** Tarjan, R. E. (1972). *Depth-first search and linear graph algorithms.* SIAM Journal on Computing 1(2), 146-160. Sharir, M. (1981). *A strong-connectivity algorithm and its applications in
data flow analysis.* Computers & Mathematics with Applications 7(1), 67-72 (Kosarajus Verfahren, unveröffentlicht 1978, wird meist über diese Arbeit zitiert). Kahn, A. B. (1962). *Topological sorting of
large networks.* Communications of the ACM 5(11), 558-562.

Implementiert in `scc_algorithm.py` (Kosaraju, Tarjan, naiver Test, Kondensation, topologische Sortierung), `scc_scenario.py` (Instanzen), `scc_evaluation.py` (Kennzahlen, Sweeps).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Graphen und Netzwerke: BFS bis Cliquenbandbreite](https://sebastianhanisch.net/konzepte-graphen-netzwerke.html)."
)
