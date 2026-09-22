# Preset-Sweep: Stellplatzdisposition auf dem Hof

Alle Zahlen aus `tools/tune_presets.py` mit der **echten Wegkettenrechnung** (`hst_rules.retrieve`,
`hst_constants.leg_distance`) - nicht aus dem Vorab-Check (`hof-planung/vorab_stellplatz/`) übernommen.

## AP 0: Befund der echten Wegkettenrechnung (der wichtigste Sweep dieser Demo)

Der Vorab-Check hatte die Umsetz-Mehrstrecke grob geschätzt: Distanz(alte Reihe) + Distanz(neue
Reihe), so als führe jede Umsetzung über das Tor zurück. Die Reihen liegen aber alle entlang
**desselben Zugangswegs** (wie `yard_constants.py`: Reihe *r* bei 20 + 15·*r* Metern vom Tor) - ein
Hoffahrzeug fährt bei einer Umsetzung **direkt** von der alten in die neue Reihe und zurück, nicht
übers Tor. Diese echte Wegkette ist fast immer kürzer als die grobe Schätzung (bei benachbarten
Reihen z. B. 2×15 = 30 m echte Wegkette gegen 20+35 = 55 m grobe Schätzung).

Reproduktion der sechs Vorab-Check-Bedingungen (300 Instanzen, Kapazität 16 Plätze) mit der echten
Wegkettenrechnung:

| Bedingung | naiv (m) | vorausschauend (m) | Ersparnis vorausschauend | Vorab-Check (grob) |
|---|---|---|---|---|
| H=1, mittel | 101,1 | 101,1 | **0,0 %** (exakt gleich, wie erwartet) | 0,0 % |
| H=2, mittel | 63,3 | 66,6 | **-5,1 %** | +22,8 % |
| H=2, hoch | 65,9 | 66,8 | **-1,5 %** | +17,9 % |
| H=4, mittel | 40,2 | 48,4 | **-20,5 %** | +22,2 % |
| H=4, hoch | 40,9 | 45,5 | **-11,1 %** | +12,1 % |

Ein weiterer, breiter Sweep (R = 2..8, H = 2..4, Auslastung 50-97 %, `tools/tune_presets.py` sinngemäß,
Skript im Session-Protokoll) findet in **keiner** getesteten Bedingung eine positive Ersparnis für
"vorausschauend" - das beste gefundene Ergebnis liegt bei -1,4 % (R=8, H=2, Auslastung ~97 %), das
schlechteste bei -42 % (R=8, H=4, Auslastung ~50 %). **Die im Plan (Abschnitt 1, 7) und im
Vorab-Check berichtete 12-23-%-Ersparnis hält mit der echten Wegkettenrechnung NICHT stand** - siehe
README "Befunde/Korrekturen". Grund: die naive Regel hat zwar weiterhin 2-5× mehr Umsetzungen, aber
jede Umsetzung ist mit der echten (direkten) Wegkette so billig, dass sich der Umweg, den die
vorausschauende Regel bei der Einlagerung in Kauf nimmt (sie meidet nahe Reihen bewusst), nicht mehr
lohnt. Bei H=1 bleibt der Nullbefund unverändert (strukturell exakt, unabhängig vom Distanzmaß).

## sigma-Sweep (`tools/tune_presets.py sigma`, Bedingung "Leicht genestet")

| sigma | Ersparnis vorausschauend |
|---|---|
| 0 % | -4,5 % |
| 25 % | -6,8 % |
| 50 % | -9,2 % |
| 75 % | -11,7 % |
| 100 % | -14,3 % |
| 125 % | -16,2 % |
| 150 % | -17,6 % |

Monoton fallend, **kein Kipppunkt**: die vorausschauende Regel hat schon bei sigma=0 (perfekte
Schätzung) keinen Vorteil, ein Schätzfehler macht sie nur gleichmäßig noch teurer. Der ursprünglich
geplante sechste Preset "Unsicherer Blick voraus" entfällt deshalb (siehe `hst_constants.py`) - es
gibt keinen Kipppunkt zu zeigen. sigma bleibt als Regler (Bereich 0-150 %, Schritt 25, wie geplant),
ohne eigenes Preset.

## Presets: Population (300 Instanzen, Seeds ab 100000) und gezeigte Schicht

`tools/tune_presets.py population` und `tools/tune_presets.py shown` (Ausgabe gekürzt, volle Zahlen
im Sweep-Protokoll der Bau-Session):

| Preset | savings Population | savings gezeigt (Seed 10) | Kriterien |
|---|---|---|---|
| Offene Fläche | 0,0 % | 0,0 % | OK (exakte Gleichheit, Overflow 0,0 %) |
| Leicht genestet | -4,8 % | -8,3 % | OK (Reloc-Faktor inf/4,6×) |
| Stark genestet, ruhig | -21,8 % | -26,2 % | OK (Reloc-Faktor 1,7-2,1×) |
| Stark genestet, viel Verkehr | -11,1 % | -19,4 % | OK (Overflow 9,3-10,2 %) |
| Überlastet | -0,8 % | -0,0 % | OK (Overflow 9,3-10,2 %, |savings| klein) |

**Seed-Wahl:** ein gemeinsamer Seed für alle fünf Presets (Konvention wie `blz_constants.SEED_DEFAULT`).
Bei den zwei hoch ausgelasteten Presets ("Stark genestet, viel Verkehr" und "Überlastet", je
75 Ankünfte, gleiche Kapazität 16) braucht die Overflow-Schwelle (>= 5 % bzw. >= 8 %) einen Seed mit
genug Overflow-Ereignissen in der einen gezeigten Schicht (75 Ankünfte sind eine kleine Stichprobe für
einen ~10-%-Anteil); ein Sweep über 300 Kandidaten-Seeds fand 66, die beide Kriterien zugleich
erfüllen. Seed **10** erfüllt zusätzlich auch die Kriterien der drei übrigen Presets (Sweep über
kleine Kandidatenmenge, siehe `tools/tune_presets.py`) - gewählt statt der schönsten Einzelschicht,
wie in den anderen Hafen-Demos.

## Bestfit-Tie-Break-Absicherung

`tests/test_rules.py::test_lookahead_tiebreak_reversed_candidate_order` baut die Kandidatenliste in
`place_lookahead`/`place_nearest` in umgekehrter Reihenfolge auf und prüft, dass beide Regeln
dasselbe Ergebnis liefern wie mit der Original-Reihenfolge (kein Kandidatenlisten-Artefakt, vgl.
`feedback_bestfit_tiebreak_order_artefact` - dort ein echter 1-3-%-Fund in der Stapelplanung-Demo).
