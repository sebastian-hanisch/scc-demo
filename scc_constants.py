"""Regler-Grenzen, feste Annahmen, gemessene Werte und Presets."""

SPACING = 1.0
JITTER = 0.18
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 4, 30, 12
SEED_MAX = 999999
DEFAULT_SEED = 35
KINDS = ("city", "textbook")
KIND_LABELS = {"city": "Betriebsnetz (Karte)", "textbook": "Lehrbuchbeispiel: Kreisverkehrsviertel (10 Knoten)"}
NETTYPES = ("grid", "random")
NETTYPE_LABELS = {"grid": "Raster (Straßennetz)", "random": "Zufallsgraph (gleiche Bogenzahl)"}
ONEWAY_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
DEFAULT_ONEWAY = 0.3
ORDERS = ("fixed", "shuffled")
ORDER_LABELS = {"fixed": "feste Reihenfolge (nach Knotennummer)", "shuffled": "gemischt (nach Seed)"}
STEPS = {1: "1 · Kosaraju gegen Tarjan", 2: "2 · Starke Komponenten", 3: "3 · Kondensation und Reihenfolge", 4: "4 · Aufwand und Einbahn-Sweep"}
SWEEP_SEEDS = tuple(range(100000, 100005))
ONEWAY_SIDE = 20                                            # Seitenlänge der Instanzen im Einbahn-Sweep (400 Knoten)
COST_SIDES = (4, 6, 8, 10, 12, 14)
CONDENSATION_SHARES = (0.1, 0.3, 0.5, 0.7, 0.9)
NAIVE_MAX_N = 250                                           # bis zu dieser Knotenzahl läuft der naive Test auch für die aktuelle Instanz

# --- Gemessene Werte (MEDIAN über 5 feste Instanzen, Seeds 100000-100004; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed und ändern sich nie mit einer
# --- Bibliotheksversion; 2026-09-27, alle Werte über ev.* nachgerechnet, s. tests/test_claims.py) ---
# EINBAHN-ANTEIL (Raster 20 x 20 = 400 Knoten): die größte SCC bleibt bis etwa 20 % Einbahn-Anteil bei 100 % der Knoten (einzelne fehlende Rückwege stören den starken Zusammenhang kaum); erst danach
#   schrumpft sie uneinheitlich: 100/99/97/91/82/46/26 % bei 30/40/50/70/80/90/100 % Einbahn-Anteil (ab etwa 90 % schwankt die Größe stark zwischen den 5 festen Instanzen). Der Zufallsgraph gleicher
#   Bogenzahl verliert seine große SCC gleichmäßiger (96/87/80/57 % bei 0/50/70/100 %) - dort sinkt mit dem Einbahn-Anteil zugleich die Bogenzahl (jede Einbahnstraße ist nur EIN Bogen statt zwei).
# AUFWAND: Kosaraju macht zwei volle Tiefensuchen, Tarjan eine - das Verhältnis ist per Konstruktion IMMER exakt 2, unabhängig von der Instanz (kein gemessener Befund, sondern eine Eigenschaft des
#   Zählmaßes). Der naive Test (Vorwärts- und Rückwärtserreichbarkeit je SCC) kostet bei einer einzigen SCC ebenfalls nur das Doppelte, wächst aber mit der Zahl der SCCs: bei n = 196 vom 2-fachen
#   (0 % Einbahn) über das 18-fache (70 %) auf das 37-fache (90 %) von Tarjan.
# KONDENSATION (Raster 20 x 20): bei 10/30/50/70/90 % Einbahn-Anteil hat die Kondensation 1/2/11/33/111 Knoten und 0/1/12/53/228 Kanten - solange es nur eine SCC gibt, ist die Kondensation ein
#   einzelner Punkt ohne Kante.

