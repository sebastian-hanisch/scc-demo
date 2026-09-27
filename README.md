# Starke Zusammenhangskomponenten – Einbahnstraßen im Netz – Streamlit-Demo

Drittes Stück der **Graphen-und-Netzwerke-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind der Durchmusterung ([bfs-dfs-demo](https://github.com/sebastian-hanisch/bfs-dfs-demo)). Stück 1 und 2 waren ungerichtet; sobald Straßen nur in eine Richtung befahrbar sind, ist "von X aus erreichbar" nicht mehr symmetrisch zu "erreicht X" – man muss auch zurückkommen. Zwei Kreuzungen sind **stark zusammenhängend**, wenn jede die andere erreicht; die **starken Zusammenhangskomponenten (SCC)** zerlegen das Netz eindeutig. Schrumpft man jede SCC zu einem Punkt, bleibt die **Kondensation** übrig – und die ist **immer kreisfrei**, lässt sich also **topologisch sortieren** (eine gültige Abhängigkeitsreihenfolge). Zwei klassische Verfahren finden die SCCs im Vergleich: **Kosaraju** (zwei Tiefensuchen, einmal auf dem umgedrehten Netz) gegen **Tarjan** (eine einzige Tiefensuche mit Low-Link, wie in der Brücken-Demo). Gemessen wird, was das kostet, wie schnell eine große Komponente beim Einbahn-Anteil zerfällt und wie die Kondensation aussieht.

**Einordnung in die Reihe:** die Reihe hat zwölf Stücke, dies ist das dritte (Details in `graphen-planung/PLAN.md` des Portfolio-Ordners):

```
1 BFS und DFS (Wurzel)                                                        [gebaut: bfs-dfs-demo]
 ├─ 2 Brücken und Artikulationspunkte ─ 4 Euler-Touren                        [gebaut: bridges-demo] [4 nicht gebaut]
 ├─ 3 Starke Zusammenhangskomponenten, topologische Sortierung                [DIESES STÜCK]
 ├─ 5 Graphfärbung                                                            [nicht gebaut]
 ├─ 6 Zentralität ─ 7 Strukturkennzahlen                                      [nicht gebaut]
 │        ├─ 8 Robustheit ─ 9 Kaskaden und Ausbreitung                        [nicht gebaut]
 │        └─ 10 Kritische Knoten härten                                       [nicht gebaut]
 └─ 11 Bandbreite ─ 12 Bandbreite von G(n,k,b) und Cliquenüberdeckung         [nicht gebaut]
```

Ergebnis in Kürze: **Kosaraju kostet per Definition immer genau doppelt so viel wie Tarjan (zwei Tiefensuchen gegen eine); der naive Test (Vorwärts- und Rückwärtserreichbarkeit je Komponente) dagegen wächst mit der Zahl der SCCs – vom 2-fachen bei einer einzigen Komponente auf das 18- bis 37-fache, sobald viele kleine Komponenten entstehen.** Auf einem 20 × 20-Raster übersteht die größte Komponente bis etwa 20 % Einbahn-Anteil praktisch unbeschadet (100/99/97 % der Knoten bei 30/40/50 %), bricht danach unregelmäßig ein (91/82/46/26 % bei 70/80/90/100 %). Ein Zufallsgraph gleicher Bogenzahl verliert seine große Komponente bei mittleren Anteilen schneller als das Raster (80 statt 97 % bei 50 %) – dreht das Bild aber bei vollständiger Einbahnregelung um: dort hält der Zufallsgraph mit 57 % deutlich mehr zusammen als das Raster mit nur 26 %.

## Warum dieses Problem

Sobald ein Netz gerichtet ist – Einbahnstraßen, Leitungen mit Fließrichtung, Abhängigkeiten in einem Bauplan –, reicht "ich komme von A nach B" nicht mehr, um "A und B gehören zusammen" zu begründen. Die starken Zusammenhangskomponenten sind die richtige Verallgemeinerung der (ungerichteten) Komponenten aus Stück 1: sie zerlegen das Netz eindeutig in Teile, innerhalb derer jeder jeden erreicht. Schrumpft man jede Komponente zu einem Punkt, bleibt ein azyklischer Graph – die Kondensation –, der sich topologisch sortieren lässt: eine gültige Abhängigkeitsreihenfolge zwischen den Vierteln. Das ist der Baustein für alles, was auf gerichteten Netzen aufbaut (Multi-Agenten-Koordination, Zeitreihen-Abhängigkeiten, Netzwerkfluss mit Kapazitäten in eine Richtung).

Abgrenzung: die **gerichtete Spannbaum-Demo** (Spannbaum-Reihe) streift Einbahn-Trassen und Kreise nur am Rand, ohne Kondensation oder topologische Sortierung selbst zu zeigen.

## Vorab-Hypothesen (vor der Messung notiert, hier geprüft)

| Hypothese | Ergebnis |
|---|---|
| **H1** Kosaraju und Tarjan finden dieselbe SCC-Partition; Kosaraju kostet immer doppelt so viel wie Tarjan. | ✅ Bestätigt (Satz, im Test gegen networkx auf über 300 Instanzen; das Verhältnis ist exakt 2, eine Eigenschaft des Zählmaßes, kein überraschender Befund). |
| **H2** Bei Einbahn-Anteil 0 zerfällt das Netz in viele triviale (einzelne) SCCs, weil es "eigentlich ungerichtet" ist. | ❌ **Widerlegt – bewusst als Falle geprüft:** jede ungerichtete Straße wird zu *zwei* Bögen (hin und zurück), das erzeugt sofort einen Zyklus zwischen den Endpunkten. Bei Einbahn-Anteil 0 ist die ganze (ungerichtete) Komponente eine **einzige** starke Zusammenhangskomponente, nicht mehrere kleine – das Gegenteil der naiven Erwartung, als Test festgeschrieben (`test_zero_oneway_grid_is_one_scc`). |
| **H3** Die größte SCC zerfällt gleichmäßig mit steigendem Einbahn-Anteil. | ❌ **Widerlegt:** sie bleibt bis etwa 20 % Einbahn-Anteil bei 100 % der Knoten (einzelne fehlende Rückwege stören den starken Zusammenhang kaum), bricht dann uneinheitlich ein: 91/82/46/26 % bei 70/80/90/100 % – ab etwa 90 % schwanken die Werte stark zwischen den fünf festen Instanzen. |
| **H4** Der Zufallsgraph gleicher Bogenzahl verliert seine große SCC bei jedem Einbahn-Anteil schneller als das Raster (im Raster halten viele kurze lokale Kreisläufe Rückwege offen). | ⚠ **Nur teilweise:** bei mittleren Anteilen stimmt es (50 %: 80 gegen 97 %; 70 %: 57 gegen 91 %), aber bei vollständiger Einbahnregelung dreht sich das Bild um – der Zufallsgraph hält mit 57 % deutlich mehr zusammen als das Raster mit nur 26 %. Dort brechen die vielen kurzen Rasterkreisläufe alle gleichzeitig weg, während der Zufallsgraph zufällig verteilte Rückwege behält. |
| **H5** Der naive Test (Vorwärts- und Rückwärtserreichbarkeit je Komponente) ist eine brauchbare Referenz, solange es wenige SCCs gibt, wird aber mit vielen kleinen SCCs schnell teuer. | ✅ Bestätigt: bei einer einzigen SCC kostet er nur das 2-fache von Tarjan (Vorwärts- plus Rückwärtssuche), bei 70 % Einbahn-Anteil das 18-fache, bei 90 % das 37-fache (n = 196). |
| **H6** Die Kondensation bleibt klein, solange es wenige SCCs gibt. | ✅ Bestätigt: bei 10/30/50/70/90 % Einbahn-Anteil hat die Kondensation 1/2/11/33/111 Knoten und 0/1/12/53/228 Kanten (Raster 20 × 20) – solange es nur eine SCC gibt, ist die Kondensation ein einzelner Punkt ohne Kante. |

## Befunde (gemessen, keine Behauptungen)

Median über 5 feste Instanzen (Seeds 100000–100004), Raster mit 20 × 20 Knoten in den Sweeps; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed (die Zahlen ändern sich nie mit einer Bibliotheksversion).

| Frage | Ergebnis |
|---|---|
| **Stimmt das Verfahren?** | ✅ Kosaraju == Tarjan == networkx.strongly_connected_components (SCC-Partition) auf über 300 Instanzen (Raster mit Einbahn-Anteil 0–100 %, Zufallsgraph, n = 1, 2, reiner Kreis, DAG, vollständig gerichteter Graph, Kreisverkehrsviertel); Kondensation immer azyklisch (gegen `is_directed_acyclic_graph`); jede topologische Sortierung (Kahn und DFS-Variante) gültig; ein Zyklus im Kondensationsgraphen wird nie erzeugt |
| **Einbahn-Anteil (Raster 20 × 20)** | größte SCC **100/99/97/91/82/46/26 %** der Knoten bei 30/40/50/70/80/90/100 % Einbahn-Anteil; bis 20 % noch **100 %** |
| **Einbahn-Anteil (Zufallsgraph gleicher Bogenzahl)** | größte SCC **96/87/80/57 %** bei 0/50/70/100 % |
| **Aufwand (n = 196, 70 % Einbahn-Anteil)** | Kosaraju **1338**, Tarjan **669** Elementarschritte (Verhältnis exakt 2); der naive Test **12478** (18-fach von Tarjan) |
| **Aufwand über den Einbahn-Anteil** | naiv/Tarjan-Verhältnis **2 / 18 / 37**-fach bei 0 / 70 / 90 % Einbahn-Anteil (n = 196) |
| **Kondensation (Raster 20 × 20)** | **1/2/11/33/111** Knoten und **0/1/12/53/228** Kanten bei 10/30/50/70/90 % Einbahn-Anteil |

Presets (8), alle mit den Zahlen in ihren Hilfetexten (`tests/test_presets.py`):

| Preset | Was es zeigt |
|---|---|
| Kreisverkehrsviertel (Lehrbuch) | 10 Kreuzungen A bis J, alle Straßen Einbahnstraßen: drei Ringe A-B-C, D-E-F, G-H-I und die Sackgasse J; von Hand 4 starke Zusammenhangskomponenten, die Kondensation hat 3 Kanten und eine gültige Reihenfolge {A,B,C}, {D,E,F}, {G,H,I}, {J} |
| Standardfall (Voreinstellung) | 12 × 12 Kreuzungen, 70 % Einbahnstraßen (343 Bögen): 11 starke Zusammenhangskomponenten, die größte 133 von 144 Knoten (92.4 %), 9 Komponenten trivial; Kosaraju 974, Tarjan 487 Elementarschritte |
| Kaum Einbahn (eine große Komponente) | dasselbe Raster, nur 10 % Einbahnstraßen (502 Bögen): eine einzige starke Zusammenhangskomponente aus allen 144 Knoten |
| Viel Einbahn (viele kleine SCCs) | alle Straßen Einbahnstraßen (264 Bögen): 93 starke Zusammenhangskomponenten, 87 davon trivial; die größte hat nur 33 Knoten (22.9 %); die Kondensation hat 93 Knoten und 178 Kanten |
| Zufallsgraph | dieselbe Bogenzahl (343), aber beliebige Paare: 34 starke Zusammenhangskomponenten, die größte 111 Knoten (77.1 %); der naive Test kostet 13390 Schritte gegen 487 bei Tarjan (27-fach) |
| Kondensation sichtbar | 10 × 10 Kreuzungen, 70 % Einbahnstraßen: 13 Komponenten, die größte 85 % der Knoten; die Kondensation (13 Knoten, 19 Kanten) ist klein genug, um sie als eigenen Graphen zu zeichnen |
| Aufwand: Kosaraju, Tarjan, naiv | 14 × 14 Kreuzungen, 70 % Einbahnstraßen (196 Knoten, 19 Komponenten): Kosaraju 1338, Tarjan 669 (Faktor 2), naiv 12478 (19-fach von Tarjan) |
| Große Instanz (20 × 20) | 400 Kreuzungen, 60 % Einbahnstraßen: 19 Komponenten, die größte 377 Knoten (94.2 %); Kosaraju 2928, Tarjan 1464 Elementarschritte |

## Modell und Verfahren

- **Instanz** (`scc_scenario.py`): gestörtes Raster (Straßennetz, weiterhin frei zerfallend wie in Stück 1) oder Zufallsgraph mit derselben Knoten- und Bogenzahl; jede Straße wird mit Wahrscheinlichkeit gleich dem Einbahn-Anteil zu genau *einer* zufälligen Richtung, sonst bleiben beide Richtungen (zwei Bögen) – der exakte Anteil wird über eine Ziehung ohne Zurücklegen garantiert, nicht über unabhängige Münzwürfe je Straße. Lehrbuchbeispiel *Kreisverkehrsviertel*: drei Ringe (je in sich befahrbar) mit zwei einseitigen Verbindungsstraßen und einer Sackgasse.
- **Kosaraju** (`scc_algorithm.kosaraju`): erste Tiefensuche auf dem Netz sammelt die Abschlusszeiten; zweite Tiefensuche auf dem transponierten (umgedrehten) Netz, gestartet in absteigender Abschlusszeit – jeder Suchbaum dieser zweiten Suche ist genau eine SCC.
- **Tarjan** (`scc_algorithm.tarjan_scc`): eine einzige Tiefensuche mit Entdeckungszeit disc, low-Wert und einem Stapel der noch keiner fertigen SCC zugeordneten Knoten (wie das Low-Link-Verfahren aus der Brücken-Demo, hier für gerichtete Graphen). Ein Knoten u schließt eine SCC ab, wenn low[u] == disc[u]: dann werden vom Stapel bis einschließlich u alle Knoten zu einer neuen SCC.
- **Naiver Test** (`naive_scc`): für jeden noch nicht zugeordneten Knoten Vorwärts- und Rückwärtserreichbarkeit je per Breitensuche, ihr Schnitt ist die SCC – deutlich teurer, sobald es viele SCCs gibt.
- **Kondensation und topologische Sortierung** (`condensation`, `topo_sort_kahn`, `topo_sort_dfs`): jede SCC wird zu einem Punkt geschrumpft, eine Kante bleibt zwischen zwei verschiedenen SCCs, wenn eine Originalstraße sie verbindet – das Ergebnis ist immer ein DAG. Kahns Verfahren (Ein-Grad-Abbau) und die umgekehrte DFS-Abschlussreihenfolge liefern beide eine gültige, aber nicht notwendig identische topologische Sortierung.
- **Elementarschritte:** jeder abgearbeitete Knoten und jeder von einem Ende angesehene Bogen zählt 1. Anders als in den ungerichteten Geschwister-Demos wird ein Bogen u → v nur *einmal* angesehen: eine Tiefensuche über einen gerichteten Graphen zählt also n + m, nicht n + 2m.

## Was die App zeigt

1. **Vier Schritte** (Schritt-Regler): **Kosaraju gegen Tarjan** (Regler über die Ereignisse der gewählten Suche, Wiedergabe auf der Karte) → **Starke Komponenten** (Karte farbig nach SCC, Größenverteilung, auf Abruf: größte SCC über den Einbahn-Anteil für beide Netztypen) → **Kondensation und Reihenfolge** (der geschrumpfte Graph als eigener Plot, Tabelle der topologischen Sortierung) → **Aufwand und Einbahn-Sweep** (Kosaraju gegen Tarjan gegen naiv, auf Abruf über die Größe; Kondensation auf Abruf über den Einbahn-Anteil).
2. Regler: Instanz (Betriebsnetz / Kreisverkehrsviertel), Kreuzungen je Seite (4 bis 30), Einbahn-Anteil der Straßen (0 bis 100 %), Netztyp (Raster / Zufallsgraph), Nachbarreihenfolge (fest / gemischt nach Seed), Zufalls-Seed der Instanz (+🎲); Permalink in der Adresszeile.

## Was nicht funktioniert hat / Grenzen

- **Die q = 0-Falle (H2).** Bei Einbahn-Anteil 0 ist die ganze ungerichtete Komponente eine einzige SCC, nicht mehrere triviale – wer das nicht bedenkt, überschätzt leicht die Zahl der Komponenten bei niedrigem Einbahn-Anteil.
- **H3 und H4 zeigen keinen glatten Verlauf.** Die größte Komponente zerfällt nicht gleichmäßig, sondern hält lange stand und bricht dann unregelmäßig ein; der Vergleich Raster gegen Zufallsgraph kippt bei sehr hohem Einbahn-Anteil um.
- **Nur zwei SCC-Algorithmen.** Keine pfadbasierte Variante (Gabow 2000); die Kondensation wird nur gezeigt, nicht weiter genutzt (kein eigenes Scheduling auf ihr).
- **Einbahn-Modell ist ein Münzwurf je Straße.** Eine echte Verkehrsführung plant Einbahnstraßen gezielt (Durchgangsverkehr, Sackgassen), nicht zufällig verteilt.
- **Elementarschritte statt Laufzeit.** Der Faktor 2 zwischen Kosaraju und Tarjan ist eine Eigenschaft des Zählmaßes (zwei volle Tiefensuchen gegen eine), keine gemessene Erkenntnis; echte Laufzeiten hängen an der Implementierung.
- **Synthetische, gerichtete Netze.** Ein gestörtes Raster und ein Zufallsgraph gleicher Bogenzahl, kein echtes Einbahnstraßensystem.

## Tests

`tests/test_algorithm.py` (16: Kosaraju und Tarjan gegen networkx auf über 300 Instanzen, Kondensation azyklisch, topologische Sortierung gültig, die q=0-Falle als Test festgeschrieben, Buchführung), `tests/test_scenario.py`, `tests/test_evaluation.py`, `tests/test_presets.py` (jede Zahl der Hilfetexte), `tests/test_claims.py` (jede README-Zahl über die echten Auswertungsfunktionen), `tests/test_app.py` (40: AppTest – Voreinstellung, jedes Preset, jeder Schritt für jede Instanz, jeden Netztyp und beide Algorithmen, jede Position des Ereignis-Reglers, Randwerte, Permalink-Grenzen, bedingte Regler, Berechnungen auf Abruf, Footer). 76 Tests insgesamt.

```
python -m pytest tests/ -v
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App |
| `scc_algorithm.py` | Kosaraju, Tarjan, naiver Test, Kondensation, topologische Sortierung |
| `scc_scenario.py` | Raster, Zufallsgraph, Kreisverkehrsviertel |
| `scc_evaluation.py` | Analyse, Sweeps (Aufwand, Einbahn-Anteil, Kondensation) |
| `scc_visualization.py` | Plotly-Figuren (inkl. Pfeilrichtung auf den Bögen) |
| `scc_presets.py`, `scc_constants.py` | Permalink, Presets, gemessene Werte |
| `tests/` | Tests |

## Bewusst nicht umgesetzt

Graphfärbung, Zentralität, Robustheit und Kaskaden, kritische Knoten härten, Bandbreite – eigene Stücke der Reihe.

## Lokal ausführen

```
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\streamlit run app.py
```

## Literatur

- Tarjan, R. E. (1972). *Depth-first search and linear graph algorithms.* SIAM Journal on Computing 1(2), 146–160.
- Sharir, M. (1981). *A strong-connectivity algorithm and its applications in data flow analysis.* Computers & Mathematics with Applications 7(1), 67–72 (Kosarajus Verfahren, unveröffentlicht 1978, wird meist über diese Arbeit zitiert).
- Kahn, A. B. (1962). *Topological sorting of large networks.* Communications of the ACM 5(11), 558–562.

Gebaut mit Streamlit, Plotly, NumPy und pandas.
