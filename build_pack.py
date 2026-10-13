#!/usr/bin/env python3
"""Build the Dyson Sphere client modpack (packwiz format).

The pack is Adrenaline (performance only, MIT) plus Distant Horizons, Nuit and
Nuit Interop, pinned to exact Modrinth versions. Mod files are never copied:
every mod is a packwiz metafile with its Modrinth download URL and SHA-512, so
packwiz-installer downloads and verifies it on each player's PC.

Usage:
  python3 build_pack.py                 # regenerate pack.toml, index.toml, mods/, config/
  python3 build_pack.py --instance-zip  # also build dist/Dyson-Sphere-MultiMC.zip

Needs network access to Modrinth (and GitHub for the instance zip).
"""

import argparse
import hashlib
import io
import json
import shutil
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API = "https://api.modrinth.com/v2"
HEADERS = {"User-Agent": "staedter/dyson-sphere-modpack (github.com/staedter/dyson-sphere-modpack)"}
PACK_NAME, PACK_VERSION = "Dyson Sphere", "0.1.0"
MINECRAFT, FABRIC_LOADER = "26.1.2", "0.19.5"
BASE = ("adrenaline", "26.5.1+mc26.1.2.fabric")
EXTRAS = {                                  # Modrinth slug -> pinned version number, side
    "distanthorizons": ("3.3.3-26.1.2", "both"),
    "nuit": ("mc26.1.2-1.0.0-beta.6+fabric", "client"),
    "nuit-interop": ("mc26.1.2-1.0.0-beta.5+fabric", "client"),
}
PACK_URL = "https://raw.githubusercontent.com/staedter/dyson-sphere-modpack/main/pack.toml"
BOOTSTRAP_URL = "https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/packwiz-installer-bootstrap.jar"
BOOTSTRAP_SHA256 = "a8fbb24dc604278e97f4688e82d3d91a318b98efc08d5dbfcbcbcab6443d116c"   # pinned on first download (2026-10-14); GitHub publishes no digest for v0.0.3
GENERATED = ("mods", "config")


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as response:
        return response.read()


def fetch_json(url):
    return json.loads(fetch(url))


def verified(url, algorithm, digest):
    data = fetch(url)
    if hashlib.new(algorithm, data).hexdigest() != digest:
        raise SystemExit(f"{algorithm} mismatch for {url}")
    return data


def modrinth_version(slug, number):
    versions = fetch_json(f"{API}/project/{slug}/version")
    match = [v for v in versions if v["version_number"] == number]
    if not match:
        raise SystemExit(f"{slug} has no version {number}")
    return match[0]


def primary_file(version):
    files = version["files"]
    return next((f for f in files if f["primary"]), files[0])


def toml(value):
    return json.dumps(value, ensure_ascii=False)


def write_metafile(slug, title, file, side, project_id, version_id):
    lines = [f"name = {toml(title)}", f"filename = {toml(file['filename'])}", f"side = {toml(side)}", "",
             "[download]", f"url = {toml(file['url'])}", 'hash-format = "sha512"',
             f"hash = {toml(file['hashes']['sha512'])}", "", "[update]", "[update.modrinth]",
             f"mod-id = {toml(project_id)}", f"version = {toml(version_id)}", ""]
    path = ROOT / "mods" / f"{slug}.pw.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def side_of(env):
    client, server = env.get("client", "required"), env.get("server", "required")
    if server == "unsupported":
        return "client"
    return "server" if client == "unsupported" else "both"


