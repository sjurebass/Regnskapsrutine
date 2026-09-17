"""Datamodeller som kontrollene og rapportene deler."""

from __future__ import annotations

import calendar
import hashlib
from dataclasses import dataclass, field
from datetime import date

ROD = "rød"
GUL = "gul"
INFO = "info"
ALVORSRANG = {ROD: 0, GUL: 1, INFO: 2}


MAANEDER = [
    "januar", "februar", "mars", "april", "mai", "juni",
    "juli", "august", "september", "oktober", "november", "desember",
]


@dataclass(frozen=True)
class Periode:
    aar: int
    maaned: int

    @property
    def navn(self) -> str:
        return f"{MAANEDER[self.maaned - 1]} {self.aar}"

    @classmethod
    def fra_tekst(cls, tekst: str) -> "Periode":
        aar, maaned = tekst.split("-")
        return cls(int(aar), int(maaned))

    @property
    def fra(self) -> date:
        return date(self.aar, self.maaned, 1)

    @property
    def til(self) -> date:
        return date(self.aar, self.maaned, calendar.monthrange(self.aar, self.maaned)[1])

    @property
    def aar_fra(self) -> date:
        return date(self.aar, 1, 1)

    def forrige_aar(self) -> "Periode":
        return Periode(self.aar - 1, self.maaned)

    def forrige(self) -> "Periode":
        return Periode(self.aar, self.maaned - 1) if self.maaned > 1 else Periode(self.aar - 1, 12)

    @property
    def termin(self) -> int:
        """Mva- og skattetrekkstermin (1-6)."""
        return (self.maaned + 1) // 2

    def __str__(self) -> str:
        return f"{self.aar}-{self.maaned:02d}"


@dataclass
class Klient:
    navn: str
    mappe: str
    company_id: str | None = None
    aktiv: bool = True


@dataclass
class Funn:
    """Ett utslag fra én kontroll."""

    kontroll: str
    omraade: str
    tittel: str
    alvorlighet: str = GUL
    belop: float | None = None
    konto: str | None = None
    detalj: str = ""
    referanse: str = ""
    # settes av kjente-avvik-filteret
    kjent: bool = False
    kjent_kommentar: str = ""

    @property
    def noekkel(self) -> str:
        """Stabil nøkkel for å kjenne igjen samme avvik måned etter måned.
        Beløp inngår, slik at et avvik som endrer størrelse dukker opp på nytt."""
        raa = f"{self.kontroll}|{self.konto or ''}|{self.referanse or self.tittel}|{round(self.belop or 0)}"
        return hashlib.sha1(raa.encode("utf-8")).hexdigest()[:10]

    def sorteringsnokkel(self):
        return (ALVORSRANG.get(self.alvorlighet, 3), -abs(self.belop or 0), self.kontroll)


@dataclass
class Kontroll:
    """Én kontroll i katalogen."""

    id: str
    navn: str
    omraade: str
    funksjon: object
    krever: tuple[str, ...] = ()  # profilflagg som må være på, f.eks. ("lonn",)


@dataclass
class Resultat:
    klient: Klient
    periode: Periode
    funn: list[Funn] = field(default_factory=list)
    kjorte: list[str] = field(default_factory=list)
    hoppet_over: list[tuple[str, str]] = field(default_factory=list)  # (kontroll-id, grunn)
    feil: list[tuple[str, str]] = field(default_factory=list)  # (kontroll-id, feilmelding)

    @property
    def aapne_funn(self) -> list[Funn]:
        return [f for f in self.funn if not f.kjent]

    @property
    def status(self) -> str:
        if self.feil:
            return "feil"
        if any(f.alvorlighet == ROD for f in self.aapne_funn):
            return ROD
        if any(f.alvorlighet == GUL for f in self.aapne_funn):
            return GUL
        return "grønn"
