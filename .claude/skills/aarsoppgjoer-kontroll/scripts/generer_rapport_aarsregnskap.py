"""
Genererer PDF-gjennomgangsrapport for årsregnskap (norske små foretak).
Silfer.no-branding med Poppins-font og Silfer-fargepalett.

Bruk:
    python generer_rapport.py <output_path> <data_json_path>
"""

import json
import sys
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonter (Poppins) ─────────────────────────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "poppins")
# Fallback: sjekk også standard plassering
if not os.path.exists(os.path.join(FONT_DIR, "Poppins-Regular.ttf")):
    FONT_DIR = "/sessions/relaxed-clever-faraday/fonts/poppins"

pdfmetrics.registerFont(TTFont("Poppins",         os.path.join(FONT_DIR, "Poppins-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Bold",     os.path.join(FONT_DIR, "Poppins-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Medium",   os.path.join(FONT_DIR, "Poppins-Medium.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-SemiBold", os.path.join(FONT_DIR, "Poppins-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Light",    os.path.join(FONT_DIR, "Poppins-Light.ttf")))

pdfmetrics.registerFontFamily(
    "Poppins",
    normal="Poppins",
    bold="Poppins-Bold",
)

# ── Silfer fargepalett ────────────────────────────────────────────────────────
SILFER_DARK    = colors.HexColor("#1B2E28")   # Mørk grønn fra logo
SILFER_BLACK   = colors.HexColor("#1A1A1A")   # Nesten svart
SILFER_GREEN   = colors.HexColor("#2D5A4A")   # Mellomgrønn
SILFER_ACCENT  = colors.HexColor("#0693E3")   # Cyan-blå aksent fra nettsiden
SILFER_LIGHT   = colors.HexColor("#F7F9F8")   # Lys bakgrunn
SILFER_BORDER  = colors.HexColor("#D4DDD8")   # Subtil ramme

RED_BG         = colors.HexColor("#FFF0F0")
RED_TEXT       = colors.HexColor("#C0392B")
ORANGE_BG      = colors.HexColor("#FFF8EC")
ORANGE_TEXT    = colors.HexColor("#D4760A")
GREEN_TEXT     = colors.HexColor("#1B6E3D")
GREEN_BG       = colors.HexColor("#F0FAF4")
GREY_TEXT      = colors.HexColor("#6B7280")
BLACK          = colors.HexColor("#1A1A1A")
WHITE          = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
W = PAGE_W - 2 * MARGIN   # tekstbredde

# ── Logo ──────────────────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "silfer_logo.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = "/sessions/relaxed-clever-faraday/silfer_logo.png"
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = "/tmp/silfer_logo.png"


# ── Stilar ────────────────────────────────────────────────────────────────────
def st(name, size, font="Poppins", color=BLACK, leading=None,
       sb=0, sa=4, align=TA_LEFT):
    return ParagraphStyle(
        name,
        fontName=font,
        fontSize=size, textColor=color,
        leading=leading or size * 1.4,
        spaceBefore=sb, spaceAfter=sa, alignment=align,
    )


S = {
    "title":     st("title",    16, font="Poppins-Bold",     color=SILFER_DARK),
    "subtitle":  st("sub",       9, font="Poppins",          color=GREY_TEXT),
    "h1":        st("h1",       12, font="Poppins-SemiBold", color=SILFER_DARK, sb=14, sa=4),
    "h2":        st("h2",        9, font="Poppins-SemiBold", color=SILFER_GREEN, sb=10, sa=4),
    "body":      st("body",      8.5, font="Poppins",        leading=14),
    "small":     st("small",     7.5, font="Poppins",        color=GREY_TEXT, leading=11),
    "hdr":       st("hdr",       7.5, font="Poppins-SemiBold", color=WHITE),
    "cell":      st("cell",      7.5, font="Poppins",        leading=11),
    "cellb":     st("cellb",     7.5, font="Poppins-Medium", leading=11),
    "ok":        st("ok",        7.5, font="Poppins-SemiBold", color=GREEN_TEXT, leading=11),
    "feil":      st("feil",      7.5, font="Poppins-SemiBold", color=RED_TEXT,   leading=11),
    "merknad":   st("merk",      7.5, font="Poppins-SemiBold", color=ORANGE_TEXT, leading=11),
    "ikke":      st("ikke",      7.5, font="Poppins",          color=GREY_TEXT,   leading=11),
    "footer":    st("footer",    7,   font="Poppins-Light",    color=GREY_TEXT, align=TA_CENTER),
    "tag_ok":    st("tag_ok",    7,   font="Poppins-SemiBold", color=GREEN_TEXT, leading=10),
    "tag_feil":  st("tag_feil",  7,   font="Poppins-SemiBold", color=RED_TEXT,   leading=10),
    "tag_merk":  st("tag_merk",  7,   font="Poppins-SemiBold", color=ORANGE_TEXT, leading=10),
    "tag_ikke":  st("tag_ikke",  7,   font="Poppins",          color=GREY_TEXT,   leading=10),
}

STATUS_STYLE = {
    "OK":           "ok",
    "FEIL":         "feil",
    "MANGLER":      "feil",
    "MERKNAD":      "merknad",
    "IKKE AKTUELT": "ikke",
}

CELL_PAD = [
    ("TOPPADDING",    (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
]


# ── Hjelpefunksjoner ─────────────────────────────────────────────────────────
def p(text, style="cell"):
    return Paragraph(str(text), S[style])


def header_row(cols, widths):
    row = [[p(c, "hdr") for c in cols]]
    t = Table(row, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), SILFER_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBELOW",     (0, 0), (-1, -1), 0, SILFER_DARK),
    ]))
    return t


def data_tbl(rows, widths):
    t = Table(rows, colWidths=widths)
    style = list(CELL_PAD) + [
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, SILFER_LIGHT]),
        ("LINEBELOW",      (0, 0), (-1, -1), 0.4, SILFER_BORDER),
        ("LINEAFTER",      (0, 0), (-2, -1), 0.3, SILFER_BORDER),
    ]
    t.setStyle(TableStyle(style))
    return t


def colored_tbl(rows, widths, bg):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle(list(CELL_PAD) + [
        ("BACKGROUND",  (0, 0), (-1, -1), bg),
        ("LINEBELOW",   (0, 0), (-1, -1), 0.4, SILFER_BORDER),
        ("LINEAFTER",   (0, 0), (-2, -1), 0.3, SILFER_BORDER),
    ]))
    return t


