# Ausbau der AutoShorts-Engine (Anleitung für die nächtliche Ausbau-Sitzung)

Die Engine zeichnet alle Videos selbst (`engine/toon/`). Was einem Video gefehlt hat, steht in `docs/data/wishes.json`
(`{"wort": {"n": Anzahl, "last": "Videotitel", "done": true|fehlt}}`). Vorläufige, automatisch von der Text-KI gezeichnete
Gegenstände stehen in `docs/data/shapes.json` mit `"auto": true`.

## Zuerst: was das nächste Video braucht
`docs/data/plans.json` enthält die vorbereiteten Videos der nächsten Termine (`{"2026-11-11 18:00": {"topic", "title", "script", "needs": [...]}}`).
Alles in `needs` MUSS vor dem Termin gebaut sein – sonst wird das Video nicht hochgeladen. Diese Wörter haben Vorrang vor der
übrigen Wunschliste. Lies dazu das Drehbuch im Plan (`script.scenes[].text`), damit das Gebaute zu den Sätzen passt, und sorge
dafür, dass es auch erscheint: Bibliotheks-Gegenstände erscheinen automatisch, wenn ihr Name oder ein Alias im Satz vorkommt;
für Code-Requisiten einen Eintrag in `TEXT_PROPS` (engine/toon/stage.py) ergänzen. Prüfe am Ende mit
`python3 -c "from engine import main; print([w for w in NEEDS if not main.known_thing(w)])"`, dass nichts mehr fehlt.

## Stil seit dem Umbau vom 11.11.2026 (bitte einhalten)
- Figuren (`rig.py`): großer Kopf mit Frisur, Augenbrauen, Wangenrot; Kapuzenpulli mit Schattenkante, Jeans, Turnschuhe. Jede Farbfläche
  hat eine dunklere Schattenseite (`_dark`) – neue Kleidung/Kopfbedeckungen genauso zeichnen.
- Frauenfiguren (`rig.py`): Frisuren long, bob (fließend mit runden Spitzen und Strähnen am Gesicht), ponytail, curly, bun; `fem`
  (automatisch bei diesen Frisuren oder `gender: "w"`) gibt Wimpern, feinere Brauen, Lippenfarbe und einen eigenen Seitenscheitel-Pony.
  `stage.balance_cast`: „du“ ist in jedem zweiten Video eine Frau (benannte Figuren und „ich“ bleiben); GROUP_LOOKS sind gemischt.
- Hintergründe (`places.py`): weiche Bausteine `grad` (Verlauf), `veil`/`fade` (Licht, Schatten, Dunst), `blobs` (Kronen/Büsche als eine
  Form mit Licht und Schatten), `cloud`, `window(…, curtain=…)`, `rug`, `books`, `floor_lamp`, `plant`. Jeder Ort endet mit `p.vignette()`
  – das legt Fensterlicht, Dunst, leichte Weichzeichnung und Körnung darüber. Kein kahler Raum: mindestens Fenster oder Bild, ein Möbel,
  eine Pflanze oder ein Teppich.
- Bewegung (`stage.py`): Kamera (`_camera`) mit Ruck beim Schnitt und Sprung auf das Schlüsselwort (`highlight`), Dinge springen ins Bild,
  Figuren federn. Neue Requisiten brauchen dafür nichts Besonderes.
- Requisiten (`extras.py`): Grundformen `_o` (Ellipse) und `_r` (abgerundetes Rechteck) zeichnen automatisch Umriss, Schattenseite unten
  rechts und Glanz; für freie Flächen `_poly`, für Kronen/Wolken/Büsche `_blobs`. Neue Requisiten mit diesen Bausteinen zeichnen, nicht mit
  nackten `d.ellipse`/`d.polygon`-Flächen.
- Tiere/Wesen (`extras.creature`): nach rechts blickend in Wesen-Koordinaten zeichnen (Helfer `ell`, `rr`, `poly`, `stroke`, `eye`, `brow`,
  `cheek`, `mouthf`), gespiegelt wird automatisch. Augen wie bei den Figuren (`rig._eye`), Wangenrot, Kopf immer mit Hals/Körper verbunden.
- Bildgestaltung wie in den Vorbild-Shorts: Halbnahe statt Totale (`_camera` mit `tight`, Zoom passt sich an die Breite von
  Gruppe und Requisiten an, nichts wird angeschnitten); Licht (`stage._light`): bei unheimlich/angespannt/traurig und nachts drinnen
  Halbdunkel mit Lichtkegel auf den Figuren, nachts draußen dunkelblau mit warmen Fenstern und Lichtfleck um die Figuren, sonst läuft der
  Boden unten weich ins Dunkle. Großaufnahme (`shot: close`, automatisch bei starkem Gefühl): Figur 2,6-fach groß und scharf vor
  unscharfer Kulisse. Beschriftungs-Schild `{"type": "tag", "text": "AUGUST 1914"}`; Datum/Jahr/Anlass im Satz setzt es automatisch.
