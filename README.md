# Stellplatzdisposition auf dem Hof – Streamlit-Demo

Interaktive Fall-Demo zur **Stellplatzdisposition im Ankunftsfeld** eines Hofs: Eine Wechselbrücke kommt an – in welche Reihe stellt man sie, wenn die Reihen **genestet** sind (mehrere Brücken
hintereinander, nur von der Gassenseite erreichbar, LIFO) und man die **Abholzeit** vorab kennt? Zusatz zur Yard-Linie (`yard-demo`, das Fahraufträge zwischen Feldern entscheidet, aber Aufträgen bisher
nur einen zufälligen Punkt zur Wegzeitberechnung zuweist – **keine** Kapazitäts- oder Belegungsprüfung je Stellplatz). Analogie zu `stapelplanung-demo` (horizontales Wegfahren statt vertikalem Kranhub).

Teil des Portfolios für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Lokal gebaut bis zum Commit (siehe unten) – **nicht** gepusht, kein GitHub-Repo, nicht deployed.

## Kernfrage

Lohnt sich ein Blick auf die Abholzeit beim Einparken? Zwei Regeln: 🎯 **Nächster freier Platz** (ignoriert die Abholzeit) gegen 🔭 **Vorausschauend** (meidet Reihen, in denen sie später etwas
verdrängen müsste). Ein Vorab-Check (`hof-planung/vorab_stellplatz/`) hatte mit einer **groben Schätzung** der Umsetz-Mehrstrecke 12–23 % Ersparnis für die vorausschauende Regel gezeigt. Diese Demo
rechnet die Umsetz-Mehrstrecke **echt** (Wegkette zwischen den Reihen, kein Umweg übers Tor) nach – siehe **Befunde/Korrekturen** unten.

## Befunde / Korrekturen (ehrlich, gegenüber dem Vorab-Check)

**Die im Vorab-Check gemessene 12–23-%-Ersparnis hält mit der echten Wegkettenrechnung NICHT stand.** Der Vorab-Check hatte die Umsetz-Mehrstrecke grob als Distanz(alte Reihe) + Distanz(neue Reihe)
geschätzt – so, als führe jede Umsetzung übers Tor zurück. Die Reihen liegen aber alle entlang desselben Zugangswegs (wie `yard_constants.py`); ein Hoffahrzeug fährt bei einer Umsetzung **direkt**
zwischen den Reihen. Diese echte Wegkette ist fast immer kürzer, oft deutlich (benachbarte Reihen: 30 m echte Wegkette gegen 55 m grobe Schätzung).

Mit der echten Wegkettenrechnung (`hst_rules.retrieve`, `tools/PRESET_SWEEP.md`) gewinnt die vorausschauende Regel **in keiner** der sechs Vorab-Check-Bedingungen, und auch nicht in einem breiten
Sweep über R = 2..8, H = 2..4, Auslastung 50–97 %:

| Bedingung | naiv (m) | vorausschauend (m) | Ersparnis vorausschauend | Vorab-Check (grob) |
|---|---|---|---|---|
| H=1, mittel | 101,1 | 101,1 | **0,0 %** | 0,0 % |
| H=2, mittel | 63,3 | 66,6 | **−5,1 %** | +22,8 % |
| H=2, hoch | 65,9 | 66,8 | **−1,5 %** | +17,9 % |
| H=4, mittel | 40,2 | 48,4 | **−20,5 %** | +22,2 % |
| H=4, hoch | 40,9 | 45,5 | **−11,1 %** | +12,1 % |

Grund: Die naive Regel hat weiterhin 2–5× mehr Umsetzungen, aber jede einzelne ist mit der echten (direkten) Wegkette so billig, dass sich der Umweg, den die vorausschauende Regel bei der
Einlagerung bewusst nimmt (sie meidet nahe Reihen), nicht mehr auszahlt. Der **H=1-Nullbefund bleibt unverändert** – das ist strukturell (keine Verdrängung möglich), unabhängig von der Distanzrechnung,
und als hart kodierter Regressionstest abgesichert (`tests/test_evaluation.py::test_h1_exact_zero_difference_hardcoded`).

**Weitere Korrekturen gegenüber dem freigegebenen Plan** (Abschnitt 15 "Offene Entscheidungen"):

- **Preset "Unsicherer Blick voraus" entfällt.** Ohne anfänglichen Vorteil (schon bei σ=0 verliert "vorausschauend") gibt es keinen Kipppunkt über den Schätzfehler σ zu zeigen – ein σ-Sweep
  (`tools/PRESET_SWEEP.md`) zeigt einen **monoton fallenden**, nicht kippenden Verlauf. σ bleibt als Regler (0–150 %, Schritt 25), ohne eigenes Preset – damit sind es **5 Presets** (3+2), nicht 6.
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
| Leicht genestet | 8, H=2 | mittel | vorausschauend meidet nahe Reihen und zahlt drauf, trotz 3–5× weniger Umsetzungen |
| Stark genestet, ruhig | 4, H=4 | mittel | größter gemessener Nachteil der vorausschauenden Regel |
| Stark genestet, viel Verkehr | 4, H=4 | hoch | wie oben, Overflow wird spürbar |
| Überlastet | 8, H=2 | hoch | Overflow ist hier der größere Hebel als die Einlagerungsregel |

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
(`test_reference_cross_check_many_small_instances`), ein Sensitivitätscheck mit umgekehrter Kandidatenreihenfolge (`test_lookahead_tiebreak_reversed_candidate_order`), AppTests mit
`clean_cache`-Fixture, sowie `tools/mutation_check.py` (Fehler-Einbau-Test, PYTHONDONTWRITEBYTECODE=1, LF-Normalisierung).
