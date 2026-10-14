"""HTML-siden som PDF-en skrives ut fra (og som kan forhåndsvises i nettleseren).

CSS-en er Silfer-notatenes CSS ordrett (Tripletex-CLI-ets mva-notater, 2026-10), med noen tillegg nederst:
statusklassene merknad/ikke, sentrering, uthevet avviksrad, nummerert liste og utskriftssikring.
`side()` gir samme skjelett som notatene: logo, h1, undertittel, innhold, bunntekst.
"""

from __future__ import annotations

import base64
import re

from . import modell, tema
from .tekst import dato_no, esc, hel, kr

# Notatenes CSS – ordrett.
CSS_NOTAT = """@page { size: A4; margin: 14mm 13mm; } body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; font-size: 9pt; }
.topp { display: flex; align-items: center; gap: 14px; border-bottom: 2px solid #1B2E28; padding-bottom: 8px; } .topp img { height: 44px; }
h1 { font-size: 16pt; margin: 0; color: #1B2E28; } .under { color: #6B7280; font-size: 8.8pt; } h2 { font-size: 11pt; color: #1B2E28; margin: 14px 0 5px; } h3 { font-size: 9.8pt; color: #2D5A4A; margin: 10px 0 4px; }
table { width: 100%; border-collapse: collapse; margin-bottom: 5px; } th { background: #1B2E28; color: #fff; text-align: left; font-weight: 600; padding: 3px 5px; font-size: 8.4pt; }
td { padding: 2.5px 5px; border-bottom: 1px solid #D1D5DB; vertical-align: top; } .n { text-align: right; white-space: nowrap; }
.ok { color: #1B6E3D; background: #F0FAF4; font-weight: 600; text-align: center; } .avvik { color: #C0392B; background: #FFF0F0; font-weight: 600; text-align: center; }
.merk { color: #6B7280; font-size: 8pt; } .konkl { border: 1px solid #2D5A4A; background: #F0FAF4; padding: 8px 10px; margin-top: 8px; }
.varsel { border: 1px solid #D4760A; background: #FFF8EC; padding: 8px 10px; margin-top: 8px; } .liten td, .liten th { font-size: 7.6pt; padding: 1.5px 4px; }
.sideskift { page-break-before: always; } .nw { white-space: nowrap; } .bunn { margin-top: 14px; text-align: center; color: #6B7280; font-size: 8pt; }"""

# Tillegg (ikke i notatene).
CSS_TILLEGG = """td.merknad { color: #D4760A; background: #FFF8EC; font-weight: 600; text-align: center; } td.ikke { color: #6B7280; text-align: center; }
th.c, td.c { text-align: center; } tr.avvikrad td { background: #FFF0F0; } ol.punkter { margin: 4px 0 6px 18px; padding: 0; } .merk + .merk { margin-top: 2px; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; } thead { display: table-header-group; }
tr, .konkl, .varsel { page-break-inside: avoid; } h2, h3 { page-break-after: avoid; }
td.inn { padding-left: 14px; } tr.sumlinje td { border-top: 1px solid #1B2E28; } tr.gruppe td { padding-top: 7px; border-bottom: none; }"""

CSS = CSS_NOTAT + "\n" + CSS_TILLEGG


def _logo_b64() -> str | None:
    try:
        return base64.b64encode(tema.LOGO.read_bytes()).decode("ascii")
    except OSError:
        return None


def side(tittel: str, under: str, innhold: str, bunntekst: str, logo_b64: str | None = None) -> str:
    """Silfer-side: logo, tittel, undertittel og innhold (samme skjelett som notatene)."""
    logo_b64 = logo_b64 if logo_b64 is not None else _logo_b64()
    logo = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else ""
    return f"""<!doctype html><html lang="nb"><head><meta charset="utf-8"><title>{esc(tittel)}</title><style>{CSS}</style></head><body>
<div class="topp">{logo}<div><h1>{esc(tittel)}</h1><div class="under">{esc(under)}</div></div></div>
{innhold}
<div class="bunn">{esc(bunntekst)}</div></body></html>"""


