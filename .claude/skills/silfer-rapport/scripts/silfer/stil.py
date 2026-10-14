"""Kompat-skall for lønnsavstemmingen: samme navn og samme resultat som den gamle `lonnsavstemming/scripts/stil.py`.

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "silfer-rapport" / "scripts"))
    from silfer.stil import (ANTALL, GRA, KRONER, MORK, SVART, bredder, celle, seksjon, statusregler, tabellhode, topp)

Byte-likhet er et krav (regresjon: scripts/test_stil_kompat.py): ramme D1D5DB, ingen mørk strek i rad 5,
fire statusregler i rekkefølgen OK, AVVIK, FORKLART, PERIODISERT. Endre ikke dette skallet; nye rapporter bruker
`silfer.bygg` med spec.
"""

from __future__ import annotations

from openpyxl.styles import Border, Side

from . import excel as _excel
from . import tema
from .tema import (ANTALL, AVVIK_FYLL, AVVIK_TEKST, FORKLART_FYLL, FORKLART_TEKST, GRA, GRONN, KRONER, MORK,
                   OK_FYLL, OK_TEKST, SVART)

__all__ = ["MORK", "GRONN", "GRA", "SVART", "OK_TEKST", "OK_FYLL", "AVVIK_TEKST", "AVVIK_FYLL", "FORKLART_TEKST",
           "FORKLART_FYLL", "KRONER", "ANTALL", "TYNN", "UNDER", "LOGO", "topp", "bredder", "tabellhode", "seksjon",
           "celle", "statusregler"]

TYNN = Side(style="thin", color=tema.RAMME_KOMPAT)
UNDER = Border(bottom=TYNN)

LOGO = str(tema.LOGO)


def topp(ws, tittel: str, undertittel: str) -> None:
    _excel.topp(ws, tittel, undertittel, logo=LOGO)


def bredder(ws, kart: dict[str, float]) -> None:
    _excel.bredder(ws, kart)


def tabellhode(ws, rad: int, kolonner: list[tuple[str, str]]) -> None:
    """kolonner: [(tekst, 'l'|'r'), ...] fra kolonne A."""
    _excel.tabellhode(ws, rad, kolonner, hoyde=19.5)


def seksjon(ws, rad: int, tekst: str) -> None:
    _excel.seksjon(ws, rad, tekst)


def celle(ws, rad, kol, verdi, *, fet=False, farge=SVART, nf=None,
          just=None, ramme=True, str_=9):
    return _excel.celle(ws, rad, kol, verdi, fet=fet, farge=farge, nf=nf, just=just, ramme=ramme, str_=str_,
                        ramme_farge=tema.RAMME_KOMPAT)


def statusregler(ws, omraade: str) -> None:
    _excel.statusregler(ws, omraade, statuser=tema.KOMPAT_FIRE)
