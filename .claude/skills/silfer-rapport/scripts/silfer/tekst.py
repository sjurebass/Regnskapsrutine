"""Tekst og tall: rensing av banktekster, beløpstolking, maskering av personopplysninger og norsk formatering.

`clean_tekst`, `parse_amount` og `parse_raw` er flyttet uendret fra bankavstemmingens gamle `generer_excel.py`.
`kr`, `hel`, `dato_no` og `esc` gir samme resultat som `kr`, `hel`, `datoNo` og `esc` i notatene fra Tripletex-CLI-et.
"""

from __future__ import annotations

import datetime as _dt
import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

# ── Tekst-rensing ──────────────────────────────────────────────────────────
# Gjør rå bankbeskrivelser korte og lesbare for kunden. Eksempel:
#   "VisaVALUTAKURS: 11,0353 – EUR 126,50 GOOGLE:WORKSPACE E, 05469769..."
#   → "Google Workspace 126,50 EUR"
# Kjøres kun på råstrenger ("raw"); eksplisitt "tekst" i data.json røres ikke.
BETALINGSPREFIKS = (r"^\s*(?:Visa|Giro|Avtalegiro|Straksbetaling|Straksoverf\w+|"
                    r"Nettgiro|Nettbank|MobilePay|Vipps|Kort|Bankaxept)\s*")
VALUTA = "EUR|USD|GBP|SEK|DKK|CHF|PLN|JPY|CAD|AUD|NOK"
# Ord som skal beholde store bokstaver (selskapsformer, valuta, forkortelser)
# Selskapsformer/forkortelser som skal beholde store bokstaver. Anglo-former
# (Inc/Ltd/LLC/GmbH) utelates med vilje – de leses penere som «Inc.», «Ltd».
ACRONYMER = {"AS", "ASA", "A/S", "ANS", "DA", "BA", "SA", "NUF", "AB", "OY",
             "EUR", "USD", "GBP", "SEK", "DKK", "NOK", "CHF", "PLN", "JPY",
             "UK", "US", "EU", "IT", "AI", "VVS"}


def _cap_ord(w):
    up = w.upper()
    if up in ACRONYMER:
        return up
    if any(ch.isdigit() for ch in w):     # koder som 26_247480 – la stå
        return w
    if w.isupper() or w.islower():         # KUN helt caps/lower gjøres pene
        return w.capitalize()
    return w                               # blandet case (iZettle) – la stå


def clean_tekst(tekst):
    if not tekst:
        return tekst
    t = tekst.strip()
    # 1) fjern betalingstype-prefiks limt foran (VisaVALUTAKURS, GiroSTOREBRAND)
    t = re.sub(BETALINGSPREFIKS, "", t, flags=re.I)
    # 2) fjern valutakurs-støy
    t = re.sub(r"VALUTAKURS:?\s*[\d.,]+", " ", t, flags=re.I)
    # 3) trekk ut utenlandsk valutabeløp (EUR 126,50) og legg som suffiks til slutt
    cur = ""
    m = re.search(r"\b(" + VALUTA + r")\s+(\d[\d .]*,\d{2})", t, flags=re.I)
    if m:
        cur = f"{m.group(2).strip()} {m.group(1).upper()}"
        t = t.replace(m.group(0), " ")
    # 4) kutt bort merkelapp-haler (bilag/betaling/faktura/ref/detaljer m.m.)
    t = re.sub(r"(Bilag:|Betaling:|Betalingstype:|Detaljer:|Beskrivelse:|Annet:|"
               r"Melding:|KID:|Fakturanr|Faktura\s*nummer|Ref[:.]|Til\s+konto|"
               r"Fra\s+konto).*$", " ", t, flags=re.I)
    # 5) fjern norske kontonummer (1234 56 78901 / 1234.56.78901) og lange arkivnr
    t = re.sub(r"\b\d{4}[ .]\d{2}[ .]\d{5}\b", " ", t)
    t = re.sub(r",\s*\d{4,}.*$", " ", t)
    t = re.sub(r"\b\d{7,}\b", " ", t)
    # 6) fjern separatorer og skilletegn-støy
    t = re.sub(r"[|–]", " ", t)
    t = re.sub(r"\s[-]\s", " ", t)
    t = t.replace(":", " ").replace("*", " ").replace("_", " ")
    # 7) rydd whitespace og kant-tegn
    t = re.sub(r"\s+", " ", t).strip(" ,.-")
    # 8) dropp etterhengende ensom stor bokstav (f.eks. «Workspace E»)
    ord_ = t.split()
    if len(ord_) >= 2 and re.fullmatch(r"[A-ZÆØÅ]", ord_[-1]):
        ord_ = ord_[:-1]
    # dropp etterhengende løs preposisjon/konjunksjon (f.eks. «Plasseringskonto Fra»)
    STOPP = {"fra", "til", "og", "for", "med", "av", "på"}
    while len(ord_) >= 2 and ord_[-1].lower() in STOPP:
        ord_ = ord_[:-1]
    t = " ".join(_cap_ord(w) for w in ord_).strip()
    if cur:
        t = (t + " " + cur).strip()
    return t or tekst.strip()


def parse_amount(txt):
    """'−5 060,50' / '5 060,50' / '-1.808,25' -> float."""
    t = txt.strip().replace("−", "-").replace(" ", " ")
    neg = t.startswith("-")
    t = t.lstrip("-").replace(" ", "").replace(".", "").replace(",", ".")
    val = float(re.sub(r"[^0-9.]", "", t) or 0)
    return -val if neg else val


