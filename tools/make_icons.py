#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Generate the Microsoft 365 app package icons from source, with no image library.

The app package requires a 192x192 colour icon and a 32x32 outline icon, and store validation
rejects a package that is missing either. Rather than commit two opaque binaries, this draws them:
a chevron pair on the Libre DevOps green, with the symbol inside the 120x120 safe region so the
hosts that crop the icon do not clip it.

The brand colour comes from a profile, so a rebranded package gets its own icons without anyone
opening an image editor. The default profile writes to assets/ (committed); any other profile
writes to build/<profile>/assets/ (gitignored).

Usage:
    uv run tools/make_icons.py                  # default profile
    uv run tools/make_icons.py --profile acme
    uv run tools/make_icons.py --color "#2563EB" --out-dir /tmp/icons
"""
from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
PROFILES = ROOT / "profiles"
BUILD = ROOT / "build"

DEFAULT_BRAND = "#15803D"  # Libre DevOps green-700
WHITE = (0xFF, 0xFF, 0xFF)


def parse_hex(value: str) -> tuple[int, int, int]:
    text = value.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"expected #RRGGBB, got {value!r}")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

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


def generate(dest: Path, brand_hex: str) -> None:
    """Write both icons into `dest`, using `brand_hex` as the colour icon background."""
    dest.mkdir(parents=True, exist_ok=True)
    brand = parse_hex(brand_hex)

    # Colour icon: 192x192, solid brand background, symbol inside the 120x120 safe region.
    write_png(dest / "color.png", 192, 192, render(192, 120, brand))

    # Outline icon: 32x32, white symbol on a transparent background. Validation forbids extra
    # padding, so the safe box is oversized to push the glyph out to the canvas edge.
    write_png(dest / "outline.png", 32, 32, render(32, 46, None))


def profile_colour(name: str) -> str:
    """Read the accent colour out of a profile without importing a YAML library."""
    path = PROFILES / f"{name}.yaml"
    if not path.is_file():
        raise SystemExit(f"profile not found: profiles/{name}.yaml")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("accent_color:"):
            return stripped.split(":", 1)[1].strip().strip("\"'")
    raise SystemExit(f"profiles/{name}.yaml has no package.accent_color")


def main() -> int:
    parser = argparse.ArgumentParser(description="Draw the app package icons.")
    parser.add_argument("--profile", default="default", help="branding profile to take the colour from")
    parser.add_argument("--color", help="override the brand colour, as #RRGGBB")
    parser.add_argument("--out-dir", help="override the output directory")
    args = parser.parse_args()

    colour = args.color or (DEFAULT_BRAND if args.profile == "default" else profile_colour(args.profile))
    if args.out_dir:
        dest = Path(args.out_dir)
    else:
        dest = ASSETS if args.profile == "default" else BUILD / args.profile / "assets"

    try:
        generate(dest, colour)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    shown = dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest
    for name in ("color.png", "outline.png"):
        print(f"  wrote {shown}/{name} ({(dest / name).stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