def add_base():
    """Adrenaline's mods as metafiles, its overrides as plain files."""
    version = modrinth_version(*BASE)
    pack_file = primary_file(version)
    mrpack = verified(pack_file["url"], "sha512", pack_file["hashes"]["sha512"])
    archive = zipfile.ZipFile(io.BytesIO(mrpack))
    index = json.loads(archive.read("modrinth.index.json"))
    ids = [entry["downloads"][0].split("/data/")[1].split("/")[0] for entry in index["files"]]
    projects = {p["id"]: p for p in fetch_json(f"{API}/projects?ids=" + urllib.parse.quote(json.dumps(ids, separators=(",", ":"))))}
    for entry, project_id in zip(index["files"], ids):
        url = entry["downloads"][0]
        file = {"filename": entry["path"].split("/")[-1], "url": url, "hashes": entry["hashes"]}
        project = projects[project_id]
        write_metafile(project["slug"], project["title"], file, side_of(entry.get("env", {})),
                       project_id, url.split("/versions/")[1].split("/")[0])
    for name in archive.namelist():
        if name.startswith("overrides/") and not name.endswith("/"):
            target = ROOT / name.removeprefix("overrides/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    return index["dependencies"]


def add_extras():
    for slug, (number, side) in EXTRAS.items():
        version = modrinth_version(slug, number)
        project = fetch_json(f"{API}/project/{slug}")
        write_metafile(slug, project["title"], primary_file(version), side, version["project_id"], version["id"])


def write_index_and_pack():
    entries = []
    for path in sorted(p for d in GENERATED for p in (ROOT / d).rglob("*") if p.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        entry = [f"file = {toml(relative)}", f"hash = {toml(hashlib.sha256(path.read_bytes()).hexdigest())}"]
        if relative.endswith(".pw.toml"):
            entry.append("metafile = true")
        entries.append("[[files]]\n" + "\n".join(entry))
    index = 'hash-format = "sha256"\n\n' + "\n\n".join(entries) + "\n"
    (ROOT / "index.toml").write_text(index, encoding="utf-8")
    pack = [f"name = {toml(PACK_NAME)}", 'author = "staedter"', f"version = {toml(PACK_VERSION)}",
            'pack-format = "packwiz:1.1.0"', "", "[index]", 'file = "index.toml"', 'hash-format = "sha256"',
            f"hash = {toml(hashlib.sha256(index.encode()).hexdigest())}", "", "[versions]",
            f"minecraft = {toml(MINECRAFT)}", f"fabric = {toml(FABRIC_LOADER)}", ""]
    (ROOT / "pack.toml").write_text("\n".join(pack), encoding="utf-8")
    return len(entries)


def instance_zip():
    """MultiMC/Prism instance that runs packwiz-installer before every start."""
    jar = verified(BOOTSTRAP_URL, "sha256", BOOTSTRAP_SHA256)
    cfg = ("InstanceType=OneSix\nname=Dyson Sphere\niconKey=default\nOverrideCommands=true\n"
           f'PreLaunchCommand="$INST_JAVA" -jar packwiz-installer-bootstrap.jar {PACK_URL}\n'
           "OverrideMemory=true\nMinMemAlloc=1024\nMaxMemAlloc=4096\n")
    components = {"formatVersion": 1, "components": [
        {"uid": "net.minecraft", "version": MINECRAFT, "important": True},
        {"uid": "net.fabricmc.intermediary", "version": MINECRAFT, "dependencyOnly": True},
        {"uid": "net.fabricmc.fabric-loader", "version": FABRIC_LOADER}]}
    target = ROOT / "dist" / "Dyson-Sphere-MultiMC.zip"
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Dyson Sphere/instance.cfg", cfg)
        archive.writestr("Dyson Sphere/mmc-pack.json", json.dumps(components, indent=4))
        archive.writestr("Dyson Sphere/.minecraft/packwiz-installer-bootstrap.jar", jar)
    return target, "v0.0.3"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance-zip", action="store_true", help="also build the MultiMC instance zip")
    args = parser.parse_args()
    for name in GENERATED:
        shutil.rmtree(ROOT / name, ignore_errors=True)
    dependencies = add_base()
    if dependencies != {"fabric-loader": FABRIC_LOADER, "minecraft": MINECRAFT}:
        raise SystemExit(f"base pack targets {dependencies}; update MINECRAFT/FABRIC_LOADER")
    add_extras()
    print(f"pack written: {write_index_and_pack()} files in index.toml")
    if args.instance_zip:
        target, tag = instance_zip()
        print(f"instance zip: {target} (packwiz-installer-bootstrap {tag})")


if __name__ == "__main__":
    main()
