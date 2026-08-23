#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Generate the Microsoft 365 app package icons from source, with no image library.

The app package requires a 192x192 colour icon and a 32x32 outline icon, and store validation
rejects a package that is missing either. Rather than commit two opaque binaries, this draws them:
a chevron pair on the Libre DevOps green, with the symbol inside the 120x120 safe region so the
hosts that crop the icon do not clip it.

Usage:
    uv run tools/make_icons.py

Writes assets/color.png and assets/outline.png.
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

BRAND = (0x15, 0x80, 0x3D)  # Libre DevOps green-700
WHITE = (0xFF, 0xFF, 0xFF)

# Chevron pair "<>" in normalised coordinates, origin at the centre, half-extent 1.0.
STROKES = [
    ((-0.16, -0.46), (-0.58, 0.00)),
    ((-0.58, 0.00), (-0.16, 0.46)),
    ((0.16, -0.46), (0.58, 0.00)),
    ((0.58, 0.00), (0.16, 0.46)),
]
STROKE_WIDTH = 0.115
SUPERSAMPLE = 3


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def coverage(x: int, y: int, centre: float, scale: float) -> float:
    """Fraction of pixel (x, y) covered by the glyph.

    Subsamples are offset in PIXEL space and only then mapped into the glyph's normalised
    coordinates, so the sampling grid stays inside the pixel it belongs to.
    """
    hits = 0
    for sy in range(SUPERSAMPLE):
        for sx in range(SUPERSAMPLE):
            ox = (x + (sx + 0.5) / SUPERSAMPLE - centre) / scale
            oy = (y + (sy + 0.5) / SUPERSAMPLE - centre) / scale
            if any(distance_to_segment(ox, oy, *a, *b) <= STROKE_WIDTH for a, b in STROKES):
                hits += 1
    return hits / (SUPERSAMPLE * SUPERSAMPLE)


def write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (None)
        for x in range(width):
            raw.extend(pixels[y * width + x])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def render(size: int, safe: int, background: tuple[int, int, int] | None) -> list[tuple[int, int, int, int]]:
    """Draw the glyph scaled to `safe` pixels, centred on a `size` canvas."""
    pixels: list[tuple[int, int, int, int]] = []
    centre = size / 2.0
    scale = safe / 2.0
    for y in range(size):
        for x in range(size):
            alpha = coverage(x, y, centre, scale)
            if background is None:
                pixels.append((*WHITE, round(alpha * 255)))
            else:
                blended = tuple(
                    round(background[i] * (1 - alpha) + WHITE[i] * alpha) for i in range(3)
                )
                pixels.append((*blended, 255))
    return pixels


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)

    # Colour icon: 192x192, solid brand background, symbol inside the 120x120 safe region.
    write_png(ASSETS / "color.png", 192, 192, render(192, 120, BRAND))

    # Outline icon: 32x32, white symbol on a transparent background. Validation forbids extra
    # padding, so the safe box is oversized to push the glyph out to the canvas edge.
    write_png(ASSETS / "outline.png", 32, 32, render(32, 46, None))

    for name in ("color.png", "outline.png"):
        print(f"  wrote assets/{name} ({(ASSETS / name).stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
