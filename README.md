# Stellplatzdisposition auf dem Hof – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-hofstellplatz-demo.streamlit.app/)**

Interaktive Fall-Demo zur **Stellplatzdisposition im Ankunftsfeld** eines Hofs: Eine Wechselbrücke kommt an – in welche Reihe stellt man sie, wenn die Reihen **genestet** sind (mehrere Brücken
hintereinander, nur von der Gassenseite erreichbar, LIFO) und man die **Abholzeit** vorab kennt? Zusatz zur Yard-Linie (`yard-demo`, das Fahraufträge zwischen Feldern entscheidet, aber Aufträgen bisher
nur einen zufälligen Punkt zur Wegzeitberechnung zuweist – **keine** Kapazitäts- oder Belegungsprüfung je Stellplatz). Analogie zu `stapelplanung-demo` (horizontales Wegfahren statt vertikalem Kranhub).

Teil des Portfolios für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.

## Kernfrage

Lohnt sich ein Blick auf die Abholzeit beim Einparken? Zwei Regeln: 🎯 **Nächster freier Platz** (ignoriert die Abholzeit) gegen 🔭 **Vorausschauend** (meidet Reihen, in denen sie später etwas
verdrängen müsste, und parkt unter den übrigen in der mit der engsten Passung zur Abholzeit). Ein Vorab-Check (`hof-planung/vorab_stellplatz/`) hatte mit einer **groben Schätzung** der Umsetz-Mehrstrecke 12–23 % Ersparnis für die vorausschauende Regel gezeigt. Diese Demo
rechnet die Umsetz-Mehrstrecke **echt** (Wegkette zwischen den Reihen, kein Umweg übers Tor) nach – siehe **Befunde/Korrekturen** unten.

## Befunde / Korrekturen (ehrlich, gegenüber dem Vorab-Check)

**Die im Vorab-Check gemessene 12–23-%-Ersparnis hält mit der echten Wegkettenrechnung NICHT stand.** Der Vorab-Check hatte die Umsetz-Mehrstrecke grob als Distanz(alte Reihe) + Distanz(neue Reihe)
geschätzt – so, als führe jede Umsetzung übers Tor zurück. Die Reihen liegen aber alle entlang desselben Zugangswegs (wie `yard_constants.py`); ein Hoffahrzeug fährt bei einer Umsetzung **direkt**
zwischen den Reihen. Diese echte Wegkette ist fast immer kürzer, oft deutlich (benachbarte Reihen: 30 m echte Wegkette gegen 55 m grobe Schätzung).

Mit der echten Wegkettenrechnung (`hst_rules.retrieve`, `tools/PRESET_SWEEP.md`) und der **engsten Passung** der vorausschauenden Regel (`hst_rules.place_lookahead`: unter den Reihen ohne Verdrängung die mit der kleinsten vordersten Abholzeit, Best-Fit wie in `stapelplanung-demo`) bleibt der Vorteil weitgehend aus: Bei H=1 sind beide Regeln gleich, bei H=2 liegen sie dicht beieinander (nur bei hoher Auslastung ist die vorausschauende Regel knapp vorn), ab H=3 ist sie klar teurer. In einem breiten Sweep über R = 2..8, H = 2..4, Auslastung 50–97 % (126 Bedingungen mit je 300 Instanzen, Schätzfehler σ = 0) ist sie in 2 Bedingungen klar günstiger (beide R = 8, H = 2: +1,0 % bei Auslastung 90 %, +1,9 % bei 97 %), in 8 ohne klaren Unterschied und in 116 klar teurer (klar = Unterschied größer als zwei Standardfehler der gepaarten Differenz). Je Reihentiefe: H=2 zwischen 8,8 % teurer und 1,9 % günstiger, H=3 durchgehend teurer (um 1,9 bis 20,8 %), H=4 durchgehend teurer (um 6,2 bis 32,2 %, der Höchstwert bei R = 4, Auslastung 50 %). Sechs Bedingungen aus dem Vorab-Check:

| Bedingung | naiv (m) | vorausschauend (m) | Ersparnis vorausschauend | Vorab-Check (grob) |
|---|---|---|---|---|
| H=1, mittel | 101,1 | 101,1 | **0,0 %** | 0,0 % |
| H=1, hoch | 105,4 | 105,4 | **0,0 %** | 0,0 % |
| H=2, mittel | 63,6 | 64,1 | **−0,8 %** | +22,8 % |
| H=2, hoch | 66,0 | 64,7 | **+1,8 %** | +17,9 % |
| H=4, mittel | 40,1 | 47,1 | **−17,4 %** | +22,2 % |
| H=4, hoch | 41,0 | 44,6 | **−8,7 %** | +12,1 % |