- Bild passt zum Satz (Vorrang vor allem anderen): Nennt der Satz einen Ort („in deinen Garten“, „im Keller“, „im Kino“), gilt er
  (`stage._said_place`) – auch gegen das Drehbuch. Ergibt der Titel einen Schauplatz (Hollywood → `cinema`), spielen ortlose
  Wohnzimmer-Szenen dort (`TOPIC_PLACES`). Das Ding des Themas steht auch drinnen jede zweite Szene und immer, wenn der Satz es nennt.
  Kleines (Spinne, Chip, Schuh) wird nie kleiner als `MIN_PROP_PX` gezeichnet. Ohne Einblendung im Drehbuch erklärt
  `stage._auto_explain` den Satz selbst: Aufzählung → Liste/„SPEISEKARTE“, Temperatur → `thermo`, Prozent mit Bezug → `bar`,
  Signalwort → `stamp` (Liste `STAMPS`, verneinte Wörter zählen nicht). Experten-Aussage („Forscher warnen, dass …“) →
  `quote` (nur die Rolle, nie ein Name). `_time_weather`: „nachts“, „um Mitternacht“ → Nacht; Regen, Schnee, Sturm, Wind, Hitze → Wetter
  (nur draußen, verneint zählt nicht). Nennt der Titel ein Tier/Wesen aus `TOPIC_CREATURES`
  (Spinne, Katze, Hund, Biene, Hai, Roboter …), ist es die Hauptfigur: groß (`HERO_SIZE`), mit Gefühl, in fast jeder Szene (`_topic_creature`).
  Abstrakte Begriffe als Figur: `agent` (KI, Bot, Assistent), `virus` (Virus, Bakterie, Erreger), `cell` (Zelle, Immunsystem). Mehrzahl ohne
  Menschen („Die Agenten arbeiten …“) → Gruppe aus drei. Schnitt mitten im Satz (`_cut_plan`, ab `CUT_MIN` s): beim Schlüsselwort hart auf
  das genannte Ding groß oder die Großaufnahme der Figur – jede dritte Szene bleibt ruhig. Neue Orte: `cinema` (Kinosaal), `restaurant` mit Essen.
- Meerestiere und Winzlinge (`extras.creature`: `shrimp` Pistolenkrebs mit Knallschere, `mantis` Fangschreckenkrebs mit Keulenschlag, `jelly` Qualle,
  `axolotl`, `tardigrade` Bärtierchen; Requisite `aquarium` mit Goldfisch): Nennt der Satz das Tier (`stage.SEA_CREATURES`, `ANY_CREATURES`), ist es
  groß und allein die Figur der Szene – Meerestiere unter Wasser, das Bärtierchen an dem Ort, von dem der Satz spricht. Folgesätze bleiben beim Tier
  (höchstens drei, bis ein Satz von Menschen handelt – `HUMAN_RE`), Ankündigungen („Nummer drei“) zeigen schon das nächste. Unter Wasser stehen nur
  Dinge, auf die das Tier zielt (`SEA_TARGETS`); kein Mensch, keine Explosion, keine Symbole. Neue Tiere dieser Art: zeichnen, in die Liste eintragen,
  Größe in `HERO_SIZE`/`CREATURE_SIZE`, Breite in `LONG_KINDS`, Fall im Selbsttest (`_sea`) ergänzen.
- Mimik und Gesten (`stage.lips`, `stage._mouth`, `stage.gesture_plan`, `rig.GESTURES`): Die Figur bewegt die Lippen nur, wenn sie selbst
  spricht (Ich-/Wir-Satz oder wörtliche Rede) – erzählt die Stimme über sie („Du wachst auf …“), hört sie mit geschlossenem Mund zu.
  Beim Sprechen öffnet jede Silbe den Mund in der Form ihres Vokals (a offen, o/u rund, e/i breit), in Pausen ist er zu. Gesten kommen aus
  den Wörtern: Frage → Schultern hoch, nie/kein → Kopfschütteln, riesig/Millionen → Arme weit, plötzlich/gefährlich → Hände an den Kopf,
  vielleicht/warum → Hand ans Kinn, leider → traurig, toll/endlich → Freude, ja/genau → Nicken, ich/du nur beim Selbst-Sprechen;
  dazwischen mindestens `GAP` Sekunden ruhige Grundhaltung. Neue Gesten: Eintrag in `rig.GESTURES` und Wörter in `stage.CUES`.
