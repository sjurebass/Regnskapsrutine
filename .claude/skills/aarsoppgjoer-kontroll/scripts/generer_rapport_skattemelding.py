"""
generer_rapport.py – Skattemeldingskontroll PDF-rapport med Silfer-branding
Poppins-font, Silfer-fargepalett og Silfer-logo.

Bruk:
    python generer_rapport.py /sti/rapport_data.json /sti/output.pdf

Krever: pip install reportlab --break-system-packages
"""

import json, sys, os, datetime
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

# ── Fonter (Poppins) ──────────────────────────────────────────────────────────
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR  = os.path.join(SKILL_DIR, "..", "fonts", "poppins")

# Fallback: bruk Silfer-skills fonter
if not os.path.exists(os.path.join(FONT_DIR, "Poppins-Regular.ttf")):
    FONT_DIR = os.path.join(
        os.path.dirname(SKILL_DIR),
        "..", ".skills", "skills", "arsregnskap-gjennomgang", "fonts", "poppins"
    )
if not os.path.exists(os.path.join(FONT_DIR, "Poppins-Regular.ttf")):
    # Absolutt fallback
    FONT_DIR = "/sessions/upbeat-zen-goodall/mnt/.skills/skills/arsregnskap-gjennomgang/fonts/poppins"

pdfmetrics.registerFont(TTFont("Poppins",         os.path.join(FONT_DIR, "Poppins-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Bold",     os.path.join(FONT_DIR, "Poppins-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Medium",   os.path.join(FONT_DIR, "Poppins-Medium.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-SemiBold", os.path.join(FONT_DIR, "Poppins-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Light",    os.path.join(FONT_DIR, "Poppins-Light.ttf")))
pdfmetrics.registerFontFamily("Poppins", normal="Poppins", bold="Poppins-Bold")

# ── Silfer fargepalett ────────────────────────────────────────────────────────
SILFER_DARK   = colors.HexColor("#1B2E28")
SILFER_BLACK  = colors.HexColor("#1A1A1A")
SILFER_GREEN  = colors.HexColor("#2D5A4A")
SILFER_ACCENT = colors.HexColor("#0693E3")
SILFER_LIGHT  = colors.HexColor("#F7F9F8")
SILFER_BORDER = colors.HexColor("#D4DDD8")

RED_BG        = colors.HexColor("#FFF0F0")
RED_TEXT      = colors.HexColor("#C0392B")
GREEN_BG      = colors.HexColor("#F0FAF4")
GREEN_TEXT    = colors.HexColor("#1B6E3D")
ORANGE_BG     = colors.HexColor("#FFF8EC")
ORANGE_TEXT   = colors.HexColor("#D4760A")
GREY_TEXT     = colors.HexColor("#6B7280")
BLACK         = colors.HexColor("#1A1A1A")
WHITE         = colors.white

# ── Logo ──────────────────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(SKILL_DIR, "..", "silfer_logo.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = "/sessions/upbeat-zen-goodall/mnt/.skills/skills/arsregnskap-gjennomgang/silfer_logo.png"

# ── Sideoppsett ───────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
W = PAGE_W - 2 * MARGIN

# ── Stilar ────────────────────────────────────────────────────────────────────
def st(name, size, font="Poppins", color=BLACK, leading=None, sb=0, sa=4, align=TA_LEFT):
    return ParagraphStyle(name, fontName=font, fontSize=size,
        textColor=color, leading=leading or size * 1.4,
        spaceBefore=sb, spaceAfter=sa, alignment=align)

S = {
    "title":    st("title",   16, "Poppins-Bold",     SILFER_DARK),
    "subtitle": st("sub",      9, "Poppins",           GREY_TEXT),
    "h1":       st("h1",      12, "Poppins-SemiBold",  SILFER_DARK,  sb=14, sa=4),
    "h2":       st("h2",       9, "Poppins-SemiBold",  SILFER_GREEN, sb=10, sa=4),
    "body":     st("body",     8.5, "Poppins",          leading=14),
    "small":    st("small",    7.5, "Poppins",          GREY_TEXT,   leading=11),
    "hdr":      st("hdr",      7.5, "Poppins-SemiBold", WHITE),
    "cell":     st("cell",     7.5, "Poppins",          leading=11),
    "cellb":    st("cellb",    7.5, "Poppins-Medium",   leading=11),
    "cellr":    st("cellr",    7.5, "Poppins",          leading=11, align=TA_RIGHT),
    "cellbr":   st("cellbr",   7.5, "Poppins-Medium",   leading=11, align=TA_RIGHT),
    "ok":       st("ok",       7.5, "Poppins-SemiBold", GREEN_TEXT,  leading=11),
    "feil":     st("feil",     7.5, "Poppins-SemiBold", RED_TEXT,    leading=11),
    "merknad":  st("merk",     7.5, "Poppins-SemiBold", ORANGE_TEXT, leading=11),
    "ikke":     st("ikke",     7.5, "Poppins",          GREY_TEXT,   leading=11),
    "footer":   st("footer",   7,   "Poppins-Light",    GREY_TEXT,   align=TA_CENTER),
}

CELL_PAD = [
    ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING",   (0, 0), (-1, -1), 7),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
]

# ── Hjelpefunksjoner ──────────────────────────────────────────────────────────
def p(text, style="cell"):
    return Paragraph(str(text), S[style])

def fmt(n):
    if n is None: return "–"
    try:
        f = float(n)
        s = f"{abs(f):,.0f}".replace(",", "\u202f")
        return f"−{s}" if f < 0 else s
    except: return str(n)

def status_p(ok, missing=False):
    if missing: return p("Ikke funnet", "merknad")
    return p("✓ OK", "ok") if ok else p("✗ AVVIK", "feil")

def header_row(cols, widths):
    row = [[p(c, "hdr") for c in cols]]
    t = Table(row, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), SILFER_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ]))
    return t

def data_tbl(rows_data, widths, highlight_rows=None):
    """highlight_rows: dict {row_idx: color}"""
    t = Table(rows_data, colWidths=widths)
    style = list(CELL_PAD) + [
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, SILFER_LIGHT]),
        ("LINEBELOW",      (0, 0), (-1, -1), 0.4, SILFER_BORDER),
        ("LINEAFTER",      (0, 0), (-2, -1), 0.3, SILFER_BORDER),
    ]
    if highlight_rows:
        for idx, bg in highlight_rows.items():
            style.append(("BACKGROUND", (0, idx), (-1, idx), bg))
    t.setStyle(TableStyle(style))
    return t

