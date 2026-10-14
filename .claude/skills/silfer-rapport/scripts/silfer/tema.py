"""Silfer-stilen som konstanter: farger, tallformater, statusmengde og stier.

Ingen tredjepartsimport her, slik at både Excel- og PDF-delen (og kompat-skallet `stil.py`) kan bruke modulen.
Farger står som ARGB (`FF…`): openpyxl fyller sekssifrede farger ut til `00RRGGBB`, og da endres XML-en.
"""

from __future__ import annotations

from pathlib import Path

# ── farger (ARGB for Excel; hex6() gir CSS-formen) ───────────────────────────
MORK = "FF1B2E28"          # mørk grønn fra logoen: titler, tabellhoder, strek
GRONN = "FF2D5A4A"         # mellomgrønn: seksjonslinjer, h3
GRA = "FF6B7280"           # undertittel, merknader
SVART = "FF1A1A1A"         # brødtekst
LYS = "FFF7F9F8"           # sebrastriper
RAMME = "FFD4DDD8"         # rammelinje i nye Excel-rapporter
RAMME_KOMPAT = "FFD1D5DB"  # rammen i lønnsrapporten (stil.py) og i CSS-en fra notatene
AKSENT = "FF0693E3"
HVIT = "FFFFFFFF"

OK_TEKST, OK_FYLL = "FF1B6E3D", "FFF0FAF4"
AVVIK_TEKST, AVVIK_FYLL = "FFC0392B", "FFFFF0F0"
FORKLART_TEKST, FORKLART_FYLL = "FFD4760A", "FFFFF8EC"

# ── tallformater (Excel) ──────────────────────────────────────────────────────
KRONER = "#,##0.00;[RED]\\-#,##0.00"
ANTALL = "#,##0;[RED]\\-#,##0"
DATO = "dd.mm.yyyy"
PROSENT = '0.0" %"'

# ── statusmengden (lukket) ────────────────────────────────────────────────────
# status → (tekstfarge, fyllfarge | None). Rekkefølgen er rekkefølgen på de betingede formatene i Excel.
STATUSER: dict[str, tuple[str, str | None]] = {
    "OK": (OK_TEKST, OK_FYLL),
    "AVVIK": (AVVIK_TEKST, AVVIK_FYLL),
    "FORKLART": (FORKLART_TEKST, FORKLART_FYLL),
    "PERIODISERT": (FORKLART_TEKST, FORKLART_FYLL),
    "FEIL": (AVVIK_TEKST, AVVIK_FYLL),
    "MANGLER": (AVVIK_TEKST, AVVIK_FYLL),
    "MERKNAD": (FORKLART_TEKST, FORKLART_FYLL),
    "KJENT": (FORKLART_TEKST, FORKLART_FYLL),        # kjent avvik, uendret beløp (funn-formatet)
    "IKKE AKTUELT": (GRA, None),
    "IKKE AVKLART": (GRA, None),                     # funn-formatet
}
STATUSER_ORDNET = tuple(STATUSER)
KOMPAT_FIRE = ("OK", "AVVIK", "FORKLART", "PERIODISERT")  # stil.py: fire regler i denne rekkefølgen

# CSS-klasse per status i HTML/PDF (ok/avvik fra notatene, merknad/ikke er tillegg)
STATUS_KLASSE = {
    "OK": "ok", "AVVIK": "avvik", "FEIL": "avvik", "MANGLER": "avvik",
    "FORKLART": "merknad", "PERIODISERT": "merknad", "MERKNAD": "merknad", "KJENT": "merknad",
    "IKKE AKTUELT": "ikke", "IKKE AVKLART": "ikke",
}

# ── kolonnetyper ──────────────────────────────────────────────────────────────
TYPER = ("tekst", "heltall", "dato", "belop", "antall", "prosent", "status")
STANDARD_BREDDE = {"tekst": 24, "heltall": 9, "dato": 12, "belop": 14, "antall": 10, "prosent": 9, "status": 13}
STANDARD_JUST = {"tekst": "l", "heltall": "l", "dato": "l", "belop": "r", "antall": "r", "prosent": "r", "status": "c"}

# ── stier ─────────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parents[2]   # .claude/skills/silfer-rapport
ASSETS = SKILL_DIR / "assets"
LOGO = ASSETS / "silfer_logo.png"

FORFATTER = "Silfer AS"


def hex6(argb: str) -> str:
    """'FF1B2E28' → '#1B2E28' (CSS)."""
    return "#" + argb[-6:]