- Bewegung und Schnitt: Jede Szene hat eine echte Kamerafahrt (`_camera`, `move`: push, pull, pan_l, pan_r im Wechsel). Übergänge sind
  meist harte Schnitte (`render.TOON_TRANSITIONS`, „cut“), dazwischen ein Wisch – keine Unschärfe-Blende. Ruhige Szenen ohne Schnitt
  höchstens `CALM_MAX` Sekunden; geht kein Insert oder keine Großaufnahme, schneidet `_cut_plan` auf den Gegenschnitt („flip“: gespiegelt,
  näher, andere Fahrt). Großaufnahmen nur bei einer Figur; bei Tieren zielt sie auf den Kopf. `_vary_repeats`: gleiches Bild wie die
  Szene davor → Wesen bewegt sich durchs Bild, Seiten gespiegelt oder Großaufnahme. Wesen ohne Bewegung treiben sanft hin und her.
- Himmels-Dinge (Sonne, Mond, Wolken) rücken in der Regie selbst an eine Stelle mit freiem Himmel (`stage._open_sky_x`) – nicht hinter Bäume.
- Grafik-Einschübe (`number`, `question`, `badge`, `round`, `versus`, `score`, `compare`, `share`, `timer`, `calendar`) rendert
  HyperFrames als HTML/GSAP-Animation (`engine/hyper.py`); fehlt HyperFrames oder scheitert es, zeichnet `graphics.py` sie wie bisher.
  Neue Grafik-Arten zuerst in `graphics.py` (Rückfall), dann optional in `hyper.BUILD`. Abschalten: `AS_HYPER=0`.

- Bibliothek: englische „falsche Freunde“ (`library.FALSE_FRIENDS`: bug, gift, rock …) sind nie Alias; für Begriffe in `main.NO_THINGS`
  (Bug, Glitch, Regel …) wird nichts gelernt. Aufzählungen prüft `writer.list_trouble` (nie mehr Punkte als angekündigt, höchstens fünf).
  Nummern-Schilder und Stempel bleiben nur am Satz, der Nummer bzw. Wort nennt; `stage._carry_thing` lässt das zuvor genannte Ding im
  Folgesatz stehen („diese Früchte … eine Tonne“), bei großer Zahl dreifach.

- Handlung mit einem kleinen Ding (`stage.GIVE_RE`, `TAKE_RE`): „teilt sein Stück Kuchen“, „schenkt“, „isst einen Apfel“ → eine Figur hält das genannte
  Ding vor sich (beim Geben die zweite Figur, sonst die Hauptfigur) statt es nur auf den Boden zu stellen; Kleines in der Hand ist mindestens 84 px groß.
  Einsatzfahrzeuge: `ambulance` (Rettungswagen; Einsatzkräfte, Notruf, Sanitäter) und `police` (Streifenwagen) – ersetzen das beliebige rote Auto.
  Konfetti gibt es nur noch, wenn gefeiert wird (`PARTY_RE`) oder eine Menge jubelt, nicht in jeder fröhlichen Szene. Schilder (`tag`) mit einer Zahl,
  die der Satz nicht nennt, entfallen (Jahreszahlen bleiben). Die Handy-Einblendung zeigt höchstens drei Nachrichten in großer Schrift, ohne Emojis.

- Nie zweimal hintereinander dieselbe Karte/Weltkugel (die zweite Szene spielt mit der Hauptfigur im Zimmer) und nie zweimal hintereinander dieselbe
  Grafik-Art (zwei Zahlen-Tafeln); Zahl-Grafik „3 PRO KETTE“ behält nur die Zahl. Schilder (`tag`) bis 30 Zeichen in kleinerer Schrift; gekürzte
  Einblendungen enden nie auf Artikel oder Verhältniswort (`overlays._DANGLING`).

- Tiefsee-Technik (Flugzeug-Suche, Wracks): `places.underwater(night=True)` zeichnet die dunkle Tiefsee (`_deepsea`: Schlick, Felsrücken, Schlot,
  Meeresschnee). Requisiten `submersible` (Forschungs-Tauchboot mit Scheinwerfer und Sonar-Ringen; Wörter Sonar, Tauchboot, Tauchroboter, U-Boot –
  `stage.SUB_RE`) und `ping` (Signal-Ringe über einem Sender, setzt nur die Regie); Bibliothek: `blackbox` (orange, wie echte Flugschreiber), `wrack`.
  Regie: Nennt der Satz Meeresboden/Tiefsee/„Metern Tiefe“ (`DEEP_RE`) oder gibt das Drehbuch `underwater` an, spielt die Szene unter Wasser – auch
  gegen eine Baukasten-Landschaft mit Meeresoberfläche. Mit Blackbox, Wrack oder Tauchboot im Satz (`DEEP_THING_RE`) wird es die Tiefsee: nur die
  Technik im Bild (Boot links, Wrack/Blackbox rechts am Grund, beim Wrack leuchtet ein Tauchboot), kein Flugzeug, kein Mensch, kein Fisch, keine
  Zahlen-Tafel. Tauchboot und Sonar erscheinen nur unter Wasser (Fledermaus-„Sonar“ im Wald bleibt ohne Boot). Selbsttest: `_deep`.

