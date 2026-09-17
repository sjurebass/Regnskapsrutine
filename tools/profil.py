"""Leser klientprofil.md og kjente-avvik.md.

Profilen bestemmer hvilke kontroller som kjøres på klienten, hvilke kontonumre
som gjelder, og hvor vesentlighetsgrensen ligger. Uten profil kjøres et
forsiktig standardoppsett.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date

STANDARD_KONTOER = {
    "kunde": [1500],
    "leverandor": [2400],
    "forskuddstrekk": [2600],
    "skyldig_aga": [2770],
    "aga_kostnad": [5400],
    "feriepenger": [2940],
    "aga_feriepenger": [2785],
    "skyldig_lonn": [2930],
    "mva_utgaaende": [2700],
    "mva_inngaaende": [2710],
    "mva_oppgjor": [2740],
    "mellomregning": [1380, 1570, 2910, 2911, 2920],
    "observasjon": [1099, 2099, 9999],
    "varelager": [1400, 1410, 1420, 1430, 1460, 1465],
    "avskrivning": [6000, 6010, 6011, 6017, 6020],
}

SANNE = {"ja", "j", "true", "yes", "x", "1"}
USANNE = {"nei", "n", "false", "no", "0", "-", ""}


@dataclass
class Klientprofil:
    navn: str
    company_id: str | None = None
    orgnr: str | None = None
    mva_pliktig: bool = True
    lonn: bool = False
    prosjekt: bool = False
    varelager: bool = False
    anleggsmidler: bool = True
    utleie: bool = False
    vesentlighet: float = 5000.0
    vesentlighet_prosent: float = 0.5  # av omsetning hittil i år
    avvik_prosent: float = 30.0  # terskel for A1/A2
    deaktiverte_kontroller: set[str] = field(default_factory=set)
    kontoer: dict[str, list[int]] = field(default_factory=lambda: dict(STANDARD_KONTOER))
    notater: str = ""

    def har(self, flagg: str) -> bool:
        return bool(getattr(self, flagg, False))

    def konto(self, navn: str) -> list[int]:
        return self.kontoer.get(navn, STANDARD_KONTOER.get(navn, []))

    def grense(self, omsetning_hittil: float | None = None) -> float:
        """Vesentlighetsgrense: høyeste av fast beløp og prosent av omsetning."""
        if omsetning_hittil:
            return max(self.vesentlighet, abs(omsetning_hittil) * self.vesentlighet_prosent / 100)
        return self.vesentlighet


def _tolk_bool(verdi: str, fallback: bool) -> bool:
    v = verdi.strip().lower()
    if v in SANNE:
        return True
    if v in USANNE:
        return False
    return fallback


def _tolk_tall(verdi: str, fallback: float) -> float:
    v = verdi.replace(" ", "").replace(" ", "").replace(",", ".")
    v = re.sub(r"[^0-9.\-]", "", v)
    try:
        return float(v)
    except ValueError:
        return fallback


def _par_fra_markdown(tekst: str) -> dict[str, str]:
    """Plukker ut «| nøkkel | verdi |» og «nøkkel: verdi» fra en md-fil."""
    par: dict[str, str] = {}
    for linje in tekst.splitlines():
        linje = linje.strip()
        if linje.startswith("|") and linje.count("|") >= 3:
            deler = [d.strip() for d in linje.strip("|").split("|")]
            if len(deler) >= 2 and deler[0] and not set(deler[0]) <= set("-: "):
                par.setdefault(deler[0].lower(), deler[1])
        elif ":" in linje and not linje.startswith("#") and not linje.startswith("-"):
            n, _, v = linje.partition(":")
            if len(n) < 40:
                par.setdefault(n.strip().lower(), v.strip())
    return par


def les_profil(mappe: str, navn: str) -> Klientprofil:
    sti = os.path.join(mappe, "klientprofil.md")
    profil = Klientprofil(navn=navn)
    if not os.path.exists(sti):
        return profil
    with open(sti, encoding="utf-8") as f:
        tekst = f.read()
    par = _par_fra_markdown(tekst)

    profil.company_id = par.get("company_id") or par.get("companyid") or None
    if profil.company_id in ("", "-", "?"):
        profil.company_id = None
    profil.orgnr = par.get("orgnr") or None
    profil.mva_pliktig = _tolk_bool(par.get("mva_pliktig", ""), profil.mva_pliktig)
    profil.lonn = _tolk_bool(par.get("lonn", ""), profil.lonn)
    profil.prosjekt = _tolk_bool(par.get("prosjekt", ""), profil.prosjekt)
    profil.varelager = _tolk_bool(par.get("varelager", ""), profil.varelager)
    profil.anleggsmidler = _tolk_bool(par.get("anleggsmidler", ""), profil.anleggsmidler)
    profil.utleie = _tolk_bool(par.get("utleie", ""), profil.utleie)
    profil.vesentlighet = _tolk_tall(par.get("vesentlighet", ""), profil.vesentlighet)
    profil.vesentlighet_prosent = _tolk_tall(
        par.get("vesentlighet_prosent", ""), profil.vesentlighet_prosent
    )
    profil.avvik_prosent = _tolk_tall(par.get("avvik_prosent", ""), profil.avvik_prosent)

    av = par.get("deaktiverte_kontroller", "")
    profil.deaktiverte_kontroller = {
        k.strip().upper() for k in re.split(r"[,\s]+", av) if k.strip() and k.strip() != "-"
    }

    for nokkel in STANDARD_KONTOER:
        raa = par.get(f"konto_{nokkel}")
        if raa and raa not in ("-", ""):
            numre = [int(n) for n in re.findall(r"\d{4}", raa)]
            if numre:
                profil.kontoer[nokkel] = numre

    m = re.search(r"##\s*Notater\s*\n(.*)", tekst, re.S)
    if m:
        profil.notater = m.group(1).strip()
    return profil


@dataclass
class KjentAvvik:
    noekkel: str
    kontroll: str
    kommentar: str
    gyldig_til: date | None


def les_kjente_avvik(mappe: str) -> dict[str, KjentAvvik]:
    sti = os.path.join(mappe, "kjente-avvik.md")
    ut: dict[str, KjentAvvik] = {}
    if not os.path.exists(sti):
        return ut
    with open(sti, encoding="utf-8") as f:
        for linje in f:
            linje = linje.strip()
            if not linje.startswith("|") or linje.count("|") < 4:
                continue
            deler = [d.strip() for d in linje.strip("|").split("|")]
            noekkel = deler[0]
            if not re.fullmatch(r"[0-9a-f]{6,12}", noekkel):
                continue
            gyldig = None
            if len(deler) > 3 and re.match(r"\d{4}-\d{2}-\d{2}", deler[3]):
                gyldig = date.fromisoformat(deler[3][:10])
            ut[noekkel] = KjentAvvik(noekkel, deler[1], deler[2], gyldig)
    return ut


def merk_kjente(funn, kjente: dict[str, KjentAvvik], idag: date | None = None) -> None:
    """Setter .kjent på funn som allerede er kvittert ut og fortsatt er gyldige."""
    idag = idag or date.today()
    for f in funn:
        k = kjente.get(f.noekkel)
        if k and (k.gyldig_til is None or k.gyldig_til >= idag):
            f.kjent = True
            f.kjent_kommentar = k.kommentar
