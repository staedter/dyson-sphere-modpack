#!/usr/bin/env python3
"""Turn NASA's equirectangular galactic star map (OpenEXR) into a Nuit skybox texture.

Standard library only: a minimal OpenEXR reader (single-part scanline files with
NONE, ZIPS or ZIP compression and HALF channels), a tone-mapping lookup table,
an equirectangular-to-cube projection in Nuit's square-textured layout and a PNG
writer.

Nuit's square-textured layout (FlashyReese/nuit, Utils.TEXTURE_FACES and
SkyboxFace): a 3 x 2 grid, top row bottom | top | south, bottom row
west | north | east; within a face, texel (u, v) in [0, 1]^2 looks along
origin + u * uAxis + v * vAxis on the cube [-1, 1]^3 (x east, y up, z south).

Usage: make_sky.py <input.exr> <output.png> [--face 1024] [--exposure 1.0]
                   [--centre-deg 20] [--preview preview.png]
"""

import argparse
import array
import math
import struct
import zlib
from itertools import accumulate

FACES = (  # (column, row, origin, u axis, v axis) per Nuit face index 0..5
    (0, 0, (-1, -1, -1), (2, 0, 0), (0, 0, 2)),     # 0 bottom
    (1, 1, (-1, 1, -1), (2, 0, 0), (0, -2, 0)),     # 1 north
    (2, 0, (1, 1, 1), (-2, 0, 0), (0, -2, 0)),      # 2 south
    (1, 0, (-1, 1, 1), (2, 0, 0), (0, 0, -2)),      # 3 top
    (2, 1, (1, 1, -1), (0, 0, 2), (0, -2, 0)),      # 4 east
    (0, 1, (-1, 1, 1), (0, 0, -2), (0, -2, 0)),     # 5 west
)
COMPRESSION = {0: ("NONE", 1), 2: ("ZIPS", 1), 3: ("ZIP", 16)}


def read_header(f):
    magic, version = struct.unpack("<ii", f.read(8))
    if magic != 20000630 or version & 0x200 or version & 0x1000:
        raise SystemExit("unsupported OpenEXR file (need single-part scanline)")
    header = {}

    def cstr():
        out = bytearray()
        while (c := f.read(1)) != b"\0":
            out += c
        return out.decode()

    while (name := cstr()):
        kind = cstr()
        size, = struct.unpack("<i", f.read(4))
        header[name] = (kind, f.read(size))
    return header


def channels(value):
    names, i = [], 0
    while value[i] != 0:
        j = value.index(b"\0", i)
        names.append((value[i:j].decode(), struct.unpack("<i", value[j + 1:j + 5])[0]))
        i = j + 1 + 16
    return names


def unpredict(data):
    """Undo OpenEXR's ZIP predictor and byte interleaving."""
    restored = bytes(v & 255 for v in accumulate(data, lambda a, b: a + b - 128))
    half = (len(restored) + 1) // 2
    out = bytearray(len(restored))
    out[0::2] = restored[:half]
    out[1::2] = restored[half:]
    return out


def half_lut(exposure, gamma=2.2):
    """8-bit tone-mapped value for every 16-bit half pattern."""
    lut = bytearray(65536)
    for bits in range(65536):
        value = struct.unpack("<e", struct.pack("<H", bits))[0]
        if not value > 0 or math.isinf(value):
            lut[bits] = 255 if value == math.inf else 0
            continue
        lut[bits] = round(255 * min(1.0, value * exposure) ** (1 / gamma))
    return lut