- Meeresoberfläche (`stage.SURFACE_RE`, `DEBRIS_RE`, Schlussdurchgang in `direct`): „auf dem Ozean“, „über dem Meer“, treibende Trümmerteile spielen auf dem
  Meer mit Himmel (Baukasten `ground: water`) – nicht am Meeresgrund, nicht am Palmenstrand. Dort steht kein Mensch und kein Karton auf dem Wasser:
  Es treibt die Requisite `debris` (Rumpfstück, Sitzkissen, Koffer), sonst fährt ein Schiff. Steht nur ein Flugzeug/Satellit am Himmel, rückt die
  Einblendung tiefer ins freie Bild (`_ov_low`, `render.scene_clip`). Satelliten-Sätze spielen im All (Satellit vor der Erde); eine Europakarte ohne
  Land im Satz (`GEO_RE`) entfällt. Grafik `radar` (Radarschirm, mit `"sub": "lost"` erlischt der Leuchtpunkt) – ab dem zweiten Satz automatisch bei
  „Radar“, „Funkkontakt“, „Transponder“. Bibliothek: `muschel`. Selbsttest: `_surface`.

- Heißluftballon (Ballonflucht, Ballonfahrt – `stage._balloon_story`, greift bei `HOTAIR_RE` in Thema oder Sätzen; ein „Luftballon“ zählt nicht): Requisiten
  `balloon` (fliegt, acht Köpfe in der Plattform-Gondel, Brennerflamme), `balloon_dark` (Gas aus), `balloon_out` (sackt schräg durch), `balloon_fill`
  (richtet sich am Boden mit Flamme auf), `balloon_ground` (Stoffberg mit Gondel), `balloon_down` (Hülle im Gebüsch), `gondola` (Gondel ganz nah),
  `searchlight` (zwei schwenkende Lichtkegel); dazu `sewing` (Nähmaschine mit Stoffbahnen, Wörter nähen/Nähmaschine) und `fabric` (Stoffballen).
  Ort `highsky` (`places.highsky`: hoher Himmel, Wolken, tief unten das Land). Die Regie führt Buch, ob der Ballon in der Luft ist (`B_UP_RE` …
  `B_DOWN_RE`): Flug-Sätze spielen ohne Figuren vor dem hohen Himmel (Suchscheinwerfer, Gas aus, Absturz je ein eigenes Bild), der erste Satz zeigt
  den Ballon im Scheinwerferlicht, am Boden steht die Wiese ohne Bäume und Windräder davor. Einblendungen stehen über dem Ballon (`_ov_low` 3),
  nachts leuchtet er im eigenen Schein (`GLOWS`, `_light`). Selbsttest: `_balloon`.
  Vorgriff am Anfang („kurz vor dem Ziel geht das Gas aus“) zeigt den dunklen Ballon, ohne dass die Geschichte schon fliegt; nach der Gondel ganz nah
  zeigt der Folgesatz (Geländer, Wäscheleine, Gasflaschen) die leere Gondel `gondola_empty` auf der Wiese; „bauen … auf“ zeigt den Stoffberg auch
  ohne das Wort Ballon; ein Ballon aus dem Drehbuch in einem Satz, der nicht vom Ballon handelt, entfällt; Zähler werden über dem Ballon zum Schild.
  Nähmaschine: Figur steht daneben, kein Schnitt auf die Maschine allein (`_no_cut`).
  Abheben und Landung zeigen den Ballon (eine Zahlen-Tafel wird dort zum Schild). Nach der Landung spielt der Schluss auf der Wiese am Dorfrand mit
  der Hauptfigur – keine Großstadtstraße, kein beliebiges Auto, nicht nur ein Streifenwagen vor leeren Häusern.
