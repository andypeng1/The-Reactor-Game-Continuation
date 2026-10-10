#!/usr/bin/env python3
"""Turn an ASCII PPM (P3) into a PNG, using nothing but the standard library.

Why this exists: the Roblox side can only hand out text, so the lens renders
itself as P3 and POSTs it to receive.py. Something has to make that viewable,
and Pillow is not installed on this machine (the memory that said it was is
wrong, or it was true of a different interpreter). zlib + struct is enough for
a PNG -- the format is five chunks and one filter byte per row.

    python -I _tools/ppm_to_png.py Data/gravity_lens.ppm Data/gravity_lens.png
"""
import struct
import sys
import zlib


def read_p3(path):
    with open(path, "rb") as handle:
        tokens = handle.read().split()
    if tokens[0] != b"P3":
        raise SystemExit("not an ASCII PPM: header is " + repr(tokens[0]))
    width, height, maxval = int(tokens[1]), int(tokens[2]), int(tokens[3])
    values = [int(t) for t in tokens[4:]]
    if len(values) != width * height * 3:
        raise SystemExit("expected %d samples, found %d"
                         % (width * height * 3, len(values)))
    if maxval != 255:
        raise SystemExit("only 8-bit samples are handled, got maxval %d" % maxval)
    return width, height, values


def write_png(path, width, height, values):
    raw = bytearray()
    for y in range(height):
        raw.append(0)                      # filter type 0: none
        raw += bytes(values[y * width * 3:(y + 1) * width * 3])

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    body = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))
    with open(path, "wb") as handle:
        handle.write(body)
    return len(body)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    w, h, vals = read_p3(src)
    size = write_png(dst, w, h, vals)
    print("wrote %s  %dx%d  %d bytes" % (dst, w, h, size))
