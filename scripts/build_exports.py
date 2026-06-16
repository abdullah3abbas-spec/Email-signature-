#!/usr/bin/env python3
"""
Build all GFF email-signature exports from the SINGLE approved design.

Source of truth : dist/email-signature.html  (table-based, inline CSS)
Logo            : dist/gff-logo.png           (extracted via scripts/extract-logo.sh)

Outputs (all the SAME design):
  dist/email-signature.png   high-res raster (2x)
  dist/email-signature.jpg   white background
  dist/email-signature.pdf   A4, signature centered
  dist/email-signature.svg   vector layout, employee text editable, logo embedded

Pipeline: WeasyPrint (HTML/CSS -> PDF, with Pango RTL Arabic shaping) +
poppler (pdftoppm) for rasterisation + ImageMagick (convert) for trim/JPG.
No browser required.

Requirements: python3-weasyprint, poppler-utils, imagemagick, and Arabic +
Latin fonts (Noto Sans Arabic, Liberation Sans).
"""
import base64
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SIG = os.path.join(DIST, "email-signature.html")
LOGO = os.path.join(DIST, "gff-logo.png")

# Brand colors (from GFF Brand Guidelines 2025_V01)
BLUE = "#00558C"   # Extra-time Blue  (name / accents / links)
TEAL = "#49C5B1"   # Stricker Teal    (dividers)
NAVY = "#043D56"   # Corporate Navy   (values)
STEEL = "#34677E"  # Steel Blue       (labels)


def sh(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def signature_markup():
    with open(SIG, encoding="utf-8") as f:
        return f.read()


def build_png_jpg():
    from weasyprint import HTML
    sig = signature_markup()
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>@page{size:600px 240px;margin:0}"
        "html,body{margin:0;padding:0;background:#ffffff}</style>"
        f"</head><body>{sig}</body></html>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "sig.pdf")
        HTML(string=doc, base_url=DIST + "/").write_pdf(pdf)
        # 192 DPI ~= 2x retina for a 96dpi/600px design
        sh(["pdftoppm", "-png", "-r", "192", "-f", "1", "-l", "1", pdf, os.path.join(tmp, "sig")])
        raw = os.path.join(tmp, "sig-1.png")
        png = os.path.join(DIST, "email-signature.png")
        sh(["convert", raw, "-fuzz", "1%", "-trim", "+repage",
            "-bordercolor", "white", "-border", "24", png])
        jpg = os.path.join(DIST, "email-signature.jpg")
        sh(["convert", png, "-background", "white", "-flatten", "-quality", "92", jpg])
    print("  PNG :", os.path.relpath(os.path.join(DIST, "email-signature.png"), ROOT))
    print("  JPG :", os.path.relpath(os.path.join(DIST, "email-signature.jpg"), ROOT))


def build_pdf():
    from weasyprint import HTML
    sig = signature_markup()
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>@page{size:A4;margin:18mm}"
        "html,body{margin:0;padding:0}"
        ".page{width:100%;height:261mm;border-collapse:collapse}"
        ".cell{vertical-align:middle;text-align:center}"
        ".sig{display:inline-block}"
        f".cap{{font-family:Arial,Helvetica,sans-serif;font-size:10px;color:{STEEL};"
        "text-align:center;padding-top:18px;letter-spacing:.4px}"
        "</style></head><body>"
        "<table class='page'><tr><td class='cell'>"
        f"<div class='sig'>{sig}"
        "<div class='cap'>Gulf Football Federation &middot; Official Email Signature</div>"
        "</div></td></tr></table>"
        "</body></html>"
    )
    out = os.path.join(DIST, "email-signature.pdf")
    HTML(string=doc, base_url=DIST + "/").write_pdf(out)
    print("  PDF :", os.path.relpath(out, ROOT))


def build_svg():
    """Hand-built vector mirror of the same layout: centered stacked AR/EN text
    on the left, a vertical teal divider, and the official logo on the right.
    Employee text = real <text> (editable). Official logo embedded as image."""
    with open(LOGO, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

    LATIN = "Arial, 'Liberation Sans', Helvetica, sans-serif"
    ARABIC = "Tahoma, 'Noto Sans Arabic', Arial, sans-serif"

    # Geometry: text column 28..343 (center 186), spacer, divider at x=361,
    # spacer, logo 381..571 (190 wide).
    TX = 186          # text-column center (text-anchor middle)
    DIV_X = 361       # vertical divider
    LOGO_X, LOGO_W = 381, 190
    LOGO_H = round(LOGO_W * 107 / 280)  # keep logo aspect ratio -> 73
    H = 200

    def ctext(y, size, color, s, weight="normal", family=LATIN, ls=None):
        extra = f' letter-spacing="{ls}"' if ls else ""
        return (f'<text x="{TX}" y="{y}" font-family="{family}" font-size="{size}" '
                f'font-weight="{weight}" fill="{color}" text-anchor="middle"{extra} '
                f'xml:space="preserve">{s}</text>')

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" '
                 'xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'width="600" height="{H}" viewBox="0 0 600 {H}" '
                 'font-family="Arial, sans-serif">')
    parts.append(f'<rect x="0" y="0" width="600" height="{H}" fill="#ffffff"/>')

    # ---- Centered stacked text: name, title, contacts ----
    parts.append(ctext(54, 20, BLUE, "عبدالله عباس", "bold", ARABIC))
    parts.append(ctext(76, 15, BLUE, "ABDULLAH ABBAS", "bold", LATIN, ls="0.4"))
    parts.append(ctext(100, 14, NAVY, "مصمم جرافيك", "normal", ARABIC))
    parts.append(ctext(118, 13, STEEL, "Graphic Designer", "normal", LATIN))
    parts.append(ctext(148, 13, NAVY, "+974 XXXXXXXX / +974 XXXXXXXX", "normal", LATIN))
    parts.append(ctext(170, 13, BLUE, "example@gff.org.qa", "normal", LATIN))

    # ---- Vertical brand divider ----
    parts.append(f'<rect x="{DIV_X}" y="30" width="2" height="148" fill="{TEAL}"/>')

    # ---- Logo (right, vertically centered) ----
    logo_y = round((H - LOGO_H) / 2)
    parts.append(f'<image x="{LOGO_X}" y="{logo_y}" width="{LOGO_W}" height="{LOGO_H}" '
                 f'xlink:href="data:image/png;base64,{logo_b64}"/>')

    parts.append('</svg>')
    out = os.path.join(DIST, "email-signature.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("  SVG :", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    print("Building GFF email-signature exports...")
    build_png_jpg()
    build_pdf()
    build_svg()
    print("Done.")