def read_exr(path, exposure):
    """The image as three bytearrays (R, G, B), tone-mapped to 8 bits."""
    with open(path, "rb") as f:
        header = read_header(f)
        compression = header["compression"][1][0]
        if compression not in COMPRESSION:
            raise SystemExit(f"unsupported OpenEXR compression {compression}")
        lines_per_chunk = COMPRESSION[compression][1]
        xmin, ymin, xmax, ymax = struct.unpack("<4i", header["dataWindow"][1])
        width, height = xmax - xmin + 1, ymax - ymin + 1
        names = channels(header["channels"][1])
        if any(kind != 1 for _, kind in names):
            raise SystemExit("only HALF channels are supported")
        chunks = (height + lines_per_chunk - 1) // lines_per_chunk
        offsets = struct.unpack(f"<{chunks}Q", f.read(8 * chunks))
        lut = half_lut(exposure)
        planes = {name: bytearray(width * height) for name, _ in names}
        for offset in offsets:
            f.seek(offset)
            y, size = struct.unpack("<ii", f.read(8))
            raw = f.read(size)
            lines = min(lines_per_chunk, ymax + 1 - y)
            expected = lines * len(names) * width * 2
            data = raw if size == expected else unpredict(zlib.decompress(raw))
            for line in range(lines):
                row = (y - ymin + line) * width
                for c, (name, _) in enumerate(names):
                    start = (line * len(names) + c) * width * 2
                    values = array.array("H")
                    values.frombytes(bytes(data[start:start + width * 2]))
                    planes[name][row:row + width] = bytes(map(lut.__getitem__, values))
    return width, height, planes["R"], planes["G"], planes["B"]


def sample(plane, width, height, x, y):
    """Bilinear sample with horizontal wrap and clamped rows."""
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = x - x0, y - y0
    xa, xb = x0 % width, (x0 + 1) % width
    ya, yb = min(max(y0, 0), height - 1), min(max(y0 + 1, 0), height - 1)
    top = plane[ya * width + xa] * (1 - fx) + plane[ya * width + xb] * fx
    bottom = plane[yb * width + xa] * (1 - fx) + plane[yb * width + xb] * fx
    return top * (1 - fy) + bottom * fy


def cube(image, face_size, centre_deg):
    """The 3 x 2 Nuit texture as RGB rows."""
    width, height, red, green, blue = image
    rows = [bytearray(3 * 3 * face_size) for _ in range(2 * face_size)]
    centre = math.radians(centre_deg)
    for column, row, origin, ua, va in FACES:
        for j in range(face_size):
            v = (j + 0.5) / face_size
            out = rows[row * face_size + j]
            for i in range(face_size):
                u = (i + 0.5) / face_size
                dx = origin[0] + u * ua[0] + v * va[0]
                dy = origin[1] + u * ua[1] + v * va[1]
                dz = origin[2] + u * ua[2] + v * va[2]
                norm = math.sqrt(dx * dx + dy * dy + dz * dz)
                lat = math.asin(dy / norm)                      # galactic latitude b
                lon = centre - math.atan2(dz, dx)               # galactic longitude l
                x = (0.5 - lon / (2 * math.pi)) * width - 0.5   # l grows to the left
                y = (0.5 - lat / math.pi) * height - 0.5
                k = 3 * (column * face_size + i)
                out[k] = round(sample(red, width, height, x, y))
                out[k + 1] = round(sample(green, width, height, x, y))
                out[k + 2] = round(sample(blue, width, height, x, y))
    return rows


def write_png(path, rows):
    width, height = len(rows[0]) // 3, len(rows)

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    raw = bytearray()
    for row in rows:
        raw.append(1)                                   # filter "Sub"
        raw += bytes((row[i] - (row[i - 3] if i >= 3 else 0)) & 255 for i in range(len(row)))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))


def preview(rows, path, step):
    small = [bytearray(r[k] for i in range(0, len(r) // 3, step) for k in (3 * i, 3 * i + 1, 3 * i + 2))
             for r in rows[::step]]
    write_png(path, small)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--face", type=int, default=1024)
    parser.add_argument("--exposure", type=float, default=1.0)
    parser.add_argument("--centre-deg", type=float, default=20.0)
    parser.add_argument("--preview")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()
    image = read_exr(args.source, args.exposure)
    if args.stats:
        width, height, red, green, blue = image
        values = sorted(max(red[i], green[i], blue[i]) for i in range(0, width * height, 97))
        for q in (0.5, 0.9, 0.99, 0.999):
            print(f"8-bit max channel at {q:.3f}: {values[int(q * (len(values) - 1))]}")
        return
    rows = cube(image, args.face, args.centre_deg)
    write_png(args.target, rows)
    if args.preview:
        preview(rows, args.preview, max(1, args.face // 256))


if __name__ == "__main__":
    main()