(300 Instanzen, Kapazität 16 Plätze, σ = 0; „mittel“ = 55, „hoch“ = 75 Ankünfte in 8 h bei 100 min Standzeit, also Auslastung 72 % bzw. 97 %; Ersparnis = (naiv − vorausschauend) / naiv, negativ heißt: die vorausschauende Regel liegt darüber.)

Grund: Die naive Regel hat weiterhin mehr Umsetzungen (in den Presets 1,4- bis 6,0-fach, im Sweep 1,2- bis 91,7-fach), aber jede einzelne ist mit der echten (direkten) Wegkette so billig, dass sich der Umweg, den die vorausschauende Regel bei der Einlagerung bewusst nimmt (sie meidet nahe Reihen), nur bei H=2 und sehr hoher Auslastung knapp auszahlt. Ein Schätzfehler kippt auch diesen Vorteil: Bei R = 8, H = 2, 75 Ankünften (Preset „Überlastet“) fällt die Ersparnis von +1,8 % bei σ = 0 auf −1,6 % bei σ = 25 %. Der **H=1-Nullbefund bleibt unverändert** – das ist strukturell (keine Verdrängung möglich), unabhängig von der Distanzrechnung,
und als hart kodierter Regressionstest abgesichert (`tests/test_evaluation.py::test_h1_exact_zero_difference_hardcoded`).

**Weitere Korrekturen gegenüber dem freigegebenen Plan** (Abschnitt 15 "Offene Entscheidungen"):

- **Preset "Unsicherer Blick voraus" entfällt.** Der einzige Vorteil (R = 8, H = 2, Auslastung 97 %, +1,8 %) ist klein und kippt schon bei σ = 25 %; bei „Leicht genestet“ (8×2, Auslastung 72 %) fällt die Ersparnis monoton von −0,8 % (σ = 0) auf −16,4 % (σ = 150 %). Ein Kipppunkt über den Schätzfehler σ trägt kein eigenes Preset (`tools/PRESET_SWEEP.md`). σ bleibt als Regler (0–150 %, Schritt 25), ohne eigenes Preset – damit sind es **5 Presets** (3+2), nicht 6.
- Die Kapazität der Presets orientiert sich weiterhin an der Vorab-Check-Größenordnung (16 Plätze bei den H=2/H=4-Bedingungen); das Preset "Überlastet" zeigt bewusst hohen Overflow (~10 % der
  Ankünfte) als eigenen Effekt neben der Einlagerungsregel, die übrigen Presets liegen bei ~2 % (realistisch, kein Dauerzustand).

## Modell

*R* Reihen im Ankunftsfeld (Regler 4–16), Reihentiefe *H* ∈ {1, 2, 3, 4} (feste Stufen, `st.radio` – kein freier Slider). Reihe *r* liegt 20 + 15·*r* Meter vom Tor entfernt (Maßstab wie
`yard_constants.py`). Nur der vorderste (gassenseitige) Platz ist ohne Umsetzen erreichbar (LIFO). Ankünfte gleichverteilt über ein Schichtfenster (4–12 h), Standzeit exponentiell (Ø 40–200 min,
rechtsschief). Beim Abholen eines nicht-vordersten Auftrags werden die davorstehenden (später geparkten) Brücken zuerst per **nächster freier Platz** umgesetzt – für beide Einlagerungsregeln
dieselbe Umsetz-Regel, damit der Vergleich nur die Einlagerungsentscheidung misst.

**Echte Wegkettenrechnung** (AP 0 dieses Baus, siehe `hst_rules.py`-Moduldoc): eine Umsetzung fährt direkt von der alten in die neue Reihe (`leg(a,b) = |dist(a) − dist(b)|`) und – weil das
Hoffahrzeug den nächsten Blockierer bzw. anschließend den Zielauftrag an derselben Reihe holen muss – wieder zurück: `2 · Σ leg(r, n_i)` über alle *k* Blockierer. Das ersetzt die grobe Schätzung
`Σ (dist(r) + dist(n_i))` eines Vorab-Checks. Formal im Expander „📐 Mathematische Formulierung“ der App.

