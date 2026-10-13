# Dyson Sphere – Minecraft-Client

Der Client für unsere Dyson-Sphären-Welt (Minecraft Java **26.1.2**, Fabric):

- **Adrenaline** – reine Performance-Mods (Sodium, Lithium, …), sieht aus wie Vanilla
- **Distant Horizons** – Fernsicht weit über die normale Sichtweite hinaus
- **Nuit** + **Nuit Interop** – eigener Sternenhimmel

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

## Schwächere Grafikkarten (z. B. GTX 1050 Ti)

Sichtweite in den Videoeinstellungen auf 12–16 Chunks stellen und in den
Distant-Horizons-Einstellungen (Taste F6 bzw. Mod-Menü) die Qualität auf
„Niedrig“. Eigene Einstellungen bleiben bei Updates erhalten.

## Für Pflege

`python3 build_pack.py` erzeugt `pack.toml`, `index.toml`, `mods/` und
`config/` neu (Adrenaline-Version und Zusatz-Mods stehen oben im Skript);
`python3 build_pack.py --instance-zip` baut zusätzlich die Import-Datei.

## Lizenzen und Dank

- [Adrenaline](https://modrinth.com/modpack/adrenaline) (MIT, skywardmc) –
  Mod-Auswahl und die Standardeinstellungen unter `config/`.
- Jede Mod steht unter ihrer eigenen Lizenz (siehe Modrinth).
- [packwiz](https://packwiz.infra.link/) und packwiz-installer-bootstrap.
- Das Skript in diesem Repository steht unter der MIT-Lizenz.