def status_p(val):
    sty = STATUS_STYLE.get(val.upper().strip(), "cell")
    return p(val, sty)


def section_line():
    return HRFlowable(width=W, thickness=1, color=SILFER_BORDER, spaceAfter=8)


# ── Hovudfunksjon ─────────────────────────────────────────────────────────────
def generer(output_path, data):
    story = []

    selskap = data.get("selskap", "Ukjent selskap")
    orgnr   = data.get("orgnr", "")
    aar     = data.get("aar", "")
    dato    = data.get("dato", "")

    # ── Header med logo ──────────────────────────────────────────────────────
    # Rad 1: Logo + tittel
    logo_img = None
    if os.path.exists(LOGO_PATH):
        logo_img = Image(LOGO_PATH, width=62*mm, height=19*mm)

    # Toppseksjon: Logo til venstre, info til høyre
    title_para = Paragraph(
        f"Gjennomgang av \u00e5rsregnskap {aar}",
        S["title"]
    )
    subtitle_para = Paragraph(
        f"{selskap}&nbsp;&nbsp;|&nbsp;&nbsp;Org.nr. {orgnr}&nbsp;&nbsp;|&nbsp;&nbsp;{dato}",
        S["subtitle"]
    )

    if logo_img:
        hdr_data = [
            [logo_img, title_para],
            ["",       subtitle_para],
        ]
        col_w = [66 * mm, W - 66 * mm]
        hdr_tbl = Table(hdr_data, colWidths=col_w, rowHeights=[22*mm, None])
        hdr_tbl.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("SPAN",          (0, 0), (0, 1)),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
    else:
        hdr_data = [
            [title_para],
            [subtitle_para],
        ]
        hdr_tbl = Table(hdr_data, colWidths=[W])
        hdr_tbl.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ]))

    story.append(hdr_tbl)
    story.append(HRFlowable(width=W, thickness=2, color=SILFER_DARK, spaceAfter=6))
    story.append(Spacer(1, 4))

    story.append(p(
        f"Rapporten oppsummerer gjennomgangen av noter, notehenvisninger, "
        f"noterekkef\u00f8lge og matematisk kontroll for \u00e5rsregnskapet til "
        f"{selskap} for regnskaps\u00e5ret {aar}. Alle funn er vurdert mot "
        f"regnskapsloven \u00a7\u00a7 7-35 til 7-46 og NRS 8.",
        "body"))
    story.append(Spacer(1, 10))

    # ── Del 1: Må rettes ─────────────────────────────────────────────────────
    story.append(p("1. Punkt som m\u00e5 rettes", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5, color=RED_TEXT, spaceAfter=8))

    maa = data.get("maa_rettes", [])
    if not maa:
        # Grønn boks: ingen funn
        ok_rows = [[p("\u2713  Ingen kritiske funn \u2013 regnskapet er klart for ferdigstilling.", "ok")]]
        ok_tbl = Table(ok_rows, colWidths=[W])
        ok_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GREEN_BG),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ]))
        story.append(ok_tbl)
    else:
        story.append(p(
            f"F\u00f8lgende punkt(er) er identifisert og m\u00e5 korrigeres "
            f"f\u00f8r regnskapet er klart:", "body"))
        story.append(Spacer(1, 6))
        w = [8*mm, 40*mm, W - 8*mm - 40*mm - 60*mm, 60*mm]
        story.append(header_row(["#", "Post / omr\u00e5de", "Funn", "Anbefalt rettelse"], w))
        rows = []
        for i, item in enumerate(maa, 1):
            rows.append([
                p(str(i), "feil"),
                p(item.get("post", ""), "cellb"),
                p(item.get("funn", ""), "cell"),
                p(item.get("rettelse", ""), "cell"),
            ])
        story.append(colored_tbl(rows, w, RED_BG))
    story.append(Spacer(1, 14))

    # ── Del 2: Utført kontroll ───────────────────────────────────────────────
    story.append(p("2. Oppsummering av utf\u00f8rt kontroll", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5, color=SILFER_GREEN, spaceAfter=8))

    # 2a Obligatoriske noter
    story.append(p("2a. Obligatoriske noter (\u00a7\u00a7 7-35 til 7-46 og NRS 8)", "h2"))
    w2a = [55*mm, 25*mm, W - 55*mm - 25*mm]
    story.append(header_row(["Krav", "Status", "Plassering"], w2a))
    rows = []
    for item in data.get("obligatoriske", []):
        rows.append([
            p(item.get("krav", ""), "cell"),
            status_p(item.get("status", "")),
            p(item.get("plassering", ""), "cell"),
        ])
    story.append(data_tbl(rows, w2a))
    story.append(Spacer(1, 10))

    # 2b Notehenvisninger
    story.append(p("2b. Notehenvisninger \u2013 poster i oppstillingene", "h2"))
    w2b = [30*mm, 45*mm, 30*mm, 25*mm]
    # Juster siste kolonne for å fylle bredden
    w2b[-1] = W - sum(w2b[:-1])
    story.append(header_row(["Oppstilling", "Post", "Note", "Status"], w2b))
    rows = []
    for item in data.get("notehenvisninger", []):
        rows.append([
            p(item.get("oppstilling", ""), "cell"),
            p(item.get("post", ""), "cell"),
            p(item.get("note", ""), "cell"),
            status_p(item.get("status", "")),
        ])
    story.append(data_tbl(rows, w2b))
    story.append(Spacer(1, 10))

    # 2c Noterekkefølge
    story.append(p("2c. Noterekkef\u00f8lge (\u00a7 7-1a)", "h2"))
    story.append(p(
        "\u00a7 7-1a krever at noter f\u00f8lger samme rekkef\u00f8lge som "
        "postene i oppstillingene. Resultatregnskapsnoter skal komme "
        "f\u00f8r balansenoter.", "body"))
    story.append(Spacer(1, 4))
    w2c = [22*mm, W - 22*mm - 25*mm, 25*mm]
    story.append(header_row(["Note", "Tilh\u00f8rende post(er)", "Status"], w2c))
    rows = []
    for item in data.get("noterekkef\u00f8lge", []):
        rows.append([
            p(item.get("note", ""), "cellb"),
            p(item.get("tilh\u00f8rende", ""), "cell"),
            status_p(item.get("status", "")),
        ])
    story.append(data_tbl(rows, w2c))
    story.append(Spacer(1, 10))

    # 2d Matematisk kontroll
    story.append(p("2d. Matematisk kontroll", "h2"))
    w2d = [42*mm, 50*mm, 28*mm, 22*mm]
    w2d[-1] = W - sum(w2d[:-1])
    story.append(header_row(["Kontroll", "Beregning", "Resultat", "Status"], w2d))
    rows = []
    for item in data.get("matematikk", []):
        rows.append([
            p(item.get("kontroll", ""), "cell"),
            p(item.get("beregning", ""), "cell"),
            p(item.get("resultat", ""), "cell"),
            status_p(item.get("status", "")),
        ])
    story.append(data_tbl(rows, w2d))
    merknad = data.get("matematikk_merknad", "")
    if merknad:
        story.append(Spacer(1, 3))
        story.append(p(f"* {merknad}", "small"))
    story.append(Spacer(1, 14))

    # 2e Kontroll av roller (Brønnøysundregistrene)
    rollesjekk = data.get("rollesjekk", [])
    if rollesjekk:
        story.append(p("2e. Kontroll av roller (Br\u00f8nn\u00f8ysundregistrene)", "h2"))
        story.append(p(
            "Styre og daglig leder i \u00e5rsregnskapet er sammenlignet med "
            "registrerte roller i Br\u00f8nn\u00f8ysundregistrene (data.brreg.no).",
            "body"))
        story.append(Spacer(1, 4))
        w2e = [30*mm, 45*mm, 45*mm, 22*mm]
        w2e[-1] = W - sum(w2e[:-1])
        story.append(header_row(["Rolle", "Iflg. Brreg", "Iflg. regnskap", "Status"], w2e))
        rows = []
        for item in rollesjekk:
            rows.append([
                p(item.get("rolle", ""), "cellb"),
                p(item.get("brreg", ""), "cell"),
                p(item.get("regnskap", ""), "cell"),
                status_p(item.get("status", "")),
            ])
        story.append(data_tbl(rows, w2e))
        story.append(Spacer(1, 10))

    story.append(Spacer(1, 4))

    # ── Bunntekst ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=SILFER_BORDER, spaceAfter=6))
    story.append(p(
        f"Gjennomgang utf\u00f8rt {dato}  |  "
        f"Grunnlag: Regnskapsloven \u00a7\u00a7 7-35\u20137-46 og NRS 8  |  "
        f"{selskap}, org.nr. {orgnr}",
        "footer"))

    # ── Bygg PDF ─────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f"Gjennomgang \u00e5rsregnskap {aar} \u2013 {selskap}",
        author="Silfer.no",
    )
    doc.build(story)
    print(f"PDF generert: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Bruk: python generer_rapport.py <output.pdf> <data.json>")
        sys.exit(1)
    with open(sys.argv[2], encoding="utf-8") as f:
        data = json.load(f)
    generer(sys.argv[1], data)