def sum_row_style(t_style, idx):
    t_style.append(("BACKGROUND",  (0, idx), (-1, idx), SILFER_LIGHT))
    t_style.append(("FONTNAME",    (0, idx), (-1, idx), "Poppins-SemiBold"))
    t_style.append(("LINEABOVE",   (0, idx), (-1, idx), 0.8, SILFER_DARK))

def section_line(thick=1, color=None):
    return HRFlowable(width=W, thickness=thick, color=color or SILFER_BORDER, spaceAfter=8)

# ── Hovudfunksjon ─────────────────────────────────────────────────────────────
def generer_rapport(data: dict, output_path: str):
    story = []

    selskap      = data.get("selskap", "Ukjent selskap")
    aar          = data.get("aar", "2025")
    dato         = data.get("dato", datetime.date.today().strftime("%d.%m.%Y"))
    pnr          = data.get("partsnummer_xml", "")
    forrige_aar  = str(int(aar) - 1)

    # ── HEADER ────────────────────────────────────────────────────────────────
    title_p = p(f"Skattemeldingskontroll {aar}", "title")
    sub_p   = p(f"{selskap}&nbsp;&nbsp;|&nbsp;&nbsp;Org.nr.&nbsp;{pnr}&nbsp;&nbsp;|&nbsp;&nbsp;{dato}", "subtitle")

    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=62*mm, height=19*mm)
        hdr = Table([[logo, title_p], ["", sub_p]],
                    colWidths=[66*mm, W - 66*mm], rowHeights=[22*mm, None])
        hdr.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("SPAN",          (0, 0), (0, 1)),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
    else:
        hdr = Table([[title_p], [sub_p]], colWidths=[W])

    story.append(hdr)
    story.append(HRFlowable(width=W, thickness=2, color=SILFER_DARK, spaceAfter=6))
    story.append(Spacer(1, 4))

    story.append(p(
        f"Kontrollen sammenligner utgående balanse (UB) i innsendt "
        f"{forrige_aar}-skattemelding (XML) mot inngående balanse (IB) i "
        f"{aar}-utkastet, og verifiserer skatteberegningen.",
        "body"))
    story.append(Spacer(1, 10))

    # ── OPPSUMMERING ──────────────────────────────────────────────────────────
    ib_kontroll_raw = data.get("ib_kontroll", [])
    # Filtrer bort poster der IB ikke er funnet (ok=None) – kan ikke kontrolleres
    ib_kontroll   = [r for r in ib_kontroll_raw if r.get("ok") is not None]
    midl_kontroll = data.get("midl_kontroll", [])
    ek_kontroll   = data.get("ek_kontroll", {})
    und_kontroll  = data.get("und_kontroll", {})
    skatt_rader   = data.get("skatt_rader", [])

    ib_ok    = all(r["ok"] for r in ib_kontroll) if ib_kontroll else True
    midl_ok  = all(r["ok"] for r in midl_kontroll if r.get("har_ib") and r.get("ib_forskjell") is not None)
    ek_ok    = ek_kontroll.get("ok", True)
    und_ok   = und_kontroll.get("ok", True)
    skatt_ok = all(r["ok"] for r in skatt_rader if r.get("oppgitt") is not None)
    alle_ok  = ib_ok and midl_ok and ek_ok and und_ok and skatt_ok

    ib_ok_n  = sum(1 for r in ib_kontroll if r["ok"])
    ib_n     = len(ib_kontroll)

    story.append(p("Oppsummering", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5, color=SILFER_GREEN, spaceAfter=8))

    ops_data = [
        (f"Balanse IB/UB ({ib_ok_n}/{ib_n} poster)", ib_ok),
        ("Midlertidige forskjeller IB/UB",            midl_ok),
        ("Egenkapitalavstemming IB/UB",                ek_ok),
        ("Fremførbart underskudd IB/UB",               und_ok),
        ("Skatteberegning",                            skatt_ok),
    ]
    ow = [W - 30*mm, 30*mm]
    story.append(header_row(["Kontroll", "Status"], ow))
    ops_rows = []
    for label, ok in ops_data:
        ops_rows.append([p(label, "cell"), status_p(ok)])
    hl = {i: RED_BG for i, (_, ok) in enumerate(ops_data) if not ok}
    story.append(data_tbl(ops_rows, ow, hl))

    # Konklusjonsboks
    story.append(Spacer(1, 8))
    if alle_ok:
        konkl_bg  = GREEN_BG
        konkl_txt = p(f"✓  Ingen avvik funnet – skattemeldingen for {aar} er klar for innsending.", "ok")
    else:
        konkl_bg  = RED_BG
        konkl_txt = p(f"✗  Avvik funnet – se detaljer nedenfor. Må rettes før innsending.", "feil")

    kb = Table([[konkl_txt]], colWidths=[W])
    kb.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), konkl_bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
    ]))
    story.append(kb)
    story.append(Spacer(1, 16))

    # ═══════════════════════════════════════════════════════════════════════════
    # DEL 1 – BALANSE IB/UB
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(p("Del 1 – Balanse IB/UB-kontroll", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5,
        color=RED_TEXT if not ib_ok else SILFER_GREEN, spaceAfter=8))
    story.append(p(
        f"Utgående balanse (UB) fra innsendt {forrige_aar}-skattemelding (XML) "
        f"sammenlignes mot inngående balanse (IB) i {aar}-utkastet.",
        "body"))
    story.append(Spacer(1, 4))

    bw = [22*mm, W - 22*mm - 34*mm - 34*mm - 24*mm, 34*mm, 34*mm, 24*mm]
    story.append(header_row(
        ["Kode", "Post", f"UB {forrige_aar}", f"IB {aar}", "Avvik"], bw))
    b_rows = []
    hl_b   = {}
    for i, r in enumerate(ib_kontroll):
        er_sum  = r.get("er_sum", False)
        avvik   = not r["ok"]
        ib_val  = fmt(r["ib_2025"]) if r["ib_2025"] is not None else "Ikke funnet"
        diff_v  = fmt(r["diff"]) if r["diff"] is not None else "–"
        kode    = r["kode"] if not er_sum else ""
        style_n = "cellb" if er_sum else "cell"
        style_r = "cellbr" if er_sum else "cellr"
        b_rows.append([
            p(kode,   style_n),
            p(r["navn"], style_n),
            p(fmt(r["ub_2024"]), style_r),
            p(ib_val,  style_r),
            p(diff_v,  "feil" if avvik else style_r),
        ])
        if avvik:    hl_b[i] = RED_BG
        elif er_sum: hl_b[i] = SILFER_LIGHT

    if b_rows:
        story.append(data_tbl(b_rows, bw, hl_b))
    else:
        story.append(p("Ingen balanseposter å kontrollere (nystiftet – ingen innsendt 2024-skattemelding).", "small"))
    story.append(Spacer(1, 16))

    # ═══════════════════════════════════════════════════════════════════════════
    # DEL 2 – MIDLERTIDIGE FORSKJELLER
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(p("Del 2 – Midlertidige forskjeller IB/UB-kontroll", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5,
        color=RED_TEXT if not midl_ok else SILFER_GREEN, spaceAfter=8))

    if not midl_kontroll:
        story.append(p("Ingen midlertidige forskjeller i innsendt skattemelding.", "small"))
    else:
        mw = [W - 34*mm - 34*mm - 28*mm - 24*mm, 34*mm, 34*mm, 28*mm, 24*mm]
        story.append(header_row(
            ["Type", f"Forskjell UB {forrige_aar}", f"Forskjell IB {aar}", "Avvik", "Status"], mw))
        m_rows = []
        hl_m   = {}
        for i, r in enumerate(midl_kontroll):
            avvik  = not r["ok"]
            ib_val = fmt(r["ib_forskjell"]) if r.get("har_ib") and r["ib_forskjell"] is not None else "–"
            diff_v = fmt(r["diff"]) if r.get("diff") is not None else "–"
            st_p   = status_p(r["ok"]) if r.get("har_ib") and r.get("ib_forskjell") is not None else p("–", "ikke")
            m_rows.append([
                p(r["type"], "cell"),
                p(fmt(r["ub_forskjell"]), "cellr"),
                p(ib_val, "cellr"),
                p(diff_v, "feil" if avvik else "cellr"),
                st_p,
            ])
            if avvik: hl_m[i] = RED_BG

        # Sum-rad
        sum_ub = data.get("sum_midl_ub_xml", 0)
        sum_ib = data.get("sum_midl_ib_pdf")
        sum_ok = data.get("sum_midl_ok", True)
        sum_ib_txt = fmt(sum_ib) if sum_ib is not None else "Ikke funnet"
        sum_diff = fmt(round(sum_ib - sum_ub, 2)) if sum_ib is not None else "–"
        m_rows.append([
            p("Sum midlertidige forskjeller", "cellb"),
            p(fmt(sum_ub), "cellbr"),
            p(sum_ib_txt, "cellbr"),
            p(sum_diff, "feil" if not sum_ok else "cellbr"),
            status_p(sum_ok),
        ])
        if not sum_ok: hl_m[len(m_rows) - 1] = RED_BG
        else:          hl_m[len(m_rows) - 1] = SILFER_LIGHT

        story.append(data_tbl(m_rows, mw, hl_m))
    story.append(Spacer(1, 16))

    # ═══════════════════════════════════════════════════════════════════════════
    # DEL 3 – EGENKAPITALAVSTEMMING
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(p("Del 3 – Egenkapitalavstemming IB/UB-kontroll", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5,
        color=RED_TEXT if not ek_ok else SILFER_GREEN, spaceAfter=8))

    ek_ub  = ek_kontroll.get("utgaaende_ek_xml")
    ek_ib  = ek_kontroll.get("ib_ek_pdf")
    ek_ok_ = ek_kontroll.get("ok", True)

    ew = [W - 34*mm - 34*mm - 24*mm, 34*mm, 34*mm, 24*mm]
    story.append(header_row(
        ["Post", f"UB {forrige_aar} (XML)", f"IB {aar} (kilde)", "Status"], ew))
    ib_txt = fmt(ek_ib) if ek_ib is not None else "Ikke funnet"
    e_rows = [[
        p("Egenkapital (egenkapitalavstemming)", "cell"),
        p(fmt(ek_ub), "cellr"),
        p(ib_txt, "cellr"),
        status_p(ek_ok_, missing=ek_ib is None),
    ]]
    story.append(data_tbl(e_rows, ew, {0: RED_BG} if not ek_ok_ else {}))

    # Egenkapitalendringer
    endringer = data.get("ek_endringer_xml", [])
    if endringer:
        story.append(Spacer(1, 6))
        story.append(p(f"Egenkapitalendringer {forrige_aar} (fra XML, til informasjon):", "h2"))
        for e in endringer:
            story.append(p(f"  • {e.get('type', '')}: {fmt(e.get('beloep'))} kr", "small"))
    story.append(Spacer(1, 16))

    # ═══════════════════════════════════════════════════════════════════════════
    # DEL 4 – FREMFØRBART UNDERSKUDD
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(p("Del 4 – Fremførbart underskudd IB/UB-kontroll", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5,
        color=RED_TEXT if not und_ok else SILFER_GREEN, spaceAfter=8))

    und_ub = und_kontroll.get("ub_xml", 0)
    und_ib = und_kontroll.get("ib_pdf")
    und_ok_ = und_kontroll.get("ok", True)

    uw = [W - 34*mm - 34*mm - 24*mm, 34*mm, 34*mm, 24*mm]
    story.append(header_row(
        ["Post", f"UB {forrige_aar} (XML)", f"IB {aar} (kilde)", "Status"], uw))
    und_ib_txt = fmt(und_ib) if und_ib is not None else ("0" if und_ub == 0 else "Ikke funnet")
    u_rows = [[
        p("Fremførbart underskudd", "cell"),
        p(fmt(und_ub), "cellr"),
        p(und_ib_txt, "cellr"),
        status_p(und_ok_, missing=(und_ub > 0 and und_ib is None)),
    ]]
    story.append(data_tbl(u_rows, uw, {0: RED_BG} if not und_ok_ else {}))
    story.append(Spacer(1, 16))

    # ═══════════════════════════════════════════════════════════════════════════
    # DEL 5 – PERMANENTE FORSKJELLER (informasjon)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(p("Del 5 – Permanente forskjeller (til informasjon)", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5, color=SILFER_GREEN, spaceAfter=8))
    story.append(p(
        "Permanente forskjeller reverseres ikke mellom år og har ingen IB/UB. "
        "Tabellen viser postene for begge år til sammenligning.",
        "body"))
    story.append(Spacer(1, 4))

    pf_2024 = data.get("permanente_forskjeller_2024", [])
    pf_2025 = data.get("permanente_forskjeller_2025", [])

    if pf_2024 or pf_2025:
        pw = [W - 34*mm - 34*mm, 34*mm, 34*mm]
        story.append(header_row(["Type", f"{forrige_aar} (XML)", f"{aar} (kilde)"], pw))
        alle_typer = sorted(set([p_["id"] for p_ in pf_2024] + [p_["id"] for p_ in pf_2025]))
        pf24 = {p_["id"]: p_["beloep"] for p_ in pf_2024}
        pf25 = {p_["id"]: p_["beloep"] for p_ in pf_2025}
        pf_rows = []
        for t in alle_typer:
            pf_rows.append([
                p(t, "cell"),
                p(fmt(pf24.get(t)), "cellr"),
                p(fmt(pf25.get(t)), "cellr"),
            ])
        story.append(data_tbl(pf_rows, pw))
    else:
        story.append(p("Ingen permanente forskjeller registrert.", "small"))
    story.append(Spacer(1, 16))

    # ═══════════════════════════════════════════════════════════════════════════
    # DEL 6 – SKATTEBEREGNING
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(p("Del 6 – Kontroll av skatteberegning (22 %)", "h1"))
    story.append(HRFlowable(width=W, thickness=1.5,
        color=RED_TEXT if not skatt_ok else SILFER_GREEN, spaceAfter=8))

    sw = [W - 34*mm - 34*mm - 24*mm, 34*mm, 34*mm, 24*mm]
    story.append(header_row(
        ["Post", "Beregnet (22 %)", "Oppgitt i kilde", "Status"], sw))
    s_rows = []
    hl_s   = {}
    for i, r in enumerate(skatt_rader):
        avvik  = not r["ok"]
        oppgitt = fmt(r["oppgitt"]) if r.get("oppgitt") is not None else "–"
        st_p   = status_p(r["ok"]) if r.get("oppgitt") is not None else p("–", "ikke")
        s_rows.append([
            p(r["post"], "cell"),
            p(fmt(r["beregnet"]), "cellr"),
            p(oppgitt, "cellr"),
            st_p,
        ])
        if avvik: hl_s[i] = RED_BG
    story.append(data_tbl(s_rows, sw, hl_s))

    # Beregningsforklaring
    bk = data.get("skatt_grunnlag", {})
    br = data.get("beregnet_skatt", {})
    ski   = bk.get("skattepliktig_inntekt", 0)
    mf_ib = bk.get("mid_forskjeller_ib", 0)
    mf_ub = bk.get("mid_forskjeller_ub", 0)

    story.append(Spacer(1, 8))
    story.append(p("Beregningsforklaring:", "h2"))
    forklaring = [
        f"Skattepliktig inntekt {aar}: {fmt(ski)} kr",
        f"Midlertidige forskjeller IB {aar}: {fmt(mf_ib)} kr",
        f"Midlertidige forskjeller UB {aar}: {fmt(mf_ub)} kr",
        f"Betalbar skatt: max(0, {fmt(ski)}) × 22 % = {fmt(br.get('betalbar_skatt'))} kr",
        f"Endring utsatt skatt: {fmt(br.get('utsatt_skatt_ub'))} − {fmt(br.get('utsatt_skatt_ib'))} = {fmt(br.get('endring_utsatt_skatt'))} kr",
        f"Total skattekostnad: {fmt(br.get('betalbar_skatt'))} + {fmt(br.get('endring_utsatt_skatt'))} = {fmt(br.get('total_skattekostnad'))} kr",
    ]
    for linje in forklaring:
        story.append(p(f"  • {linje}", "small"))
    story.append(Spacer(1, 16))

    # ── BUNNTEKST ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=SILFER_BORDER, spaceAfter=6))
    story.append(p(
        f"Generert {dato}&nbsp;&nbsp;|&nbsp;&nbsp;{selskap}, org.nr. {pnr}"
        f"&nbsp;&nbsp;|&nbsp;&nbsp;Kun beregnet skatt – ikke juridisk rådgivning",
        "footer"))

    # ── BYGG PDF ─────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f"Skattemeldingskontroll {aar} – {selskap}",
        author="Silfer.no",
    )
    doc.build(story)
    print(f"PDF generert: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Bruk: python generer_rapport.py /sti/rapport_data.json /sti/output.pdf",
              file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    generer_rapport(d, sys.argv[2])
