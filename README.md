# Dyson Sphere – Minecraft-Client

Der Client für unsere Dyson-Sphären-Welt (Minecraft Java **26.1.2**, Fabric):

- **Adrenaline** – reine Performance-Mods (Sodium, Lithium, …), sieht aus wie Vanilla
- **Distant Horizons** – Fernsicht weit über die normale Sichtweite hinaus
- **Nuit** – eigener Sternenhimmel
- **Milchstraßen-Himmel** – die Milchstraße aus NASA-Sternkarten als
  Hintergrund, nur in der Dyson-Welt (Leere-Biom der Oberwelt)

Die Mods werden nicht hier gespeichert: Das Pack verweist auf Modrinth, jede
Datei wird beim Spieler heruntergeladen und per SHA-512 geprüft.

## Installieren (einmalig)

1. Launcher: **Prism Launcher** (empfohlen, bringt Java 25 automatisch mit)
   oder **MultiMC** (dort in den Einstellungen Java 25 eintragen).
2. Unter *Releases* die Datei **`Dyson-Sphere-MultiMC.zip`** herunterladen.
3. Im Launcher: *Instanz hinzufügen → Import aus ZIP* → die Datei wählen.
4. Instanz starten. Beim ersten Start lädt der Installer alle Mods (dauert
   etwa eine Minute), danach startet Minecraft.
5. Im Spiel den Server hinzufügen – die Adresse gibt es privat.

**Updates kommen automatisch:** Vor jedem Start gleicht der Installer das
Pack mit diesem Repository ab.

## Milchstraßen-Himmel einschalten

Neue Installationen haben ihn automatisch an. Wer das Pack schon vor
Version 0.2.0 gestartet hat, schaltet ihn einmal selbst ein: im Spiel
*Optionen → Ressourcenpakete* → „dyson-sky.zip“ nach rechts schieben → *Fertig*
(oder im Mod-Menü bei *Config Manager* auf *Update* drücken).

## Schwächere Grafikkarten (z. B. GTX 1050 Ti)

Sichtweite in den Videoeinstellungen auf 12–16 Chunks stellen und in den
Distant-Horizons-Einstellungen (Taste F6 bzw. Mod-Menü) die Qualität auf
„Niedrig“. Eigene Einstellungen bleiben bei Updates erhalten.

## Für Pflege

`python3 build_pack.py` erzeugt `pack.toml`, `index.toml`, `mods/` und
`config/` neu (Adrenaline-Version und Zusatz-Mods stehen oben im Skript) und
packt `sky/` nach `resourcepacks/dyson-sky.zip`;
`python3 build_pack.py --instance-zip` baut zusätzlich die Import-Datei.

Die Himmelstextur entsteht aus NASAs Sternkarte in galaktischen Koordinaten
(`starmap_2020_4k_gal.exr` von https://svs.gsfc.nasa.gov/4851, SHA-256
`bce1d2c364720fd13ebbfaf1d444404a96b7cb4d7d8ddc88d44447358552361a`) mit
`python3 tools/make_sky.py starmap_2020_4k_gal.exr sky/assets/dyson/textures/sky/milky_way.png --exposure 0.6`
(nur Python-Standardbibliothek; Würfel-Layout wie Nuits `square-textured`).

## Lizenzen und Dank

- [Adrenaline](https://modrinth.com/modpack/adrenaline) (MIT, skywardmc) –
  Mod-Auswahl und die Standardeinstellungen unter `config/`.
- Jede Mod steht unter ihrer eigenen Lizenz (siehe Modrinth).
- [packwiz](https://packwiz.infra.link/) und packwiz-installer-bootstrap.
- Milchstraßen-Himmel: Sternkarte „Deep Star Maps 2020“ von NASA/Goddard Space
  Flight Center Scientific Visualization Studio; Gaia-DR2-Daten: ESA/Gaia/DPAC.
  Die daraus erzeugte Textur steht wie die Gaia-Daten unter CC BY-SA 3.0 IGO
  (siehe `sky/CREDITS.txt`).
- Die Skripte in diesem Repository stehen unter der MIT-Lizenz.