def parse_raw(raw):
    """'2026-06-08 5 060,50 Firma ... | Detaljer: Fylt på' -> (dato, belop, tekst)."""
    s = raw.strip().replace(" ", " ")
    # Beløpet slutter ved «,dd»; stopp der så etterfølgende referansenr (lange
    # sifferstrenger) ikke slukes inn i beløpet.
    m = re.match(r"^(\d{4}-\d{2}-\d{2})\s+([−\-]?\d[\d .]*,\d{2})\s+(.*)$", s)
    if not m:
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\s+([−\-]?[\d .,]+?)\s+(.*)$", s)
    if not m:
        return None
    dato, amt, tekst = m.group(1), m.group(2), m.group(3).strip()
    tekst = tekst.replace(" | Detaljer:", " –").replace("| Detaljer:", "–").strip()
    return dato, parse_amount(amt), tekst


# ── Personvern ───────────────────────────────────────────────────────────────
# Bevisst forsiktige mønstre: kontonummer (4-2-5), IBAN, 11 sifre (fødsels-/D-nummer), e-post og telefon bare med
# +47/0047 eller vanlig gruppering. Løse 8-sifrede tall (KID, bilag) røres ikke.
STANDARD: tuple[str, ...] = (
    r"\bNO\d{2}(?: ?\d{4}){2} ?\d{3}\b",                      # IBAN
    r"\b\d{4}[ .]?\d{2}[ .]?\d{5}\b",                         # kontonummer / 11 sifre
    r"\b\d{6} ?\d{5}\b",                                      # fødsels-/D-nummer med mellomrom
    r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",                          # e-post
    r"(?:\+47|\b0047)[ ]?\d{2}[ ]?\d{2}[ ]?\d{2}[ ]?\d{2}\b",  # telefon med landskode
    r"\b\d{3} \d{2} \d{3}\b",                                 # telefon 123 45 678
    r"\b\d{2} \d{2} \d{2} \d{2}\b",                           # telefon 12 34 56 78
)
SKJULT = "[skjult]"
_REDACT_CACHE: dict[tuple[str, ...], re.Pattern] = {}


def redact(tekst, *, monstre: Iterable[str] = STANDARD) -> tuple[str, int]:
    """Maskerer personopplysninger. Gir (ny tekst, antall erstatninger). Ikke-tekst returneres urørt."""
    if not isinstance(tekst, str) or not tekst:
        return tekst, 0
    nokkel = tuple(monstre)
    rx = _REDACT_CACHE.get(nokkel)
    if rx is None:
        rx = _REDACT_CACHE[nokkel] = re.compile("|".join(f"(?:{m})" for m in nokkel))
    ny, n = rx.subn(SKJULT, tekst)
    return ny, n


# ── Norsk formatering (samme som notatene i CLI-et) ──────────────────────────
NBSP = " "


def _grupper(heltall: str) -> str:
    deler = []
    while len(heltall) > 3:
        deler.insert(0, heltall[-3:])
        heltall = heltall[:-3]
    deler.insert(0, heltall)
    return NBSP.join(deler)


def kr(x, desimaler: int = 2) -> str:
    """1234.5 → '1 234,50' (hardt mellomrom som tusenskille, komma som desimaltegn, ASCII-minus). None → '–'."""
    if x is None or x == "":
        return "–"
    d = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-desimaler), rounding=ROUND_HALF_UP)
    if d == 0:
        d = abs(d)                       # aldri «-0,00»
    neg = d < 0
    s = f"{abs(d):.{desimaler}f}"
    heltall, _, des = s.partition(".")
    ut = _grupper(heltall) + ("," + des if desimaler > 0 else "")
    return ("-" if neg else "") + ut


def hel(x) -> str:
    """Hele kroner/antall uten desimaler (Math.round: halvdeler rundes opp), aldri «-0». None → '–'."""
    if x is None or x == "":
        return "–"
    import math
    n = math.floor(float(x) + 0.5)
    return ("-" if n < 0 else "") + _grupper(str(abs(n)))


def dato_no(d) -> str:
    """'2026-09-30' (eller date/datetime) → '30.09.2026'. Tom → '–'."""
    if d is None or d == "":
        return "–"
    if isinstance(d, (_dt.date, _dt.datetime)):
        return d.strftime("%d.%m.%Y")
    s = str(d)
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        return s
    return ".".join(reversed(s[:10].split("-")))


def til_dato(v):
    """ISO-tekst eller dd.mm.yyyy → date. Annet returneres urørt."""
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date) or not isinstance(v, str):
        return v
    s = v.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", s):
            return _dt.date.fromisoformat(s[:10])
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
            dd, mm, yyyy = s.split(".")
            return _dt.date(int(yyyy), int(mm), int(dd))
    except ValueError:
        return v
    return v


def esc(s) -> str:
    """HTML-escaping av & < > (som esc() i notatene)."""
    return str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


MAANEDER = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august",
            "september", "oktober", "november", "desember"]


def maanedsnavn(iso_maaned: str, *, stor: bool = False) -> str:
    """'2026-09' → 'september' ('September' med stor=True)."""
    navn = MAANEDER[int(str(iso_maaned)[5:7]) - 1]
    return navn.capitalize() if stor else navn


def i_dag() -> str:
    return _dt.date.today().strftime("%d.%m.%Y")