PRESETS = {
    "Kreisverkehrsviertel (Lehrbuch)": {"kind": "textbook", "step": 1},
    "Standardfall (Voreinstellung)": {"kind": "city", "side": 12, "oneway": 0.7, "nettype": "grid", "seed": 35, "order": "fixed", "step": 2},
    "Kaum Einbahn (eine große Komponente)": {"kind": "city", "side": 12, "oneway": 0.1, "nettype": "grid", "seed": 35, "order": "fixed", "step": 2},
    "Viel Einbahn (viele kleine SCCs)": {"kind": "city", "side": 12, "oneway": 1.0, "nettype": "grid", "seed": 35, "order": "fixed", "step": 2},
    "Zufallsgraph": {"kind": "city", "side": 12, "oneway": 0.7, "nettype": "random", "seed": 35, "order": "fixed", "step": 2},
    "Kondensation sichtbar": {"kind": "city", "side": 10, "oneway": 0.7, "nettype": "grid", "seed": 35, "order": "fixed", "step": 3},
    "Aufwand: Kosaraju, Tarjan, naiv": {"kind": "city", "side": 14, "oneway": 0.7, "nettype": "grid", "seed": 35, "order": "fixed", "step": 4},
    "Große Instanz (20 × 20)": {"kind": "city", "side": 20, "oneway": 0.6, "nettype": "grid", "seed": 35, "order": "fixed", "step": 2},
}
PRESET_HELP = {
    "Kreisverkehrsviertel (Lehrbuch)": "10 Kreuzungen A bis J, alle Straßen Einbahnstraßen: drei Ringe A-B-C, D-E-F, G-H-I und die Sackgasse J. Von Hand: 4 starke Zusammenhangskomponenten, die Kondensation hat "
                                       "3 Kanten und eine gültige Reihenfolge {A,B,C}, {D,E,F}, {G,H,I}, {J}.",
    "Standardfall (Voreinstellung)": "12 × 12 Kreuzungen, 70 % der Straßen sind Einbahnstraßen (343 Bögen): 11 starke Zusammenhangskomponenten, die größte hat 133 von 144 Knoten (92.4 %), 9 Komponenten sind trivial "
                                     "(ein einzelner Knoten). Kosaraju braucht 974 Elementarschritte, Tarjan 487 - genau die Hälfte.",
    "Kaum Einbahn (eine große Komponente)": "Dasselbe Raster, nur 10 % Einbahnstraßen (502 Bögen): eine einzige starke Zusammenhangskomponente aus allen 144 Knoten. Schon wenige Rückwege genügen, um das ganze "
                                            "Netz stark zusammenhängend zu halten.",
    "Viel Einbahn (viele kleine SCCs)": "Alle Straßen Einbahnstraßen (264 Bögen): 93 starke Zusammenhangskomponenten, 87 davon trivial; die größte hat nur 33 Knoten (22.9 %). Die Kondensation hat fast so viele "
                                        "Knoten wie das Original (93 gegen 144) und 178 Kanten.",
    "Zufallsgraph": "Dieselbe Bogenzahl (343), aber beliebige Paare: 34 starke Zusammenhangskomponenten, die größte 111 Knoten (77.1 %), 33 trivial. Der naive Test kostet hier 13390 Schritte gegen 487 bei Tarjan - "
                    "das 27-Fache.",
    "Kondensation sichtbar": "10 × 10 Kreuzungen, 70 % Einbahnstraßen: 13 Komponenten, die größte 85 % der Knoten - die Kondensation selbst (13 Knoten, 19 Kanten) ist klein genug, um sie als eigenen Graphen zu zeichnen.",
    "Aufwand: Kosaraju, Tarjan, naiv": "14 × 14 Kreuzungen, 70 % Einbahnstraßen (196 Knoten, 19 Komponenten): Kosaraju 1338, Tarjan 669 (Faktor 2, immer), der naive Test 12478 - das 19-Fache von Tarjan.",
    "Große Instanz (20 × 20)": "400 Kreuzungen, 60 % Einbahnstraßen: 19 Komponenten, die größte 377 Knoten (94.2 %); Kosaraju 2928, Tarjan 1464 Elementarschritte.",
}