**Schätzfehler:** die vorausschauende Regel sieht die Abholzeit nur als Schätzung mit Gauß-Rauschen (Streuung σ % der mittleren Standzeit, eigener Zufallsstrom); die naive Regel ignoriert die
Abholzeit ohnehin.

## Presets

| Preset | R, H | Auslastung | Geschichte |
|---|---|---|---|
| Offene Fläche | 16, H=1 | mittel | Grenzfall: keine Verdrängung, beide Regeln exakt gleich |
| Leicht genestet | 8, H=2 | mittel | praktisch gleichauf (−0,8 %, kein klarer Unterschied), obwohl die vorausschauende Regel rund 6× weniger Umsetzungen hat |
| Stark genestet, ruhig | 4, H=4 | mittel | größter Nachteil der vorausschauenden Regel unter den Presets (−17,4 %) |
| Stark genestet, viel Verkehr | 4, H=4 | hoch | wie oben (−8,7 %), Overflow (10,2 % der Ankünfte) wird spürbar |
| Überlastet | 8, H=2 | hoch | Overflow (10,2 % der Ankünfte) ist der größere Hebel als die Einlagerungsregel; die vorausschauende Regel ist knapp günstiger (+1,8 %), der Vorteil kippt bei σ = 25 % |

Abnahmekriterien und Seed-Wahl: `hst_stories.py`, hergeleitet und geprüft in `tools/tune_presets.py` / `tools/PRESET_SWEEP.md`.

## Grenzen des Modells

Nur eine Reihenrichtung (gassenseitig LIFO), keine Quer-/Diagonalfahrten zwischen Reihen; kein exakter Referenzlöser (Optimum mit Hellsehen) in dieser Version; keine Terminalfahrzeug-Kapazität
oder -Wartezeiten (siehe `yard-demo`); keine Wechselbrücken-Typen oder -Maße; Ankünfte und Abholungen unabhängig voneinander; die Umsetz-Regel ist für beide Verfahren bewusst gleich. Alle Zahlen
sind Größenordnungen aus einer Simulation, keine Messung an einem echten Hof.

## Ausführen

```bash
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements-dev.txt
./venv/Scripts/python.exe -m streamlit run app.py --server.port 8617
```

## Module

`hst_constants.py` (Maßstab, Regler, Presets) · `hst_scenario.py` (Schicht, Schätzfehler) · `hst_rules.py` (Regeln, echte Wegkette) · `hst_simulation.py` (Ablauf, Kennzahlen, Schritt-Log) ·
`hst_evaluation.py` (Stichprobe, H-Kurve, σ-Kurve, Urteil, Meldung) · `hst_visualization.py` (Hofansicht, Kurven, Vergleich) · `hst_ui_panel.py` (Render-Panel) · `hst_pdf_export.py` (PDF) ·
`hst_presets.py` (Regler-Spezifikation, Permalink, Presets) · `hst_stories.py` (Preset-Kriterien) · `app.py` (Skelett) · `tools/tune_presets.py` + `tools/PRESET_SWEEP.md` (Preset-Abstimmung) ·
`tools/mutation_check.py` (Fehler-Einbau-Test).

## Tests

```bash
./venv/Scripts/python.exe -m pytest tests/ -v
```

Unit-Tests je Modul (u. a. `test_h1_exact_zero_difference_hardcoded` als Regressionsschutz für den H=1-Nullbefund), eine von Hand durchgerechnete Wegkette mit echter Umsetzung UND Selbst-Umsetzung
(`test_rules.py::test_hand_example_relocation_chain`), eine unabhängige Nachrechnung von Ablauf und Wegkette gegen `hst_simulation.simulate` über viele kleine Zufallsinstanzen
(`test_reference_cross_check_many_small_instances`), ein Sensitivitätscheck mit umgekehrter Kandidatenreihenfolge (`test_lookahead_tiebreak_reversed_candidate_order`), eine Brute-Force-Prüfung der Einlagerungswahl (engste Passung) über alle Reihen und eine unabhängige Positionsmodell-Simulation
(`test_oracle_hofstellplatz.py`), AppTests mit
`clean_cache`-Fixture, sowie `tools/mutation_check.py` (Fehler-Einbau-Test, PYTHONDONTWRITEBYTECODE=1, LF-Normalisierung).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zum Thema: [Hof- und Yard-Management optimieren](https://sebastianhanisch.net/yard-management-optimierung.html).
