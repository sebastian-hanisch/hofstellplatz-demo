# Preset-Sweep: Stellplatzdisposition auf dem Hof

Alle Zahlen aus `tools/tune_presets.py` mit der **echten Wegkettenrechnung** (`hst_rules.retrieve`,
`hst_constants.leg_distance`) - nicht aus dem Vorab-Check (`hof-planung/vorab_stellplatz/`) übernommen.
Die vorausschauende Regel nimmt die **engste Passung** (`hst_rules.place_lookahead`: unter den
verdrängungsfreien Reihen die kleinste vorderste Abholzeit, Best-Fit wie in `stapelplanung-demo`).
Bis 2026-10-05 wählte der Code die größte vorderste Abholzeit (lockerste Passung, Fehlerkatalog FK-126);
alle Zahlen unten sind mit der engsten Passung neu gemessen.

## AP 0: Befund der echten Wegkettenrechnung (der wichtigste Sweep dieser Demo)

Der Vorab-Check hatte die Umsetz-Mehrstrecke grob geschätzt: Distanz(alte Reihe) + Distanz(neue
Reihe), so als führe jede Umsetzung über das Tor zurück. Die Reihen liegen aber alle entlang
**desselben Zugangswegs** (wie `yard_constants.py`: Reihe *r* bei 20 + 15·*r* Metern vom Tor) - ein
Hoffahrzeug fährt bei einer Umsetzung **direkt** von der alten in die neue Reihe und zurück, nicht
übers Tor. Diese echte Wegkette ist fast immer kürzer als die grobe Schätzung (bei benachbarten
Reihen z. B. 2×15 = 30 m echte Wegkette gegen 20+35 = 55 m grobe Schätzung).

Reproduktion der sechs Vorab-Check-Bedingungen (`tools/tune_presets.py conditions`, 300 Instanzen
ab Seed 100000, Kapazität 16 Plätze, σ = 0; „mittel“ = 55, „hoch“ = 75 Ankünfte in 8 h bei 100 min
Standzeit, also Auslastung 72 % bzw. 97 %) mit der echten Wegkettenrechnung:

| Bedingung | naiv (m) | vorausschauend (m) | Ersparnis vorausschauend | Urteil (2 Standardfehler) | Vorab-Check (grob) |
|---|---|---|---|---|---|
| H=1, mittel | 101,1 | 101,1 | **0,0 %** (exakt gleich, wie erwartet) | unklar | 0,0 % |
| H=1, hoch | 105,4 | 105,4 | **0,0 %** (exakt gleich) | unklar | 0,0 % |
| H=2, mittel | 63,6 | 64,1 | **-0,8 %** | unklar | +22,8 % |
| H=2, hoch | 66,0 | 64,7 | **+1,8 %** | besser | +17,9 % |
| H=4, mittel | 40,1 | 47,1 | **-17,4 %** | schlechter | +22,2 % |
| H=4, hoch | 41,0 | 44,6 | **-8,7 %** | schlechter | +12,1 % |

Ersparnis = (naiv − vorausschauend) / naiv; negativ heißt, die vorausschauende Regel liegt darüber.

Breiter Sweep (`tools/tune_presets.py sweep`: R = 2..8, H = 2..4, Auslastung 50-97 %, 126 Zellen
mit je 300 Instanzen, σ = 0): **2 Zellen klar günstiger** (beide R = 8, H = 2: +1,0 % bei Auslastung
90 %, +1,9 % bei 97 %), 8 ohne klaren Unterschied, **116 klar teurer** (schlechteste Zelle -32,2 %
bei R = 4, H = 4, Auslastung 50 %). Je Reihentiefe (je 42 Zellen): H=2 von -8,8 % bis +1,9 % (2 klar
günstiger, 8 unklar, 32 klar teurer), H=3 von -20,8 % bis -1,9 % (alle klar teurer), H=4 von -32,2 %
bis -6,2 % (alle klar teurer). **Die im Plan (Abschnitt 1, 7) und im Vorab-Check berichtete
12-23-%-Ersparnis hält mit der echten Wegkettenrechnung NICHT stand** - siehe README
"Befunde/Korrekturen". Grund: die naive Regel hat zwar weiterhin mehr Umsetzungen (in den Presets
1,4- bis 6,0-fach, im Sweep 1,2- bis 91,7-fach), aber jede Umsetzung ist mit der echten (direkten)
Wegkette so billig, dass sich der Umweg, den die vorausschauende Regel bei der Einlagerung in Kauf
nimmt (sie meidet nahe Reihen bewusst), nur bei H=2 und sehr hoher Auslastung knapp lohnt. Bei H=1
bleibt der Nullbefund unverändert (strukturell exakt, unabhängig vom Distanzmaß).