- Schatz im See (versenkte Kisten, Taucher – `stage._lake_story`, greift bei `LAKE_RE` im Thema oder in zwei Sätzen plus Wörtern wie versenkt/Grund/Taucher):
  Unter Wasser zeigt `places.lakebed` den dunklen Seegrund (Felswände, Schlick, Stämme) statt des Meeresbodens (`scene["_lake"]`, `places.LAKE`).
  Wesen `diver` (Taucher im Neoprenanzug mit Lampe und Blasen – in jedem Video statt des Ersatz-Fischs, wenn die Figur „taucher“ heißt oder der Satz von
  Tauchern spricht: `stage._divers`). Requisiten `crate`/`crates` (Holzkisten statt Pappkarton), `crates_sink` (Kisten sinken trudelnd), `cashcrate` (offene
  Kiste voller Scheine, ohne echtes Banknoten-Motiv), `goldbars`, `logs` (Schicht versunkener Baumstämme), `rocketpart` (verrostetes Versuchsteil am Grund
  statt startender Rakete). An Land spielt die Geschichte am Seeufer (nicht im Büro), ohne Passanten; „Soldaten bringen Kisten“ zeigt zwei Figuren mit
  schlichtem Helm (`hat: army`, ohne Abzeichen) neben dem Kistenstapel; „kein Gold“ zeigt keine Barren. Nie zweimal dasselbe Bild am Grund. Selbsttest: `_lake`.
- Grafiken: „Milliarden“ gesagt, aber „BILLIONEN“ gezeigt → wird berichtigt; Währung in der Unterzeile, die niemand nennt, entfällt; Fragezeichen-Grafik
  an einem Satz ohne Frage wird zur Plakette (`stage.direct`, Anfang).
- Familie im Bild (`stage._family`, `FAMILY_RE`): Spricht der Satz von Familien, Frauen und Kindern, stehen neben der Hauptfigur eine Frau und ein
  Kind (Nebenfiguren dürfen über `look` jetzt auch `size`, `gender`, `hair_color` mitbringen).
- Ecken-Zeilen (`render.build_ass`): Die Zeile oben links wird am Wortende gekürzt; bleibt sie das ganze Video gleich, entfällt eine Uhrzeit darin.
  Eine einzelne Zustands-Angabe oben rechts gilt nur zwei Sätze weiter; nennt sie eine Zahl, die niemand sagt, entfällt sie.
  Eine Uhrzeit in der Ecken-Zeile oder über einer Zahl-Grafik, die der Satz nicht nennt, entfällt (`stage.direct`, Anfang); eine Orts-Angabe je Szene
  („WALD“) gilt nur zwei Sätze weiter und ist keine Überschrift für eine Zahl. Auswahl-Einblendung (`choice`) nur an einer Frage oder einem „oder“.

## Was zu tun ist
1. Offene Wünsche (ohne `"done": true`) und `"auto": true`-Einträge durchgehen, höchstens 8 pro Sitzung, häufigste zuerst.
2. Einzelne Gegenstände: sauber als Eintrag in `docs/data/shapes.json` zeichnen (Format siehe Kopf von `engine/toon/library.py`:
   Zeichenfläche 400×400, Boden bei y=400, 8–30 Formen, echte Höhe in Metern, sinnvolle `aliases` inkl. Mehrzahl) und `"auto"` entfernen.
   Stil: flach, klare Flächen, gedeckte Farben, passend zu den eingebauten Requisiten in `engine/toon/extras.py`.
3. Was kein einzelner Gegenstand ist (Ort, Landschafts-Baustein, Tier, Bewegung, Wetter, Einblendung): im Code ergänzen
   (`places.py`, `extras.py`, `rig.py`, `stage.py`, `overlays.py`) und in der Drehbuch-Anleitung `engine/writer.py` (Abschnitt TOON) eintragen,
   dazu passende Text-Hinweise in `stage.py` (`HINTS`, `TEXT_PROPS`).
4. Jedes neue Teil ansehen: Bild rendern (z. B. mit `engine.toon.selftest.frame(...)` oder `python -m engine.main learn` ist NICHT nötig)
   und mit eigenen Augen prüfen – Größenverhältnis zu den Figuren, Lesbarkeit, Stil.
5. `FONTS_DIR=/usr/share/fonts/truetype/google-fonts python3 -m engine.toon.selftest` muss mit 0 Fehlern enden.
6. Erledigte Wünsche in `wishes.json` mit `"done": true` markieren. Committen (`Engine-Ausbau: …`), `git pull --rebase`, auf `main` pushen.

## Grenzen
- Keine echten Personen, Marken, Logos oder geschützten Figuren zeichnen.
- Nichts an Zugangsdaten, `tokens/`, Upload-Code, Workflow-Zeitplan oder App-Einstellungen ändern. Keine Videos hochladen.
- Die App (`quellcode/`, `AutoShorts.cmd`) nur anfassen, wenn ein Ausbau ohne das nicht funktioniert.
- Schlägt der Selbsttest fehl und lässt sich das nicht beheben: nichts pushen, sondern berichten.

