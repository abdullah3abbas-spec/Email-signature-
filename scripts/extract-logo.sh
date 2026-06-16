#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Extract the official GFF full-color master corporate logo from the brand
# guidelines PDF (page 15, top lockup) into a clean high-resolution PNG.
#
# The logo is stored as VECTOR art inside the PDF, so we render the page at a
# high DPI and crop the logo region with poppler's pdftoppm. No design tools
# are required. Crop coordinates were validated against page 15 at 150 DPI and
# are scaled here to 600 DPI for a crisp asset.
#
# Requirements: poppler-utils (pdftoppm). Optional: ImageMagick (mogrify) to
# trim surrounding whitespace — skipped automatically if not installed.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF="${1:-$ROOT/assets/GFF_Brand_Guidelines.pdf}"
OUT="$ROOT/assets/gff-logo.png"

DPI=600
SCALE=4                      # 600 DPI / 150 DPI (coords were measured at 150)
X=$(( 1440 * SCALE ))
Y=$(( 600  * SCALE ))
W=$(( 1180 * SCALE ))
H=$(( 500  * SCALE ))

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pdftoppm -png -f 15 -l 15 -r "$DPI" -x "$X" -y "$Y" -W "$W" -H "$H" "$PDF" "$TMP/logo"
mv "$TMP"/logo*.png "$OUT"

# Trim uniform white border if ImageMagick is available (keeps a small margin).
if command -v mogrify >/dev/null 2>&1; then
  mogrify -trim +repage -bordercolor white -border 24 "$OUT"
fi

echo "Wrote $OUT"
identify "$OUT" 2>/dev/null || true