def tekst_html(tekst: str) -> str:
    """Escaper og gjør **fet** til <b>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(tekst))


def overskrift(tekst: str, nivaa: int = 2) -> str:
    return f"<h{nivaa}>{esc(tekst)}</h{nivaa}>"


def avsnitt(tekst: str) -> str:
    return f"<p>{tekst_html(tekst)}</p>"


def merknad(tekst: str) -> str:
    return f'<div class="merk" style="margin-top:6px">{tekst_html(tekst)}</div>'


def punkter(liste: list[str]) -> str:
    return '<ol class="punkter">' + "".join(f"<li>{tekst_html(p)}</li>" for p in liste) + "</ol>"


def boks(type_: str, inner_html: str) -> str:
    return f'<div class="{"konkl" if type_ == "konkl" else "varsel"}">{inner_html}</div>'


def status_td(verdi, fet: bool = False) -> str:
    if verdi in (None, ""):
        return "<td></td>"
    klasse = tema.STATUS_KLASSE.get(str(verdi), "ikke")
    return f'<td class="{klasse}">{esc(verdi)}</td>'


def _celle(k: dict, c: modell.Celle | None, fet: bool) -> str:
    if c is None or c.verdi is None or c.verdi == "":
        return "<td></td>"
    typ = c.type or k["type"]
    v = c.verdi
    if typ == "status":
        return status_td(v)
    klasse = ""
    if typ == "belop":
        tekst, klasse = kr(v), "n"
    elif typ == "antall":
        tekst, klasse = hel(v), "n"
    elif typ == "prosent":
        tekst, klasse = kr(v, 1) + " %", "n"
    elif typ == "dato":
        tekst, klasse = dato_no(v), "nw"
    else:
        tekst = esc(v)
        if k["just"] == "r":
            klasse = "n"
        elif k["just"] == "c":
            klasse = "c"
    if c.fet if c.fet is not None else (fet and typ != "dato"):
        tekst = f"<b>{tekst}</b>"
    if c.dempet:
        tekst = f'<span class="merk">{tekst}</span>'
    if c.innrykk:
        klasse = (klasse + " inn").strip()
    return f'<td class="{klasse}">{tekst}</td>' if klasse else f"<td>{tekst}</td>"


def tabell(t: modell.Tabell) -> str:
    kol = [k for k in t.kolonner if k["vis"] in ("begge", "pdf")]
    hode = "".join(
        f'<th class="{"n" if k["just"] == "r" else "c"}">{esc(k["tekst"])}</th>' if k["just"] in ("r", "c")
        else f"<th>{esc(k['tekst'])}</th>" for k in kol)
    rader = []
    for r in t.rader:
        if r.vis == "excel":
            continue
        if r.art == "tom":
            c = r.celler.get(t.etikett_kol)
            celler = "".join(f"<td><i>{esc(c.verdi)}</i></td>" if k["id"] == t.etikett_kol else "<td></td>" for k in kol)
            rader.append(f"<tr>{celler}</tr>")
            continue
        celler = "".join(_celle(k, r.celler.get(k["id"]), r.fet) for k in kol)
        attr = ' class="avvikrad"' if t.uthev_avvik and r.art == "data" and modell.avvik_i(t, r) else ""
        if t.kilde == "oppstilling" and r.art in ("sum", "resultat", "gruppe"):
            attr = ' class="gruppe"' if r.art == "gruppe" else ' class="sumlinje"'
        rader.append(f"<tr{attr}>{celler}</tr>")
    klasse = ' class="liten"' if t.liten else ""
    return f"<table{klasse}><thead><tr>{hode}</tr></thead><tbody>\n" + "\n".join(rader) + "\n</tbody></table>"


def under_linje(dok: dict) -> str:
    return " | ".join(modell.under_deler(dok))


def render(spec: dict) -> str:
    """Hele dokumentet som HTML (validert spec)."""
    dok = spec["dokument"]
    deler = []
    for s in modell.los(spec):
        inn = []
        if s.overskrift:
            inn.append(overskrift(s.overskrift, s.nivaa))
        if s.tekst:
            inn.append(avsnitt(s.tekst))
        if s.tabell:
            inn.append(tabell(s.tabell))
        for b in s.bokser:
            inn.append(boks(b.type, tekst_html(b.tekst)))
        if s.punkter:
            inn.append(punkter(s.punkter))
        if s.merknad:
            inn.append(merknad(s.merknad))
        klasse = "seksjon sideskift" if s.sideskift else "seksjon"
        deler.append(f'<div class="{klasse}">\n' + "\n".join(inn) + "\n</div>")
    return side(dok["tittel"], under_linje(dok), "\n".join(deler), dok["bunntekst"])