## Video nachbauen (Aktion `remake`)
Die App lädt ein Vorlagen-Video in das Release `inbox` und startet `-f 'inputs[action]=remake' -f 'inputs[video_id]=<Dateiname>'`.
`engine/remake.py` hört es an (Spracherkennung), schickt zehn Einzelbilder mit dem Text an die Text-KI (Ablauf, Thema, Video-Art) und
`writer.write_script(..., source=…)` schreibt daraus ein eigenes Drehbuch: gleiche Idee und gleiches Tempo, eigene Worte, keine Namen,
Marken oder Figuren der Vorlage. Danach wird die Vorlage aus `inbox` gelöscht. Statt einer Datei geht auch ein TikTok-/YouTube-Link:
die App lädt ihn auf dem PC mit yt-dlp (bei Bedarf einmal per `pip --user` eingerichtet) und legt die Datei in `inbox`; klappt das nicht,
bekommt der Lauf den Link als `video_id`, `remake.download` versucht es dort, und als letzter Ausweg baut `remake.analyze_link_text` nach
Titel/Beschreibung (oEmbed). „Als Nächstes einplanen“ (App): Vorlage wird ebenso bereitgelegt, aber statt eines Laufs entsteht ein
Warteschlangen-Eintrag `{"remake": Dateiname|Link, "url", "next": true, "category": ""}` – `pick` nimmt ihn zuerst, `queue_remake` baut
ihn nach (Video-Art aus der Vorlage, wenn keine gewählt) und überholt dabei ein schon vorbereitetes Drehbuch. Kategorie `comedy`: absurde Ich-Geschichten mit Humor.

## Einstieg (erste drei Sekunden)
`writer.sharpen_hook` schärft nach jedem Drehbuch die ersten zwei Sätze: Satz 1 nennt IMMER das Thema kurz und spannend (höchstens zwölf
Wörter, z. B. „Drei Tier-Superkräfte, die eigentlich unmöglich sind.“; bei Listen die Anzahl; nicht den Titel wörtlich, keine Floskel wie
„Was wäre, wenn“/„Stell dir vor“), Satz 2 ist der Cliffhanger, den erst das Ende einlöst („Und die letzte kann dir das Leben retten.“) –
übernommen wird nur, was die Prüfung (`hook_weak`: Thema genannt, kurz, ohne Floskel) besteht. Im ersten Bild steht der Titelbild-Text als
Schild (`tag`). `stage._opening`: im ersten Bild reagiert die Hauptfigur sichtbar; die Kamera ruckt kräftig ins Bild (`opener`), Musik und
ein Auftakt-Ton sind ab der ersten Sekunde da. `stage._cold_open`: zeigt das erste Bild nur Menschen, die dastehen, kommt dort schon das
stärkste Bild aus den ersten zwei Dritteln (Vorgriff, `_scene_punch`). Schluss ohne Aufforderung, als Schleife zurück zum ersten Satz;
die Frage an die Zuschauer steht in der Beschreibung. Spannungsbogen (`writer.loop_pass`, nach dem Einstieg): nach jeder Auflösung bzw.
jedem Listenpunkt ein Rehook (neue konkrete Frage), genau eine ehrliche Finte („Du denkst … Falsch – …“); die Text-KI formuliert höchstens fünf
Sätze um, übernommen wird nur, was die Information des alten Satzes behält (≥ 50 % der Inhaltswörter), keine neuen Zahlen, Satz 1/2 und Schluss bleiben. Der Sprecher wird für die Mindestlänge höchstens um 4 % verlangsamt.

## Zahlen und Kanal-Analyse
- TikTok-Follower ohne eigene TikTok-Anmeldung (Upload über Zernio): `uploaders.tiktok_followers_fallback` – erst Zernio-Kontodaten,
  sonst öffentliche Profilseite (`tiktok_handle` in den Einstellungen). YouTube ohne Anmeldung genauso über `youtube_handle` (`uploaders.yt_public`).
- Live im Dashboard (`/api/live` im App-Server, jede Minute): YouTube mit Anmeldung über die API (Abos, Aufrufe des Kanals, Likes der eigenen
  Videos; Anmeldung aus `tokens/youtube.enc`, alle 2 Minuten), sonst öffentliche Kanalseite; TikTok: Follower und Likes vom Profil, Aufrufe
  aus der Videoliste (yt-dlp) oder den einzelnen Video-Seiten. Was live nicht kommt, nimmt die App aus dem letzten gespeicherten Stand.
- `engine/niche.py`: je Video-Art die erfolgreichsten Shorts anderer Kanäle der letzten 14 Tage (YouTube-API, sonst öffentliche Suche),
  bewertet nach Aufrufen pro Tag und Faktor Aufrufe/Abonnenten; die Text-KI macht daraus eigene Themen. Läuft mit den Trends (höchstens
  alle 6 Stunden, „Aktualisieren“ in der App sofort), liegt in `trends.json` unter `niche` und fließt in `writer.new_topic` ein.
  Eigene Suchbegriffe je Video-Art: Feld `niche_queries` in der Kategorie.