## sigma-Sweep (`tools/tune_presets.py sigma`, 300 Instanzen)

| sigma | "Leicht genestet" (8×2, Auslastung 72 %) | "Überlastet" (8×2, Auslastung 97 %) |
|---|---|---|
| 0 % | -0,8 % | **+1,8 %** |
| 25 % | -5,6 % | -1,6 % |
| 50 % | -9,0 % | -4,2 % |
| 75 % | -11,5 % | -5,6 % |
| 100 % | -13,8 % | -6,8 % |
| 125 % | -15,2 % | -8,2 % |
| 150 % | -16,4 % | -9,0 % |

Bei "Leicht genestet" monoton fallend, **kein Kipppunkt**: schon bei sigma = 0 (perfekte Schätzung)
gibt es keinen Vorteil. Bei "Überlastet" hat die vorausschauende Regel bei sigma = 0 einen kleinen
Vorteil, der schon bei sigma = 25 % verschwindet - ein Kipppunkt, aber bei einem Vorteil von nur
1,8 %. Der ursprünglich geplante sechste Preset "Unsicherer Blick voraus" entfällt deshalb weiterhin
(siehe `hst_constants.py`); sigma bleibt als Regler (Bereich 0-150 %, Schritt 25, wie geplant),
ohne eigenes Preset.

## Presets: Population (300 Instanzen, Seeds ab 100000) und gezeigte Schicht

`tools/tune_presets.py population` und `tools/tune_presets.py shown`:

| Preset | savings Population | savings gezeigt (Seed 68) | Kriterien |
|---|---|---|---|
| Offene Fläche | 0,0 % | 0,0 % | OK (exakte Gleichheit, Overflow 1,9 % bzw. 3,6 %) |
| Leicht genestet | -0,8 % | -1,7 % | OK (|Unterschied| <= 3 %, Umsetz-Faktor 5,95× bzw. 4,0×) |
| Stark genestet, ruhig | -17,4 % | -14,0 % | OK (Umsetz-Faktor 1,90× bzw. 1,55×) |
| Stark genestet, viel Verkehr | -8,7 % | -6,1 % | OK (Overflow 10,2 % bzw. 8,0 %) |
| Überlastet | +1,8 % | +0,6 % | OK (Overflow 10,2 % bzw. 8,0 %, |savings| klein) |

**Kriterien neu gesetzt (2026-10-05):** mit der engsten Passung ist "Leicht genestet" kein Nachteil
der vorausschauenden Regel mehr, sondern ein Gleichstand (|Unterschied| <= 3 % statt "mindestens
3 % teurer"); die Schwellen der beiden H=4-Presets sinken auf 12 % bzw. 5 % (gemessen -17,4 % bzw.
-8,7 %), "Überlastet" bleibt bei |savings| <= 6 %.

**Seed-Wahl:** ein gemeinsamer Seed für alle fünf Presets (Konvention wie `blz_constants.SEED_DEFAULT`).
Die zwei hoch ausgelasteten Presets brauchen einen Seed mit genug Overflow-Ereignissen in der einen
gezeigten Schicht (75 Ankünfte sind eine kleine Stichprobe für einen ~10-%-Anteil). Von den Seeds
0-299 erfüllen **6** die Kriterien aller fünf Presets zugleich; gewählt ist der mit dem kleinsten
größten Abstand der gezeigten Ersparnis zur Population (Seeds 50 und 68 liegen gleichauf bei 3,3
Prozentpunkten, 68 hat dasselbe Vorzeichen wie die Population beim Preset "Überlastet"), nicht die
schönste Einzelschicht. Der bisherige Seed 10 (für die lockerste Passung gewählt) erfüllt die
Kriterien mit der engsten Passung nicht mehr.

## Bestfit-Tie-Break-Absicherung

`tests/test_rules.py::test_lookahead_tiebreak_reversed_candidate_order` baut die Kandidatenliste in
`place_lookahead`/`place_nearest` in umgekehrter Reihenfolge auf und prüft, dass beide Regeln
dasselbe Ergebnis liefern wie mit der Original-Reihenfolge (kein Kandidatenlisten-Artefakt, vgl.
`feedback_bestfit_tiebreak_order_artefact` - dort ein echter 1-3-%-Fund in der Stapelplanung-Demo).
`tests/test_oracle_hofstellplatz.py::test_place_lookahead_is_tightest_fit_against_brute_force`
prüft die Wahl der engsten Passung gegen eine unabhängige Brute-Force-Wahl über alle Reihen.
