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
        "<style>@page{size:600px 780px;margin:0}"
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
    """Hand-built vector mirror of the same layout.
    Employee text = real <text> (editable). Official logo embedded as image."""
    with open(LOGO, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

    PAD = 28
    RIGHT = 600 - PAD          # 572  (Arabic right edge)
    LEFT = PAD                 # 28   (English left edge / logo)
    LATIN = "Arial, 'Liberation Sans', Helvetica, sans-serif"
    ARABIC = "Tahoma, 'Noto Sans Arabic', Arial, sans-serif"

    def t(x, y, s, size, color, weight="normal", anchor="start", family=LATIN):
        # Arabic lines use text-anchor="end" (right edge) and let the Unicode
        # bidi algorithm order the glyphs RTL; LTR runs (numbers, email) are
        # wrapped in <tspan direction="ltr">. This renders correctly in
        # browsers, vector editors and librsvg/Pango.
        return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
                f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}" '
                f'xml:space="preserve">{s}</text>')

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" '
                 'xmlns:xlink="http://www.w3.org/1999/xlink" '
                 'width="600" height="540" viewBox="0 0 600 540" '
                 'font-family="Arial, sans-serif">')
    parts.append('<rect x="0" y="0" width="600" height="540" fill="#ffffff"/>')
    # Logo (embedded raster of the official full-color master lockup)
    parts.append(f'<image x="{LEFT}" y="24" width="280" height="107" '
                 f'xlink:href="data:image/png;base64,{logo_b64}"/>')
    # Brand divider under logo
    parts.append(f'<rect x="{LEFT}" y="147" width="544" height="2" fill="{TEAL}"/>')

    # ---- Arabic block (RTL via bidi, right-aligned at x=RIGHT) ----
    parts.append(t(RIGHT, 190, "عبدالله عباس", 20, BLUE, "bold", "end", ARABIC))
    parts.append(t(RIGHT, 214, "مصمم جرافيك", 14, BLUE, "normal", "end", ARABIC))
    parts.append(t(RIGHT, 246, '<tspan fill="%s">الجوال:</tspan> <tspan fill="%s" direction="ltr">+974 XXXXXXXX</tspan>' % (STEEL, NAVY), 13, NAVY, "normal", "end", ARABIC))
    parts.append(t(RIGHT, 270, '<tspan fill="%s">الهاتف:</tspan> <tspan fill="%s" direction="ltr">+974 XXXXXXXX</tspan>' % (STEEL, NAVY), 13, NAVY, "normal", "end", ARABIC))
    parts.append(t(RIGHT, 294, '<tspan fill="%s">البريد الإلكتروني:</tspan> <tspan fill="%s" direction="ltr">example@gff.org.qa</tspan>' % (STEEL, BLUE), 13, BLUE, "normal", "end", ARABIC))
    parts.append(t(RIGHT, 318, '<tspan fill="%s">ص.ب:</tspan> <tspan fill="%s">XXXX - الدوحة، قطر</tspan>' % (STEEL, NAVY), 13, NAVY, "normal", "end", ARABIC))

    # Divider between Arabic and English
    parts.append(f'<rect x="{LEFT}" y="346" width="544" height="1" fill="{TEAL}"/>')

    # ---- English block (LTR, left-aligned) ----
    parts.append(t(LEFT, 388, "Abdullah Abbas", 20, BLUE, "bold", "start", LATIN))
    parts.append(t(LEFT, 412, "Graphic Designer", 14, BLUE, "normal", "start", LATIN))
    parts.append(t(LEFT, 444, '<tspan fill="%s">Mobile:</tspan> <tspan fill="%s">+974 XXXXXXXX</tspan>' % (STEEL, NAVY), 13, NAVY, "normal", "start", LATIN))
    parts.append(t(LEFT, 468, '<tspan fill="%s">Tel:</tspan> <tspan fill="%s">+974 XXXXXXXX</tspan>' % (STEEL, NAVY), 13, NAVY, "normal", "start", LATIN))
    parts.append(t(LEFT, 492, '<tspan fill="%s">Email:</tspan> <tspan fill="%s">example@gff.org.qa</tspan>' % (STEEL, BLUE), 13, BLUE, "normal", "start", LATIN))
    parts.append(t(LEFT, 516, '<tspan fill="%s">P.O. Box:</tspan> <tspan fill="%s">XXXX - Doha, Qatar</tspan>' % (STEEL, NAVY), 13, NAVY, "normal", "start", LATIN))

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