## Ton (earshot, Openverse, real-sfx)
- `engine/sound.py`: Klang-Bibliothek in `assets/sfx/` (Liste `manifest.json`, Quellen `CREDITS.md`), gebaut mit der Aktion `sounds`:
  earshot-Soundeffekte (MIT, im Code gebaut, je Rolle mehrere Takes mit gemessenem Einsatz/Spitze) und Openverse-Aufnahmen
  (nur CC0/Public Domain) als Hintergrund-Geräusch je Ort/Wetter, dazu freie Musik in `music/<Video-Art>/`.
- Platzierung nach real-sfx: Whoosh-Spitze 37 ms nach dem Schnitt, Pop 30 ms danach, Tick/Knock leicht davor; Mindestabstand je Rolle;
  kleiner Klang neben großem fällt weg; Musik wird unter der Stimme abgesenkt (sidechain). Ereignisse kommen aus der Animation
  (`scene["_sfx"]`: Dinge springen ins Bild → pop, Schreck → hit, Schnitt im Satz → swish/shutter, Geste „shock“ → hit …) und aus
  Einblendungen (stamp → stamp, tag → shutter, thermo/bar → tick). Ohne Bibliothek bleiben die alten ffmpeg-Klänge.
- Skills für Claude-Sitzungen liegen in `.claude/skills/` (earshot: Ton „hören“ und prüfen; real-sfx: Ton-Design echter Aufnahmen).

- Ausbau 15.11.2026: Bibliothek von Hand neu gezeichnet: `pistole` (schlichte Pistole ohne Vorbild-Modell), `sprungfeder`, `geländewagen`, `lüftungsschacht`,
  `schweißbrenner`, `usb-stick`. Die vorläufige Zeichnung `tuer` ist entfernt – die eingebaute Tür (`door`) kennt jetzt auch „tuer“, „Türe“, „Türen“,
  „Haustür“. Die vorläufige Krabbe `krebs` ist entfernt: ein bloßes „Krebs“ ist im Meer der Krebs als Figur (`stage._sea_kind`), sonst die Krankheit –
  als Bibliotheks-Gegenstand stünde bei jedem Satz über die Krankheit eine rote Krabbe im Bild. `main.known_thing` kennt „Krebs“ deshalb fest.

- Video über ein einziges Meerestier (Prüfung 15.11.2026, „Fangschreckenkrebs“): Nennt das Thema genau ein Meerestier (`stage._sea_default`), meint ein bloßes
  „Krebs“ – im Satz wie als Figuren-Kennung – dieses Tier und nicht mehr den Pistolenkrebs. Damit nicht jede Szene dasselbe Bild ist: Stellt das Drehbuch bei einem
  Satz über Menschen („ein menschlicher Wimpernschlag“, „Menschen haben drei Farbrezeptoren“ – `SEA_HUMAN_RE`) einen Menschen unter Wasser, spielt der Satz als
  Großaufnahme der Figur im Zimmer; mit Becken/Aquarium im Satz (`TANK_RE`) steht die Figur im Labor neben dem Forschungsbecken `tank` (Aquarium mit Krebs).
  Vor der Keule erscheint, wovon der Satz spricht (`SEA_TARGETS`): die Requisite `cavitation` (Dampfblase wächst, fällt zusammen, blitzt mit Druckringen – Wörter
  Dampfblase, Kavitation, Blase kollabiert, Druckwelle: `CAVI_RE`) oder die Sprungfeder aus der Bibliothek; zweimal hintereinander steht das Bild gespiegelt.
  Dinge neben dem groß gezeichneten Tier sind mindestens 300 px hoch (`_PROP_MIN`), Blitz, Glasscheibe und Feder stehen auch bei dunkler Stimmung im Licht (`GLOWS`).
  Küchendampf (`steam`) gibt es unter Wasser nicht. „Mehrere tausend Grad“ ergibt keinen Zähler „1.000 GRAD“ (`find_figure`). `writer.polish` streicht den
  Schlusssatz auch dann, wenn er den ersten mit Vorspann wiederholt („Und hier kommen drei Fakten …“). Selbsttest: `_one_animal`.
  Zielt das Tier auf ein Ding (Glas, Dampfblase, Feder), schwimmt es nicht aus dem Bild (`_vary_repeats` lässt solche Szenen in Ruhe). Eine Figur „taucher“
  bleibt in einem Satz über Taucher ein Taucher und wird nicht zum Krebs. Titelbild (`stage.poster`): Nennt der Kern des Themas das Tier, steht das Tier auf dem
  Titelbild – Gegenstände werden nur noch im Kern des Themas gesucht, nicht in den Vorgaben dahinter („kein Panzerglas“ ergab eine Glasscheibe als Motiv).
  `poster_hero`: Das Tier, das Titel/Thema nennen, steht immer auf dem Titelbild – auch wenn es beim letzten (verworfenen) Bau schon dort war. Tier und Ziel
  stehen sich gegenüber (Tier 400, Ding 860); ein Notizzettel/eine Liste über einer solchen Szene entfällt (schob den Krebs an den Rand). Der Menschen-Satz
  bleibt eine Großaufnahme (Figur läuft nicht durchs Zimmer). `writer.polish` streicht einen abgebrochenen Schlusssatz („Und genau deshalb –“); die Unterzeile
  einer Zahl-Grafik, die nur die Zahl wiederholt, entfällt.
  Menschen-Sätze werden auch erkannt, wenn das Drehbuch dort das Tier hinstellt („Menschen haben drei Arten von Farbrezeptoren“, „schneller als ein
  Wimpernschlag“ – `SEA_PEOPLE_RE`): Dann steht die Hauptfigur im Bild.

## Musik-Kugel (Video-Art `musik`, einmal am Tag)
- `engine/bounce.py`: Eine Kugel springt durch Glasscheiben, jeder Aufprall ist ein Ton der Melodie. Der Flugweg wird aus den Tonzeiten
  rückwärts gebaut (echte Wurfparabel zwischen zwei Tönen, die Scheibe liegt so, dass sie die Richtungsänderung erklärt) – deshalb sitzt
  jeder Aufprall exakt auf dem Ton. Ton selbst erzeugt (Glockenspiel + Glasklirren + Hall), oben „Erkennst du das Lied?“, am Ende die Auflösung.
- NUR gemeinfreie Melodien in `SONGS` (Komponist seit über 70 Jahren tot oder Volkslied) – Chart-Songs sind auch nachgespielt geschützt.
  Neue Melodie: Eintrag `slug: (Name, Komponist, Tempo, _seq("E5:.25 D#5:.25 …"))`, Dauer in Schlägen, `r` = Pause.
- Physik (`path`): an jedem Ton ein echter Abprall (`_reflect`: Einfallswinkel = Ausfallswinkel, Schwung 0,86–1,08; nur wenn ein
  langer Ton sonst unerreichbar ist, federt die Scheibe stärker, `SPRINGY`). Gesucht wird mit Rückwärtssuche (geht einen Ton zurück, wenn es
  nicht weitergeht). Pausen über `MAX_AIR` bekommen stille Zwischen-Aufpralle (`with_ghosts`). `appear_times`: eine Scheibe erscheint erst,
  wenn die Kugel nicht mehr durch ihren Platz fliegt.
- Eigene Lieder: App → „Musik-Kugel: eigene Lieder“ lädt Audiodateien ins Release `songs` (Name „Künstler - Titel.mp3“). Sie haben Vorrang
  (das am längsten nicht gespielte); `song_hits` nimmt die lautesten 40 s (Refrain) und findet die Einsätze (Spektral-Fluss), `file_song`
  mischt den Original-Ton mit leisem Glasklirren. Rechte an den Liedern liegen beim Nutzer – die Engine lädt keine Lieder selbst aus dem Netz.
- Remixe (`engine/remix.py`): ohne eigene Lieder wird automatisch eine bekannte gemeinfreie Melodie als moderner Track produziert
  (Stile `STYLES`: Phonk, Trap, EDM, Lo-Fi, Sped Up – im Wechsel): Schlagzeug, 808/Bass, Akkorde je Takt aus der Melodie (`harmonize`), Lead
  spielt die Melodie, jeder Melodie-Ton ist ein Aufprall. Neue Melodie: Eintrag in `bounce.SONGS` UND Tonart/Takt in `remix.KEYS`.
- Freie Tracks (`bounce.cc_track`): ccMixter/Jamendo über Openverse, nur CC0 und CC BY (kein NC/ND); die Namensnennung (`credit`) kommt in die
  Beschreibung und ans Videoende. `make_bounce` wechselt ohne eigene Lieder zwischen Remix und freiem Track (`STATE["bounce_src"]`);
  Thema „cc“ oder „remix“ im Studio erzwingt die Quelle.
- Kategorie mit `every_days: 1` und `special: "bounce"`: `main.pick` nimmt sie, sobald ein Tag seit der letzten um ist (`STATE["last_musik"]`),
  sonst nie; `make_bounce` rendert ohne Drehbuch und Sprecher und lädt hoch wie jedes Video.
